from __future__ import annotations

import json
from typing import Any, Callable

from .context_budget import BudgetState, BudgetReport, ContextBudgetCalculator
from .preservation import PreservationPipeline, _budget_report_to_dict
from .runtime_state import RuntimeStateStore


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
    ) -> dict[str, Any]:
        """Run the batch loop until a terminal phase or max_steps is reached.

        *workers* maps phase names to callables that receive and may mutate
        the runtime state dict.
        """
        workers = workers or {}

        # Initialise state
        state = self.store.load_state()
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

        transitions: dict[str, tuple[str, str]] = {
            "intake": ("plan", "Plan the implementation"),
            "plan": ("retrieve", "Retrieve relevant code"),
            "retrieve": ("pack", "Build context pack"),
            "pack": ("implement", "Implement the changes"),
            "implement": ("test", "Run tests"),
            "test": ("review", "Review changes"),
            "review": ("done", "Task completed"),
        }
        return transitions.get(phase, ("blocked", f"Unknown phase: {phase}"))

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
