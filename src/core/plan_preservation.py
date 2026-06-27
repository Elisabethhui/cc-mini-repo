from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .context_budget import BudgetState, ContextBudgetCalculator
from .plan_graph import PlanGraph, TaskNode
from .runtime_state import RuntimeStateStore


@dataclass
class PlanningPack:
    """Compact pack for the next planning round."""

    run_id: str = ""
    phase: str = ""
    goal: str = ""
    decisions: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_action: str = ""
    task_summary: list[dict[str, Any]] = field(default_factory=list)
    artifact_handles: list[str] = field(default_factory=list)
    requirements_summary: str = ""
    chunk_summaries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "phase": self.phase,
            "goal": self.goal,
            "decisions": list(self.decisions),
            "open_questions": list(self.open_questions),
            "modules": list(self.modules),
            "risks": list(self.risks),
            "next_action": self.next_action,
            "task_summary": list(self.task_summary),
            "artifact_handles": list(self.artifact_handles),
            "requirements_summary": self.requirements_summary,
            "chunk_summaries": list(self.chunk_summaries),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent) + "\n"


class PlanPreservationManager:
    """Manages preservation of planning state when approaching context limits.

    All operations are deterministic — no LLM calls.
    """

    def __init__(
        self,
        graph: PlanGraph,
        store: RuntimeStateStore | None = None,
        context_window: int = 32768,
        reserved_output_tokens: int = 2048,
        safety_margin_tokens: int = 1024,
        large_text_threshold: int = 8000,
    ):
        self.graph = graph
        self.store = store
        self.large_text_threshold = large_text_threshold
        self.calculator = ContextBudgetCalculator(
            context_window=context_window,
            reserved_output_tokens=reserved_output_tokens,
            safety_margin_tokens=safety_margin_tokens,
        )

    # ------------------------------------------------------------------
    # Budget checking
    # ------------------------------------------------------------------

    def estimate_plan_tokens(self) -> int:
        """Estimate tokens in the current plan graph."""
        return self.graph.estimate_tokens()

    def check_budget(self) -> BudgetState:
        """Check if planning state is approaching context window limits."""
        plan_tokens = self.estimate_plan_tokens()
        report = self.calculator.calculate(message_tokens=plan_tokens)
        return report.state

    # ------------------------------------------------------------------
    # Deterministic summarization
    # ------------------------------------------------------------------

    def _chunk_text(self, text: str, chunk_size: int = 2000) -> list[str]:
        """Split text into chunks of approximately chunk_size characters."""
        words = text.split()
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for word in words:
            word_len = len(word)
            if current_len + word_len + 1 > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_len = word_len
            else:
                current_chunk.append(word)
                current_len += word_len + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _summarize_chunk(self, chunk: str) -> str:
        """Deterministic chunk summary: first sentence + word count."""
        sentences = chunk.split(".")
        first_sentence = sentences[0].strip() + "." if sentences else chunk[:100]
        return f"{first_sentence} ({len(chunk.split())} words)"

    def _generate_chunk_summaries(self, text: str) -> list[str]:
        """Generate chunk summaries for large text."""
        if len(text) <= self.large_text_threshold:
            return []
        chunks = self._chunk_text(text)
        return [self._summarize_chunk(c) for c in chunks]

    def _generate_requirements_summary(self) -> str:
        """Generate a deterministic structured requirement summary."""
        lines = [
            f"Goal: {self.graph.goal}",
            f"Phase: {self.graph.phase}",
            "",
        ]

        if self.graph.constraints:
            lines.append("Constraints:")
            for c in self.graph.constraints:
                lines.append(f"  - {c}")
            lines.append("")

        if self.graph.assumptions:
            lines.append("Assumptions:")
            for a in self.graph.assumptions:
                lines.append(f"  - {a}")
            lines.append("")

        if self.graph.non_goals:
            lines.append("Non-goals:")
            for ng in self.graph.non_goals:
                lines.append(f"  - {ng}")
            lines.append("")

        if self.graph.acceptance_tests:
            lines.append("Acceptance tests:")
            for t in self.graph.acceptance_tests:
                lines.append(f"  - {t}")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Materialization
    # ------------------------------------------------------------------

    def _materialize_large_field(self, field_name: str, text: str) -> str | None:
        """Save large text as an artifact and return a handle."""
        if len(text) <= self.large_text_threshold:
            return None
        if self.store is None:
            return None

        safe_name = field_name.replace(" ", "_").replace("/", "_")[:50]
        handle = f"{safe_name}.md"
        self.store.write_artifact(handle, text)
        return handle

    # ------------------------------------------------------------------
    # Preservation
    # ------------------------------------------------------------------

    def preserve(self) -> PlanningPack:
        """Preserve planning state and return a compact pack for next round.

        This method:
        1. Saves the full plan graph
        2. Materializes large requirements as artifacts
        3. Generates structured summary and chunk summaries
        4. Updates runtime state
        5. Returns a compact planning pack
        """
        # Update runtime state first (ensures dirs exist)
        if self.store is not None:
            self.store.patch_state(
                phase=self.graph.phase,
                goal=self.graph.goal,
                next_action=self.graph.next_action,
                decisions=self.graph.decisions,
                open_questions=self.graph.open_questions,
            )

            # Save full plan graph
            plan_path = self.store.base_dir / "plan-graph.json"
            plan_path.write_text(self.graph.to_json(), encoding="utf-8")

        # Materialize large requirements
        artifact_handles: list[str] = []

        goal_handle = self._materialize_large_field("goal", self.graph.goal)
        if goal_handle:
            artifact_handles.append(goal_handle)

        for i, constraint in enumerate(self.graph.constraints):
            handle = self._materialize_large_field(f"constraint_{i}", constraint)
            if handle:
                artifact_handles.append(handle)

        # Generate chunk summaries for large goal
        chunk_summaries = self._generate_chunk_summaries(self.graph.goal)

        # Generate structured summary
        requirements_summary = self._generate_requirements_summary()

        # Create planning pack
        pack = PlanningPack(
            run_id=self.graph.run_id,
            phase=self.graph.phase,
            goal=self.graph.goal,
            decisions=list(self.graph.decisions),
            open_questions=list(self.graph.open_questions),
            modules=list(self.graph.modules),
            risks=list(self.graph.risks),
            next_action=self.graph.next_action,
            task_summary=self._extract_task_summary(),
            artifact_handles=artifact_handles,
            requirements_summary=requirements_summary,
            chunk_summaries=chunk_summaries,
        )

        # Save planning pack
        if self.store is not None:
            pack_path = self.store.base_dir / "planning-pack.json"
            pack_path.write_text(pack.to_json(), encoding="utf-8")

        return pack

    def create_next_pack(self) -> PlanningPack:
        """Create a minimal planning pack for the next round.

        This pack contains only essential context and omits large inline
        text that has been externalized to artifacts.
        """
        goal = self.graph.goal
        artifact_handles: list[str] = []
        chunk_summaries: list[str] = []

        if len(self.graph.goal) > self.large_text_threshold:
            handle = self._materialize_large_field("goal", self.graph.goal)
            if handle:
                artifact_handles.append(handle)
            chunk_summaries = self._generate_chunk_summaries(self.graph.goal)
            goal = goal[:200] + f" ... [see artifact: {handle}]"

        pack = PlanningPack(
            run_id=self.graph.run_id,
            phase=self.graph.phase,
            goal=goal,
            decisions=list(self.graph.decisions),
            open_questions=list(self.graph.open_questions),
            modules=list(self.graph.modules),
            risks=list(self.graph.risks),
            next_action=self.graph.next_action,
            task_summary=self._extract_task_summary(),
            artifact_handles=artifact_handles,
            requirements_summary=self._generate_requirements_summary(),
            chunk_summaries=chunk_summaries,
        )

        return pack

    def _extract_task_summary(self) -> list[dict[str, Any]]:
        """Extract compact task summary from the graph."""
        summary: list[dict[str, Any]] = []
        for task in self.graph.topological_order():
            status = "ready" if not task.depends_on else "blocked"
            summary.append({
                "id": task.id,
                "goal": task.goal,
                "status": status,
            })
        return summary
