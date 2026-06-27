from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Callable, TYPE_CHECKING

from .context_budget import BudgetState, BudgetReport, ContextBudgetCalculator
from .preservation import PreservationPipeline, _budget_report_to_dict
from .runtime_state import RuntimeStateStore

if TYPE_CHECKING:
    from .engine import Engine
    from .context_pack import ContextPackBuilder


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StepResult:
    """Structured result of a single supervised execution step."""

    step_number: int
    phase: str
    run_id: str
    goal: str
    assistant_text: str
    tool_calls: list[dict]
    budget_state: str
    next_action: str
    timestamp: str


class BatchRunner:
    """Deterministic state-machine batch runner for bounded-context execution.

    No LLM is called directly.  Workers are injected as callables.
    """

    TERMINAL_PHASES = frozenset({"done", "blocked"})

    def __init__(
        self,
        store: RuntimeStateStore,
        *,
        max_steps: int = 5,
        context_window: int = 32768,
        reserved_output_tokens: int = 2048,
        safety_margin_tokens: int = 1024,
    ) -> None:
        self.store = store
        self.max_steps = max_steps
        self.context_window = context_window
        self.reserved_output_tokens = reserved_output_tokens
        self.safety_margin_tokens = safety_margin_tokens

        self.preservation = PreservationPipeline(store)
        self.calculator = ContextBudgetCalculator(
            context_window=context_window,
            reserved_output_tokens=reserved_output_tokens,
            safety_margin_tokens=safety_margin_tokens,
        )
        self.step_count = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        goal: str,
        workers: dict[str, Callable[[dict[str, Any]], None]] | None = None,
        *,
        init_state: bool = True,
    ) -> dict[str, Any]:
        """Run the batch loop until a terminal phase or max_steps is reached.

        *workers* maps phase names to callables that receive and may mutate
        the runtime state dict.

        When *init_state* is False the existing runtime state is used as-is
        (for resume).
        """
        workers = workers or {}

        # Initialise state
        state = self.store.load_state()
        if init_state:
            state["goal"] = goal
            if not state.get("phase"):
                state["phase"] = "intake"
            if not state.get("next_action"):
                state["next_action"] = "Start intake"
            self.store.save_state(state)

        for _ in range(self.max_steps):
            self.step_count += 1
            phase = state.get("phase", "intake")

            if phase in self.TERMINAL_PHASES:
                break

            # 1. Calculate budget for the current packed state
            budget_report = self._calculate_budget(state)

            # 2. Handle budget pressure (preserve / split / hard_stop)
            if budget_report.state in (
                BudgetState.PRESERVE,
                BudgetState.SPLIT,
                BudgetState.HARD_STOP,
            ):
                result = self._handle_budget_pressure(
                    budget_report.state, state, budget_report
                )
                # Reload state after preservation may have mutated it
                state = self.store.load_state()
                state["next_action"] = result.next_action
                self.store.save_state(state)

                if budget_report.state == BudgetState.HARD_STOP:
                    state["phase"] = "blocked"
                else:
                    # After preserve or split, return to planning
                    state["phase"] = "plan"
                self.store.save_state(state)
                continue

            # 3. Execute the current phase
            next_phase, next_action = self._execute_phase(phase, state, workers)
            state["phase"] = next_phase
            state["next_action"] = next_action

            # 4. Record budget report
            self.store.append_budget_report(_budget_report_to_dict(budget_report))

            # 5. Save step log
            self._write_step_log(phase, state, budget_report)

            # 6. Persist state
            self.store.save_state(state)

        return state

    def _make_supervised_worker(
        self,
        goal: str,
        engine: "Engine",
        pack_builder: "ContextPackBuilder",
    ) -> dict[str, Callable[[dict[str, Any]], None]]:
        """Factory for supervised workers (one context pack + one model call per step)."""
        engine.set_max_turns(1)

        def _worker_for_phase(phase: str) -> Callable[[dict[str, Any]], None]:
            def worker(state: dict[str, Any]) -> None:
                # Load latest PlanGraph if available
                plan_graph = None
                try:
                    plan_path = self.store.base_dir / "plan-graph.json"
                    if plan_path.exists():
                        from .plan_graph import PlanGraph

                        plan_graph = PlanGraph.from_json(
                            plan_path.read_text(encoding="utf-8")
                        )
                except Exception:
                    pass

                # Build context pack for this step
                pack = pack_builder.build(
                    goal=goal,
                    plan_graph=plan_graph,
                    retrieval_results=state.get("retrieval_results", []),
                    runtime_state=state,
                    store=self.store,
                )

                # Fresh message window for this step
                engine.set_messages([])

                # Single engine turn (max_turns=1 prevents follow-up loops)
                events = list(engine.submit(pack.markdown))

                # Collect assistant text and tool results
                assistant_text = "".join(
                    e[1] for e in events if e[0] == "text" and len(e) > 1
                )
                tool_calls: list[dict] = []
                for e in events:
                    if e[0] == "tool_result":
                        tool_calls.append(
                            {
                                "tool_name": e[1],
                                "tool_input": e[2],
                                "result": e[3].content,
                                "is_error": e[3].is_error,
                            }
                        )

                # Detect hard-stop from engine budget protection
                budget_state = "ok"
                for e in events:
                    if (
                        e[0] == "text"
                        and len(e) > 1
                        and "checkpoint" in e[1].lower()
                    ):
                        budget_state = "hard_stop"
                        break

                # Write structured StepResult artifact
                step_result = StepResult(
                    step_number=self.step_count,
                    phase=phase,
                    run_id=self.store.run_id,
                    goal=goal,
                    assistant_text=assistant_text,
                    tool_calls=tool_calls,
                    budget_state=budget_state,
                    next_action=state.get("next_action", ""),
                    timestamp=_now_iso(),
                )
                self.store.write_artifact(
                    f"step-result-{self.step_count:03d}.json",
                    json.dumps(asdict(step_result), ensure_ascii=False, indent=2),
                )

                # Keep runtime state lean: only store artifact reference
                state["last_step_result"] = f"step-result-{self.step_count:03d}.json"

                # If engine hit hard-stop, block further progress
                if budget_state == "hard_stop":
                    state["phase"] = "blocked"
                    state["next_action"] = (
                        "Hard stop: context budget exceeded during model call"
                    )

            return worker

        return {
            phase: _worker_for_phase(phase)
            for phase in (
                "intake",
                "plan",
                "retrieve",
                "pack",
                "implement",
                "test",
                "review",
            )
        }

    def run_supervised(
        self,
        goal: str,
        engine: "Engine",
        pack_builder: "ContextPackBuilder",
    ) -> dict[str, Any]:
        """Run supervised execution: one context pack + one model call per step."""
        workers = self._make_supervised_worker(goal, engine, pack_builder)
        return self.run(goal, workers=workers)

    def resume_supervised(
        self,
        goal: str,
        engine: "Engine",
        pack_builder: "ContextPackBuilder",
    ) -> dict[str, Any]:
        """Resume supervised execution from saved runtime state.

        Loads the existing state, finds the last safe step, and continues.
        If the saved phase is terminal (done/blocked), returns immediately.
        """
        state = self.store.load_state()
        phase = state.get("phase", "intake")

        if phase in self.TERMINAL_PHASES:
            return state

        # Infer the highest step number from existing artifacts so numbering
        # continues monotonically.
        existing = self.store.list_artifacts()
        step_artifacts = [
            a for a in existing if a.startswith("step-result-") and a.endswith(".json")
        ]
        if step_artifacts:
            # Sort by numeric suffix; e.g. step-result-003.json -> 3
            last = sorted(step_artifacts)[-1]
            try:
                self.step_count = int(last[len("step-result-") : -len(".json")])
            except ValueError:
                self.step_count = 0

        workers = self._make_supervised_worker(goal, engine, pack_builder)
        return self.run(goal, workers=workers, init_state=False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calculate_budget(self, state: dict[str, Any]) -> BudgetReport:
        """Estimate token usage from the current runtime state."""
        state_json = json.dumps(state, ensure_ascii=False)
        packed_tokens = max(1, int(len(state_json) / 1.8))
        return self.calculator.calculate(
            system_prompt_tokens=500,
            tool_schema_tokens=200,
            message_tokens=1000,
            packed_context_tokens=packed_tokens,
        )

    def _handle_budget_pressure(
        self,
        budget_state: BudgetState,
        state: dict[str, Any],
        budget_report: BudgetReport,
    ) -> Any:
        """Run the preservation pipeline for the given budget state."""
        return self.preservation.run(
            budget_state=budget_state,
            messages=[],  # batch runner does not maintain a chat history
            goal=state.get("goal", ""),
            phase=state.get("phase", ""),
            current_step=state.get("current_step", ""),
            decisions=state.get("decisions", []),
            open_questions=state.get("open_questions", []),
            artifacts=state.get("artifacts", []),
            budget_report=budget_report,
        )

    def _execute_phase(
        self,
        phase: str,
        state: dict[str, Any],
        workers: dict[str, Callable[[dict[str, Any]], None]],
    ) -> tuple[str, str]:
        """Run the worker for *phase* and return the next phase + action."""
        # Special meta-phases
        if phase == "preserve":
            result = self._handle_budget_pressure(
                BudgetState.PRESERVE, state, self._calculate_budget(state)
            )
            state.update(result.state_snapshot)
            return "plan", result.next_action

        if phase == "split":
            result = self._handle_budget_pressure(
                BudgetState.SPLIT, state, self._calculate_budget(state)
            )
            state.update(result.state_snapshot)
            return "plan", result.next_action

        # Normal workflow phases
        worker = workers.get(phase)
        if worker is not None:
            worker(state)

        # If the worker mutated the phase, respect that choice
        overridden_phase = state.get("phase", phase)
        if overridden_phase != phase:
            return overridden_phase, state.get("next_action", "Continue")

        if phase == "test":
            return self._test_gate(state)
        if phase == "review":
            return self._review_gate(state)

        transitions: dict[str, tuple[str, str]] = {
            "intake": ("plan", "Plan the implementation"),
            "plan": ("retrieve", "Retrieve relevant code"),
            "retrieve": ("pack", "Build context pack"),
            "pack": ("implement", "Implement the changes"),
            "implement": ("test", "Run tests"),
            "revise": ("implement", "Revise implementation"),
        }
        return transitions.get(phase, ("blocked", f"Unknown phase: {phase}"))

    def _test_gate(self, state: dict[str, Any]) -> tuple[str, str]:
        """Gate after test phase.

        If test evidence indicates failure, return to revise.
        Otherwise proceed to review.
        """
        test_decision = state.get("test_decision", "").lower().strip()
        if test_decision in {"fail", "failed", "failing"}:
            return "revise", "Tests failed; revise implementation"
        if state.get("test_failure"):
            return "revise", "Tests failed; revise implementation"
        return "review", "Review changes"

    def _review_gate(self, state: dict[str, Any]) -> tuple[str, str]:
        """Gate after review phase.

        Only proceed to done when review decision explicitly allows it.
        Revise/rollback/hold block completion.
        """
        review_decision = state.get("review_decision", "").lower().strip()
        if review_decision in {"revise", "rollback", "hold"}:
            return (
                "blocked",
                f"Review decision: {review_decision}; follow decision before proceeding",
            )
        if review_decision in {"split", "reslice"}:
            return (
                "plan",
                f"Review decision: {review_decision}; return to planning",
            )
        if review_decision == "commit":
            return "done", "Task completed"
        # No explicit positive decision -> don't auto-done
        return "blocked", "Review incomplete; record a review decision"

    def _write_step_log(
        self, phase: str, state: dict[str, Any], budget_report: BudgetReport
    ) -> None:
        """Persist a human-readable step log."""
        lines = [
            f"# Step {self.step_count}: {phase}",
            "",
            f"**Goal:** {state.get('goal', '')}",
            f"**Next Action:** {state.get('next_action', '')}",
            "",
            f"**Budget:** {budget_report.state.value} "
            f"({budget_report.projected_total_tokens}/{budget_report.context_window})",
        ]
        if budget_report.warnings:
            lines.extend(["", "**Warnings:**"])
            for w in budget_report.warnings:
                lines.append(f"- {w}")
        self.store.write_step_log(f"step-{self.step_count:03d}", "\n".join(lines))
