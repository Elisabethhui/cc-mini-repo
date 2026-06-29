from __future__ import annotations

from .dev_contract import TaskResult, TaskSpec, VerificationSpec
from .plan_graph import PlanGraph, TaskNode


# ---------------------------------------------------------------------------
# Budget defaults (aligned with context_budget.py defaults)
# ---------------------------------------------------------------------------

_DEFAULT_RESERVED_OUTPUT = 2048
_DEFAULT_SAFETY_MARGIN = 1024


def _available_input_budget(context_window: int) -> int:
    """Return conservative available input tokens."""
    return context_window - _DEFAULT_RESERVED_OUTPUT - _DEFAULT_SAFETY_MARGIN


def _derive_context_budget(
    context_window: int,
    hint: int = 0,
    num_tasks: int = 1,
) -> tuple[int, list[str]]:
    """Compute a safe per-task context budget and any budget risks."""
    risks: list[str] = []
    available = _available_input_budget(context_window)

    if available <= 0:
        # Too small for conservative margins; fall back to minimal margin
        available = max(1, context_window - _DEFAULT_SAFETY_MARGIN)
        risks.append(
            f"Context window {context_window} leaves insufficient headroom "
            f"with default margins ({_DEFAULT_RESERVED_OUTPUT}+{_DEFAULT_SAFETY_MARGIN})"
        )

    if hint > 0:
        budget = min(hint, available)
        if budget < hint:
            risks.append(
                f"Task context_budget_hint {hint} exceeds available budget {available}; "
                f"capped to {budget}"
            )
    else:
        budget = max(1, available // max(1, num_tasks))

    return budget, risks


def _test_strategy_to_verification(test_strategy: str) -> VerificationSpec | None:
    """Convert a TaskNode test_strategy into a VerificationSpec.

    Returns None if the strategy is too vague to form a verification.
    """
    strategy = test_strategy.strip()
    if not strategy:
        return None
    # Simple heuristic: treat as a shell command split on whitespace.
    # This is intentionally generic — no business-logic heuristics.
    return VerificationSpec(kind="command", command=strategy.split())


# ---------------------------------------------------------------------------
# PlanToTaskBridge
# ---------------------------------------------------------------------------

class PlanToTaskBridge:
    """Convert PlanGraph planning state into executable TaskSpecs."""

    @staticmethod
    def from_goal(
        goal: str,
        run_id: str,
        context_window: int,
        repo_mode: str = "unknown",
    ) -> list[TaskSpec]:
        """Create a single planning intake TaskSpec from a raw goal.

        Never guesses business files or frameworks.
        """
        budget, budget_risks = _derive_context_budget(context_window)

        spec = TaskSpec(
            id="task-001-intake",
            goal=goal,
            task_kind="planning",
            task_type="intake",
            executable=False,
            planning_required=True,
            context_budget=budget,
            verification=VerificationSpec(kind="contract"),
            done_definition=[
                "Goal is refined into executable TaskSpecs",
                "File boundaries are identified or explicitly marked unknown",
                "Verification strategy is defined",
            ],
            run_id=run_id,
            risks=budget_risks,
            confidence=0.0,
        )
        return [spec]

    @staticmethod
    def from_plan_graph(plan_graph: PlanGraph, context_window: int) -> list[TaskSpec]:
        """Convert a PlanGraph into TaskSpecs.

        If the graph has a task DAG, each node becomes a TaskSpec.
        If the DAG is empty, returns an intake planning spec.
        """
        if not plan_graph.task_dag:
            return PlanToTaskBridge.from_goal(
                goal=plan_graph.goal,
                run_id=plan_graph.run_id,
                context_window=context_window,
            )

        specs: list[TaskSpec] = []
        num_tasks = len(plan_graph.task_dag)

        for node in plan_graph.task_dag:
            spec = _task_node_to_spec(
                node=node,
                plan_graph=plan_graph,
                context_window=context_window,
                num_tasks=num_tasks,
            )
            specs.append(spec)

        return specs

    @staticmethod
    def update_plan_with_task_results(
        plan_graph: PlanGraph,
        results: list[TaskResult],
    ) -> None:
        """Write task execution outcomes back into the PlanGraph.

        - passed -> decisions
        - failed -> risks
        - blocked / split / needs_planning -> next_action
        Does not remove tasks from task_dag.
        """
        for result in results:
            status = result.status.lower()
            if status == "passed":
                plan_graph.add_decision(
                    f"Task {result.task_id} passed"
                    + (f" ({result.notes})" if result.notes else "")
                )
            elif status == "failed":
                plan_graph.add_risk(
                    f"Task {result.task_id} failed"
                    + (f" ({result.notes})" if result.notes else "")
                )
                if result.risks:
                    for risk in result.risks:
                        plan_graph.add_risk(f"Task {result.task_id}: {risk}")
            elif status in {"blocked", "split", "needs_planning"}:
                action = result.next_action or f"Re-plan after {status} on {result.task_id}"
                plan_graph.set_next_action(action)
                if result.risks:
                    for risk in result.risks:
                        plan_graph.add_risk(f"Task {result.task_id}: {risk}")
            else:
                # Unknown status — record as open question
                plan_graph.add_open_question(
                    f"Task {result.task_id} ended with status '{result.status}'"
                )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _task_node_to_spec(
    node: TaskNode,
    plan_graph: PlanGraph,
    context_window: int,
    num_tasks: int,
) -> TaskSpec:
    """Convert a single TaskNode into a TaskSpec."""
    budget, budget_risks = _derive_context_budget(
        context_window,
        hint=node.context_budget_hint,
        num_tasks=num_tasks,
    )

    verification = _test_strategy_to_verification(node.test_strategy)

    has_allowed_files = bool(node.allowed_files)
    has_verification = verification is not None

    if has_allowed_files and has_verification:
        executable = True
        planning_required = False
    else:
        executable = False
        planning_required = True

    risks = list(budget_risks)
    if not has_allowed_files:
        risks.append("TaskNode lacks allowed_files; file boundaries are unknown")
    if not has_verification:
        risks.append("TaskNode lacks test_strategy; no verification defined")

    # Derive task_kind and task_type from context
    task_kind = "coding"
    task_type = "modify"
    if not executable and planning_required:
        task_kind = "planning"
        task_type = "plan"

    done_definition = list(node.acceptance_criteria) if node.acceptance_criteria else []
    if executable and not done_definition:
        done_definition.append("Verification command passes")

    return TaskSpec(
        id=node.id,
        goal=node.goal,
        task_kind=task_kind,
        task_type=task_type,
        executable=executable,
        planning_required=planning_required,
        allowed_files=list(node.allowed_files),
        forbidden_files=list(node.forbidden_files),
        context_budget=budget,
        max_files_to_read=5,
        max_files_to_edit=3,
        verification=verification or VerificationSpec(kind="contract"),
        done_definition=done_definition,
        depends_on=list(node.depends_on),
        source_plan_id=plan_graph.run_id,
        run_id=plan_graph.run_id,
        risks=risks,
        assumptions=list(plan_graph.assumptions),
        confidence=0.8 if executable else 0.3,
    )
