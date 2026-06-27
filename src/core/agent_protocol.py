from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AgentSpec:
    """Bounded agent protocol specification.

    Defines the contract for a single agent turn:
    *role*, *goal*, *budget*, *allowed/forbidden actions*, and
    the expected *input* and *output* schemas.
    """

    role: str
    goal: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    budget_tokens: int
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    stop_condition: str = ""

    def __post_init__(self):
        if self.budget_tokens <= 0:
            raise ValueError("budget_tokens must be positive")


@dataclass
class AgentResult:
    """Structured output produced by an agent turn."""

    status: str = ""  # done | revise | blocked | error
    changed_files: list[str] = field(default_factory=list)
    test_commands: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_action: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "changed_files": list(self.changed_files),
            "test_commands": list(self.test_commands),
            "risks": list(self.risks),
            "next_action": self.next_action,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentResult:
        return cls(
            status=str(data.get("status", "")),
            changed_files=list(data.get("changed_files", [])),
            test_commands=list(data.get("test_commands", [])),
            risks=list(data.get("risks", [])),
            next_action=str(data.get("next_action", "")),
            notes=str(data.get("notes", "")),
        )


# ---------------------------------------------------------------------------
# Permission / safety guard
# ---------------------------------------------------------------------------

class PermissionBlocked(Exception):
    """Raised when an agent attempts a forbidden action."""


class SpawnGuard:
    """Prevents infinite agent spawning by tracking depth."""

    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self._depth = 0

    def enter(self) -> None:
        if self._depth >= self.max_depth:
            raise PermissionBlocked(
                f"Agent spawn depth {self._depth} exceeds maximum {self.max_depth}. "
                "An agent cannot spawn another agent at this level."
            )
        self._depth += 1

    def exit(self) -> None:
        self._depth = max(0, self._depth - 1)

    def __enter__(self):
        self.enter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit()
        return False


class PermissionEnforcer:
    """Checks agent actions against the allowed/forbidden lists."""

    @staticmethod
    def check(spec: AgentSpec, action: str) -> None:
        """Raise *PermissionBlocked* if *action* matches a forbidden pattern."""
        lowered = action.lower().strip()
        for forbidden in spec.forbidden_actions:
            if lowered == forbidden.lower().strip():
                raise PermissionBlocked(
                    f"Action '{action}' is forbidden for {spec.role}."
                )
            # Also block substring matches for destructive patterns
            if forbidden.lower().strip() in lowered:
                raise PermissionBlocked(
                    f"Action '{action}' is forbidden for {spec.role}."
                )

    @staticmethod
    def validate(spec: AgentSpec) -> list[str]:
        """Return a list of warnings if the spec looks risky."""
        warnings: list[str] = []
        if not spec.forbidden_actions:
            warnings.append(f"{spec.role}: No forbidden_actions defined.")
        destructive = {"commit", "push", "reset --hard", "rm -rf", "delete", "drop"}
        lowered_forbidden = {f.lower().strip() for f in spec.forbidden_actions}
        for d in destructive:
            if d not in lowered_forbidden:
                warnings.append(
                    f"{spec.role}: Destructive action '{d}' is not explicitly forbidden."
                )
        return warnings


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_prompt(
    spec: AgentSpec,
    context_pack: str,
    *,
    templates_dir: Path | None = None,
) -> str:
    """Build a deterministic prompt from an agent spec and context pack.

    No LLM is called.  If a template file exists in *templates_dir* it is
    used; otherwise a generic structured prompt is generated.
    """
    if templates_dir is not None:
        template_path = templates_dir / f"{spec.role.lower()}.md"
        if template_path.exists():
            template = template_path.read_text(encoding="utf-8")
            return (
                template
                .replace("{{GOAL}}", spec.goal)
                .replace("{{BUDGET}}", str(spec.budget_tokens))
                .replace("{{ALLOWED}}", ", ".join(spec.allowed_actions))
                .replace("{{FORBIDDEN}}", ", ".join(spec.forbidden_actions))
                .replace("{{STOP}}", spec.stop_condition)
                .replace("{{CONTEXT}}", context_pack)
                .replace("{{INPUT_SCHEMA}}", json.dumps(spec.input_schema, indent=2))
                .replace("{{OUTPUT_SCHEMA}}", json.dumps(spec.output_schema, indent=2))
            )

    # Generic fallback prompt
    lines = [
        f"# Agent Turn: {spec.role}",
        "",
        f"**Goal:** {spec.goal}",
        f"**Budget:** {spec.budget_tokens} tokens",
        f"**Stop Condition:** {spec.stop_condition or 'Return structured JSON and stop.'}",
        "",
        "## Allowed Actions",
        *( [f"- {a}" for a in spec.allowed_actions] if spec.allowed_actions else ["_None defined._"] ),
        "",
        "## Forbidden Actions",
        *( [f"- {f}" for f in spec.forbidden_actions] if spec.forbidden_actions else ["_None defined._"] ),
        "",
        "## Input Schema",
        "```json",
        json.dumps(spec.input_schema, indent=2),
        "```",
        "",
        "## Output Schema",
        "```json",
        json.dumps(spec.output_schema, indent=2),
        "```",
        "",
        "## Context Pack",
        context_pack,
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class AgentRegistry:
    """Factory for predefined bounded agent specs.

    Each spec encodes a narrow role, strict budget, forbidden actions,
    and structured output schema.
    """

    @classmethod
    def coordinator(cls) -> AgentSpec:
        return AgentSpec(
            role="Coordinator",
            goal="Understand current phase, choose next step, respect max_steps, merge worker results, write runtime state.",
            input_schema={
                "phase": "string",
                "max_steps": "integer",
                "step_count": "integer",
                "runtime_state": "object",
            },
            output_schema={
                "status": "done | revise | blocked",
                "next_phase": "string",
                "next_action": "string",
                "notes": "string",
            },
            budget_tokens=8000,
            allowed_actions=["read_state", "write_state", "request_pack", "merge_result"],
            forbidden_actions=[
                "commit", "push", "reset --hard", "delete", "spawn_agent",
                "run_shell", "modify_credentials", "change_secrets",
            ],
            stop_condition="Return next_phase and next_action as JSON, then stop.",
        )

    @classmethod
    def planner(cls) -> AgentSpec:
        return AgentSpec(
            role="Planner",
            goal="Update PlanGraph, produce task slices, record assumptions, decisions, open questions.",
            input_schema={
                "goal": "string",
                "plan_graph": "object",
                "constraints": "list[string]",
            },
            output_schema={
                "status": "done | revise | blocked",
                "updated_plan_graph": "object",
                "decisions": "list[string]",
                "open_questions": "list[string]",
                "next_action": "string",
            },
            budget_tokens=12000,
            allowed_actions=["read_plan", "write_plan", "add_task", "record_decision"],
            forbidden_actions=[
                "commit", "push", "modify_product_code", "delete",
                "spawn_agent", "run_shell",
            ],
            stop_condition="Return updated plan graph as JSON, then stop.",
        )

    @classmethod
    def retriever(cls) -> AgentSpec:
        return AgentSpec(
            role="Retriever",
            goal="Query CodeGraph, fall back to rg, identify relevant files/symbols/tests, return compact evidence.",
            input_schema={
                "query": "string",
                "query_type": "symbols | files | tests | callers | impact",
                "workspace_root": "string",
            },
            output_schema={
                "status": "done | revise | blocked",
                "items": "list[string]",
                "confidence": "float",
                "warnings": "list[string]",
                "next_action": "string",
            },
            budget_tokens=6000,
            allowed_actions=["query_codegraph", "query_rg", "return_results"],
            forbidden_actions=[
                "commit", "push", "modify_product_code", "delete",
                "spawn_agent", "run_shell", "implement_code",
            ],
            stop_condition="Return compact evidence as JSON, then stop.",
        )

    @classmethod
    def implementer(cls) -> AgentSpec:
        return AgentSpec(
            role="Implementer",
            goal="Apply bounded changes, respect allowed_files, avoid unrelated refactors, produce concise change summary.",
            input_schema={
                "task": "string",
                "allowed_files": "list[string]",
                "forbidden_files": "list[string]",
                "context_pack": "string",
            },
            output_schema={
                "status": "done | revise | blocked",
                "changed_files": "list[string]",
                "diff_summary": "string",
                "risks": "list[string]",
                "next_action": "string",
            },
            budget_tokens=12000,
            allowed_actions=["read_file", "write_file", "edit_file", "run_tests"],
            forbidden_actions=[
                "commit", "push", "reset --hard", "delete_unrelated",
                "spawn_agent", "run_destructive_shell", "modify_credentials",
            ],
            stop_condition="Return changed_files and diff_summary as JSON, then stop.",
        )

    @classmethod
    def tester(cls) -> AgentSpec:
        return AgentSpec(
            role="Tester",
            goal="Choose minimal tests, analyze failures, recommend fix direction.",
            input_schema={
                "changed_files": "list[string]",
                "test_registry": "object",
                "failure_logs": "string",
            },
            output_schema={
                "status": "done | revise | blocked",
                "test_commands": "list[string]",
                "recommendations": "list[string]",
                "risks": "list[string]",
                "next_action": "string",
            },
            budget_tokens=8000,
            allowed_actions=["select_tests", "analyze_failures", "recommend_fix"],
            forbidden_actions=[
                "commit", "push", "modify_product_code", "delete",
                "spawn_agent", "run_shell", "skip_all_tests",
            ],
            stop_condition="Return test_commands and recommendations as JSON, then stop.",
        )

    @classmethod
    def reviewer(cls) -> AgentSpec:
        return AgentSpec(
            role="Reviewer",
            goal="Review compact diff, check scope/tests/risks, return approve/revise/rollback/split.",
            input_schema={
                "diff_summary": "string",
                "changed_files": "list[string]",
                "test_evidence": "string",
                "risks": "list[string]",
            },
            output_schema={
                "status": "approve | revise | rollback | split",
                "changed_files": "list[string]",
                "review_notes": "string",
                "risks": "list[string]",
                "next_action": "string",
            },
            budget_tokens=8000,
            allowed_actions=["read_diff", "read_tests", "approve", "request_changes"],
            forbidden_actions=[
                "commit", "push", "reset --hard", "modify_product_code",
                "delete", "spawn_agent", "run_shell", "auto_merge",
            ],
            stop_condition="Return review decision as JSON, then stop.",
        )

    @classmethod
    def all_specs(cls) -> dict[str, AgentSpec]:
        return {
            "coordinator": cls.coordinator(),
            "planner": cls.planner(),
            "retriever": cls.retriever(),
            "implementer": cls.implementer(),
            "tester": cls.tester(),
            "reviewer": cls.reviewer(),
        }
