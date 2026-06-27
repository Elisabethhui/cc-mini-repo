from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .context_budget import BudgetReport, ContextBudgetCalculator
from .plan_graph import PlanGraph
from .runtime_state import RuntimeStateStore


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: characters / 1.8."""
    return max(0, int(len(text) / 1.8))


@dataclass
class ContextPack:
    """A bounded context pack ready for a model call."""

    markdown: str
    budget_report: BudgetReport
    artifact_handles: list[str] = field(default_factory=list)
    truncated: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass
class PackItem:
    """A single item in the pack with priority."""

    priority: int  # 0-4, lower is higher
    title: str
    content: str
    source: str = ""


class ContextPackBuilder:
    """Builds a bounded context pack from planning and retrieval state.

    Priority order:
        P0: Goal + phase + next action
        P1: Decisions + open questions + risks
        P2: Code retrieval results
        P3: Test recommendations
        P4: Full task DAG + runtime state details
    """

    def __init__(
        self,
        context_window: int = 32768,
        reserved_output_tokens: int = 2048,
        safety_margin_tokens: int = 1024,
        system_prompt_tokens: int = 500,
        tool_schema_tokens: int = 200,
        message_tokens: int = 1000,
    ):
        self.context_window = context_window
        self.reserved_output_tokens = reserved_output_tokens
        self.safety_margin_tokens = safety_margin_tokens
        self.system_prompt_tokens = system_prompt_tokens
        self.tool_schema_tokens = tool_schema_tokens
        self.message_tokens = message_tokens

        self.calculator = ContextBudgetCalculator(
            context_window=context_window,
            reserved_output_tokens=reserved_output_tokens,
            safety_margin_tokens=safety_margin_tokens,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        goal: str,
        plan_graph: PlanGraph | None = None,
        retrieval_results: list[Any] | None = None,
        runtime_state: dict[str, Any] | None = None,
        test_recommendations: list[str] | None = None,
        store: RuntimeStateStore | None = None,
    ) -> ContextPack:
        """Build a context pack within the configured context_window budget."""
        items = self._collect_items(
            goal=goal,
            plan_graph=plan_graph,
            retrieval_results=retrieval_results,
            runtime_state=runtime_state,
            test_recommendations=test_recommendations,
        )
        return self._assemble_pack(items, store)

    # ------------------------------------------------------------------
    # Item collection
    # ------------------------------------------------------------------

    def _collect_items(
        self,
        goal: str,
        plan_graph: PlanGraph | None,
        retrieval_results: list[Any] | None,
        runtime_state: dict[str, Any] | None,
        test_recommendations: list[str] | None,
    ) -> list[PackItem]:
        items: list[PackItem] = []

        # P0: Goal + phase + next action
        phase_text = plan_graph.phase if plan_graph else "unknown"
        next_action = plan_graph.next_action if plan_graph else ""
        p0_content = (
            f"**Goal:** {goal}\n\n"
            f"**Phase:** {phase_text}\n\n"
            f"**Next Action:** {next_action}\n"
        )
        items.append(
            PackItem(priority=0, title="Goal & Phase", content=p0_content, source="plan")
        )

        # P1: Decisions, open questions, risks
        if plan_graph:
            lines: list[str] = []
            if plan_graph.decisions:
                lines.append("## Decisions")
                for d in plan_graph.decisions:
                    lines.append(f"- {d}")
                lines.append("")
            if plan_graph.open_questions:
                lines.append("## Open Questions")
                for q in plan_graph.open_questions:
                    lines.append(f"- {q}")
                lines.append("")
            if plan_graph.risks:
                lines.append("## Risks")
                for r in plan_graph.risks:
                    lines.append(f"- {r}")
                lines.append("")
            if lines:
                items.append(
                    PackItem(
                        priority=1,
                        title="Planning State",
                        content="\n".join(lines),
                        source="plan",
                    )
                )

        # P2: Retrieval results
        if retrieval_results:
            lines = ["## Relevant Code"]
            for result in retrieval_results:
                if getattr(result, "ok", False) and getattr(result, "items", ()):
                    lines.append(
                        f"### {getattr(result, 'query_type', 'query')}: "
                        f"{getattr(result, 'query', '')}"
                    )
                    for item in getattr(result, "items", ()):
                        lines.append(f"- `{item}`")
                    conf = getattr(result, "confidence", 0.0)
                    truncated = getattr(result, "truncated", False)
                    lines.append(f"*confidence: {conf}, truncated: {truncated}*")
                    lines.append("")
            if len(lines) > 1:
                items.append(
                    PackItem(
                        priority=2,
                        title="Retrieval",
                        content="\n".join(lines),
                        source="retrieval",
                    )
                )

        # P3: Test recommendations
        if test_recommendations:
            lines = ["## Test Recommendations"]
            for rec in test_recommendations:
                lines.append(f"- {rec}")
            lines.append("")
            items.append(
                PackItem(
                    priority=3,
                    title="Tests",
                    content="\n".join(lines),
                    source="tests",
                )
            )

        # P4: Runtime state summary
        if runtime_state:
            summary_lines = ["## Runtime State"]
            for key in ("phase", "current_step", "next_action"):
                if key in runtime_state and runtime_state[key]:
                    summary_lines.append(f"- **{key}**: {runtime_state[key]}")
            summary_lines.append("")
            items.append(
                PackItem(
                    priority=4,
                    title="Runtime",
                    content="\n".join(summary_lines),
                    source="runtime",
                )
            )

        # P4: Task summary (limit to first 10)
        if plan_graph and plan_graph.task_dag:
            lines = ["## Task Summary"]
            for task in plan_graph.topological_order()[:10]:
                status = "ready" if not task.depends_on else "blocked"
                lines.append(f"- ({status}) {task.id}: {task.goal}")
            if len(plan_graph.task_dag) > 10:
                lines.append(
                    f"- ... and {len(plan_graph.task_dag) - 10} more tasks"
                )
            lines.append("")
            items.append(
                PackItem(
                    priority=4,
                    title="Tasks",
                    content="\n".join(lines),
                    source="plan",
                )
            )

        return items

    # ------------------------------------------------------------------
    # Assembly
    # ------------------------------------------------------------------

    def _assemble_pack(
        self,
        items: list[PackItem],
        store: RuntimeStateStore | None,
    ) -> ContextPack:
        """Assemble pack items within budget, externalizing overflow."""

        # Budget available for pack content
        fixed_overhead = (
            self.system_prompt_tokens
            + self.tool_schema_tokens
            + self.message_tokens
            + self.reserved_output_tokens
            + self.safety_margin_tokens
        )
        available = max(0, self.context_window - fixed_overhead)

        # Sort by priority
        items.sort(key=lambda x: x.priority)

        included: list[PackItem] = []
        externalized: list[PackItem] = []
        artifact_handles: list[str] = []
        current_tokens = 0
        truncated = False

        for item in items:
            item_tokens = _estimate_tokens(item.content)
            if current_tokens + item_tokens <= available:
                included.append(item)
                current_tokens += item_tokens
            else:
                # Try to externalize lower-priority items
                if store is not None and item.priority >= 2:
                    safe_name = (
                        f"pack-{item.source}-"
                        f"{item.title.lower().replace(' ', '_')[:30]}.md"
                    )
                    store.write_artifact(safe_name, item.content)
                    artifact_handles.append(safe_name)
                    externalized.append(item)
                else:
                    # High-priority: try to fit a summary
                    summary = self._summarize_item(
                        item, available - current_tokens
                    )
                    if summary:
                        included.append(
                            PackItem(
                                priority=item.priority,
                                title=item.title + " (Summary)",
                                content=summary,
                                source=item.source,
                            )
                        )
                        current_tokens += _estimate_tokens(summary)
                    truncated = True
                    externalized.append(item)

        # Build markdown
        lines = ["# Context Pack", ""]
        for item in included:
            lines.append(item.content)
            lines.append("")

        if artifact_handles:
            lines.append("## Externalized Artifacts")
            for handle in artifact_handles:
                lines.append(f"- `{handle}`")
            lines.append("")

        if truncated:
            lines.append(
                "_Some content was truncated or externalized to fit the context window._"
            )
            lines.append("")

        markdown = "\n".join(lines)
        pack_tokens = _estimate_tokens(markdown)

        # Budget report
        budget_report = self.calculator.calculate(
            system_prompt_tokens=self.system_prompt_tokens,
            tool_schema_tokens=self.tool_schema_tokens,
            message_tokens=self.message_tokens,
            packed_context_tokens=pack_tokens,
        )

        warnings: list[str] = []
        if truncated:
            warnings.append(
                f"Pack was truncated; {len(externalized)} items externalized or summarized"
            )
        if externalized:
            warnings.append(
                f"Externalized {len(externalized)} items to artifacts"
            )

        return ContextPack(
            markdown=markdown,
            budget_report=budget_report,
            artifact_handles=artifact_handles,
            truncated=truncated,
            warnings=warnings,
        )

    def _summarize_item(self, item: PackItem, max_tokens: int) -> str:
        """Create a brief summary of an item that fits within max_tokens."""
        if max_tokens <= 10:
            return f"**{item.title}**: [see artifact]"

        max_chars = int(max_tokens * 1.8)
        content = item.content.strip()
        if len(content) <= max_chars:
            return content

        truncated = content[: max_chars - 20]
        # Try to break at a newline near the end
        last_newline = truncated.rfind("\n")
        if last_newline > max_chars * 0.5:
            truncated = truncated[:last_newline]

        return (
            truncated + f"\n\n_... ({item.title} truncated; see full artifact)_"
        )
