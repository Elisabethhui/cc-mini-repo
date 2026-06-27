from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class TaskNode:
    """A single node in the PlanGraph task DAG."""

    id: str
    goal: str = ""
    depends_on: list[str] = field(default_factory=list)
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    test_strategy: str = ""
    context_budget_hint: int = 0
    acceptance_criteria: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "depends_on": list(self.depends_on),
            "allowed_files": list(self.allowed_files),
            "forbidden_files": list(self.forbidden_files),
            "test_strategy": self.test_strategy,
            "context_budget_hint": self.context_budget_hint,
            "acceptance_criteria": list(self.acceptance_criteria),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskNode:
        return cls(
            id=str(data["id"]),
            goal=str(data.get("goal", "")),
            depends_on=list(data.get("depends_on", [])),
            allowed_files=list(data.get("allowed_files", [])),
            forbidden_files=list(data.get("forbidden_files", [])),
            test_strategy=str(data.get("test_strategy", "")),
            context_budget_hint=int(data.get("context_budget_hint", 0)),
            acceptance_criteria=list(data.get("acceptance_criteria", [])),
        )


@dataclass
class PlanGraph:
    """Planning-time graph for empty-repo or pre-CodeGraph phases.

    Pure data structure — no LLM calls, no CodeGraph dependency.
    """

    run_id: str = ""
    project_name: str = ""
    phase: str = "intake"
    goal: str = ""
    non_goals: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    acceptance_tests: list[str] = field(default_factory=list)
    task_dag: list[TaskNode] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    next_action: str = ""

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "project_name": self.project_name,
            "phase": self.phase,
            "goal": self.goal,
            "non_goals": list(self.non_goals),
            "constraints": list(self.constraints),
            "assumptions": list(self.assumptions),
            "modules": list(self.modules),
            "interfaces": list(self.interfaces),
            "risks": list(self.risks),
            "open_questions": list(self.open_questions),
            "decisions": list(self.decisions),
            "acceptance_tests": list(self.acceptance_tests),
            "task_dag": [t.to_dict() for t in self.task_dag],
            "artifacts": list(self.artifacts),
            "next_action": self.next_action,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent) + "\n"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanGraph:
        return cls(
            run_id=str(data.get("run_id", "")),
            project_name=str(data.get("project_name", "")),
            phase=str(data.get("phase", "intake")),
            goal=str(data.get("goal", "")),
            non_goals=list(data.get("non_goals", [])),
            constraints=list(data.get("constraints", [])),
            assumptions=list(data.get("assumptions", [])),
            modules=list(data.get("modules", [])),
            interfaces=list(data.get("interfaces", [])),
            risks=list(data.get("risks", [])),
            open_questions=list(data.get("open_questions", [])),
            decisions=list(data.get("decisions", [])),
            acceptance_tests=list(data.get("acceptance_tests", [])),
            task_dag=[TaskNode.from_dict(t) for t in data.get("task_dag", [])],
            artifacts=list(data.get("artifacts", [])),
            next_action=str(data.get("next_action", "")),
        )

    @classmethod
    def from_json(cls, text: str) -> PlanGraph:
        return cls.from_dict(json.loads(text))

    # ------------------------------------------------------------------
    # Incremental updates
    # ------------------------------------------------------------------

    def add_task(self, node: TaskNode) -> None:
        """Append a task node to the DAG."""
        self.task_dag.append(node)

    def update_task(self, task_id: str, **kwargs: Any) -> bool:
        """Patch fields on an existing task node.  Returns True if found."""
        for node in self.task_dag:
            if node.id == task_id:
                for key, value in kwargs.items():
                    if hasattr(node, key):
                        setattr(node, key, value)
                return True
        return False

    def remove_task(self, task_id: str) -> bool:
        """Remove a task node by id.  Returns True if found."""
        original_len = len(self.task_dag)
        self.task_dag = [n for n in self.task_dag if n.id != task_id]
        return len(self.task_dag) < original_len

    def add_decision(self, decision: str) -> None:
        """Record a new decision, avoiding duplicates."""
        if decision not in self.decisions:
            self.decisions.append(decision)

    def add_open_question(self, question: str) -> None:
        """Record a new open question, avoiding duplicates."""
        if question not in self.open_questions:
            self.open_questions.append(question)

    def resolve_open_question(self, question: str) -> bool:
        """Remove an open question (e.g. after it is answered)."""
        if question in self.open_questions:
            self.open_questions.remove(question)
            return True
        return False

    def add_risk(self, risk: str) -> None:
        """Record a new risk, avoiding duplicates."""
        if risk not in self.risks:
            self.risks.append(risk)

    def add_assumption(self, assumption: str) -> None:
        """Record a new assumption, avoiding duplicates."""
        if assumption not in self.assumptions:
            self.assumptions.append(assumption)

    def add_module(self, name: str) -> None:
        """Record a module name, avoiding duplicates."""
        if name not in self.modules:
            self.modules.append(name)

    def add_interface(self, name: str) -> None:
        """Record an interface name, avoiding duplicates."""
        if name not in self.interfaces:
            self.interfaces.append(name)

    def add_artifact(self, path: str) -> None:
        """Record an artifact path, avoiding duplicates."""
        if path not in self.artifacts:
            self.artifacts.append(path)

    def set_next_action(self, action: str) -> None:
        """Update the recommended next action."""
        self.next_action = action

    def set_phase(self, phase: str) -> None:
        """Update the current planning phase."""
        self.phase = phase

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def ready_tasks(self) -> list[TaskNode]:
        """Return tasks whose dependencies are all satisfied (no depends_on)."""
        return [n for n in self.task_dag if not n.depends_on]

    def task_by_id(self, task_id: str) -> TaskNode | None:
        """Lookup a task node by id."""
        for node in self.task_dag:
            if node.id == task_id:
                return node
        return None

    def topological_order(self) -> list[TaskNode]:
        """Return task nodes in a rough topological order (Kahn's algorithm)."""
        in_degree: dict[str, int] = {}
        adj: dict[str, list[str]] = {}
        for node in self.task_dag:
            in_degree[node.id] = 0
            adj[node.id] = []
        for node in self.task_dag:
            for dep in node.depends_on:
                if dep in adj:
                    adj[dep].append(node.id)
                    in_degree[node.id] = in_degree.get(node.id, 0) + 1

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        order: list[str] = []
        while queue:
            tid = queue.pop(0)
            order.append(tid)
            for neighbor in adj.get(tid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        id_to_node = {n.id: n for n in self.task_dag}
        return [id_to_node[tid] for tid in order if tid in id_to_node]
