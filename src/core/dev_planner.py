from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .dev_contract import TaskSpec, VerificationSpec
from .plan_graph import PlanGraph, TaskNode
from .plan_task_bridge import _derive_context_budget
from .runtime_state import RuntimeStateStore
from .task_spec_store import TaskSpecStore


# ---------------------------------------------------------------------------
# PlannerCandidateIssue
# ---------------------------------------------------------------------------

@dataclass
class PlannerCandidateIssue:
    """Records why a candidate task failed validation or needs review."""

    candidate_id: str | None = None
    severity: str = "error"  # error | warning
    field: str = ""
    message: str = ""
    value_preview: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "severity": self.severity,
            "field": self.field,
            "message": self.message,
            "value_preview": self.value_preview,
        }


# ---------------------------------------------------------------------------
# PlannerValidationResult
# ---------------------------------------------------------------------------

@dataclass
class PlannerValidationResult:
    """Outcome of validating candidate TaskSpecs."""

    valid_tasks: list[TaskSpec] = field(default_factory=list)
    invalid_candidates: list[dict] = field(default_factory=list)
    issues: list[PlannerCandidateIssue] = field(default_factory=list)
    requires_user_review: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid_tasks": [t.to_dict() for t in self.valid_tasks],
            "invalid_candidates": list(self.invalid_candidates),
            "issues": [i.to_dict() for i in self.issues],
            "requires_user_review": self.requires_user_review,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


# ---------------------------------------------------------------------------
# PlannerResult
# ---------------------------------------------------------------------------

@dataclass
class PlannerResult:
    """Outcome of a single planning run."""

    run_id: str = ""
    goal: str = ""
    status: str = ""  # planned | needs_planning | invalid_response | blocked | requires_review
    candidate_count: int = 0
    valid_task_ids: list[str] = field(default_factory=list)
    invalid_candidate_count: int = 0
    planning_prompt_path: str | None = None
    raw_response_path: str | None = None
    candidate_artifact_path: str | None = None
    validation_artifact_path: str | None = None
    saved_task_paths: list[str] = field(default_factory=list)
    next_action: str = ""
    issues: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "goal": self.goal,
            "status": self.status,
            "candidate_count": self.candidate_count,
            "valid_task_ids": list(self.valid_task_ids),
            "invalid_candidate_count": self.invalid_candidate_count,
            "planning_prompt_path": self.planning_prompt_path,
            "raw_response_path": self.raw_response_path,
            "candidate_artifact_path": self.candidate_artifact_path,
            "validation_artifact_path": self.validation_artifact_path,
            "saved_task_paths": list(self.saved_task_paths),
            "next_action": self.next_action,
            "issues": list(self.issues),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "risks": list(self.risks),
        }


# ---------------------------------------------------------------------------
# StrictDevPlanner
# ---------------------------------------------------------------------------

class StrictDevPlanner:
    """Generate and validate candidate TaskSpecs from a natural-language goal.

    Guarantees:
    - Only proposes candidate TaskSpecs; never executes code.
    - Validates every candidate strictly before saving.
    - Writes planning artifacts for auditability.
    - Can feed valid tasks into a PlanGraph.
    """

    _VALID_TASK_KINDS = {"planning", "coding", "verification", "review"}
    _VALID_TASK_TYPES = {
        "intake",
        "plan",
        "scaffold",
        "create",
        "modify",
        "fix",
        "test",
        "review",
    }
    _SENSITIVE_PARTS = {
        ".git",
        ".env",
        "secrets",
        "secret",
        "key",
        "token",
        "credential",
        "password",
    }

    def __init__(
        self,
        workspace: Path,
        task_store: TaskSpecStore,
        runtime_store: RuntimeStateStore | None = None,
        context_window: int = 32768,
        reserved_output_tokens: int = 2048,
        safety_margin_tokens: int = 1024,
    ):
        self.workspace = Path(workspace).expanduser().resolve()
        self.task_store = task_store
        self.runtime_store = runtime_store
        self.context_window = context_window
        self.reserved_output_tokens = reserved_output_tokens
        self.safety_margin_tokens = safety_margin_tokens
        self.run_id = self._resolve_run_id()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_planning_prompt(self, goal: str, repo_mode: str = "unknown") -> str:
        """Build a prompt that instructs the planner engine to emit only JSON."""
        available = max(
            0,
            self.context_window
            - self.reserved_output_tokens
            - self.safety_margin_tokens,
        )
        lines = [
            "# Strict Planning Task",
            "",
            f"Goal: {goal}",
            f"Repo mode: {repo_mode}",
            f"Available context budget per task: {available} tokens",
            "",
            "## Instructions",
            "You are a strict planner. Your job is to propose candidate TaskSpecs.",
            "You must NOT write code.",
            "You must NOT modify files.",
            "You must NOT run commands.",
            "You must NOT submit commits.",
            "You must output ONLY a JSON array of candidate tasks.",
            "No markdown explanations. No prose. No bullet lists outside JSON.",
            "",
            "## Required fields for each candidate",
            '- id: safe string identifier (no paths, no "..")',
            "- goal: concise description",
            '- task_kind: one of planning, coding, verification, review',
            '- task_type: one of intake, plan, scaffold, create, modify, fix, test, review',
            "- executable: true only if allowed_files and verification are known",
            "- planning_required: true if more planning is needed (must be false if executable is true)",
            "- allowed_files: list of safe relative paths (empty if unknown)",
            "- forbidden_files: list of safe relative paths",
            "- context_budget: positive integer",
            "- max_files_to_read: integer",
            "- max_files_to_edit: integer",
            '- verification: object with kind (command/artifact/manual/contract) and appropriate fields',
            "- done_definition: list of strings",
            "- depends_on: list of task ids",
            "- confidence: float in [0, 1]",
            "- risks: list of strings",
            "- assumptions: list of strings",
            "",
            "## Rules",
            "- If allowed_files cannot be determined, set executable=false or planning_required=true.",
            "- If verification cannot be determined, set executable=false or planning_required=true.",
            "- Do NOT invent file boundaries from the goal keywords.",
            "- Do NOT output business code.",
            "- Do NOT pretend high confidence when information is uncertain.",
            "",
            "## Output format",
            "Return ONLY raw JSON. No fenced code blocks. No markdown.",
            "",
            'Example: [{"id":"task-001","goal":"...","task_kind":"planning",...}]',
        ]
        return "\n".join(lines)

    def parse_candidate_task_specs(self, text: str) -> tuple[list[dict], list[str]]:
        """Parse JSON candidates from raw text or fenced blocks.

        Returns (candidates, errors).
        """
        if not text or not text.strip():
            return [], ["Empty response from planner engine"]

        raw = text.strip()

        # Try fenced block extraction first
        if "```json" in raw:
            parts = raw.split("```json")
            for part in parts[1:]:
                candidate = part.split("```", 1)[0].strip()
                parsed, err = self._try_parse_json(candidate)
                if parsed is not None:
                    return parsed, []
            return [], ["Could not parse JSON inside ```json fence"]

        if raw.startswith("```"):
            inner = raw.split("```", 2)[1] if raw.count("```") >= 2 else raw.strip("`")
            parsed, err = self._try_parse_json(inner.strip())
            if parsed is not None:
                return parsed, []

        # Try raw JSON
        parsed, err = self._try_parse_json(raw)
        if parsed is not None:
            return parsed, []

        return [], [err or "Unparseable planner response"]

    def validate_candidate_task_specs(
        self, candidates: list[dict]
    ) -> PlannerValidationResult:
        """Validate a list of candidate dicts and return a structured result."""
        result = PlannerValidationResult()
        max_budget = (
            self.context_window
            - self.reserved_output_tokens
            - self.safety_margin_tokens
        )

        known_ids: set[str] = set()
        for c in candidates:
            cid = c.get("id") if isinstance(c, dict) else None
            if cid and self._is_safe_id(str(cid)):
                known_ids.add(str(cid))

        for candidate in candidates:
            if not isinstance(candidate, dict):
                issue = PlannerCandidateIssue(
                    severity="error",
                    field="candidate",
                    message="Candidate is not a dict",
                    value_preview=str(candidate)[:200],
                )
                result.issues.append(issue)
                result.errors.append(issue.message)
                result.invalid_candidates.append(
                    {"raw": candidate, "errors": [issue.message]}
                )
                continue

            cid = candidate.get("id")
            if cid is not None:
                cid = str(cid)

            candidate_errors: list[str] = []
            candidate_warnings: list[str] = []

            # -- id safety --
            if not cid:
                candidate_errors.append("id is empty")
            elif not self._is_safe_id(cid):
                candidate_errors.append(f"id is unsafe: {cid}")

            # -- task_kind / task_type --
            task_kind = str(candidate.get("task_kind", ""))
            task_type = str(candidate.get("task_type", ""))
            if task_kind not in self._VALID_TASK_KINDS:
                candidate_errors.append(
                    f"Invalid task_kind: {task_kind}; must be one of {self._VALID_TASK_KINDS}"
                )
            if task_type not in self._VALID_TASK_TYPES:
                candidate_errors.append(
                    f"Invalid task_type: {task_type}; must be one of {self._VALID_TASK_TYPES}"
                )

            # -- executable / planning_required combo --
            executable = bool(candidate.get("executable", False))
            planning_required = bool(candidate.get("planning_required", False))
            if planning_required and executable:
                candidate_errors.append(
                    "planning_required=True requires executable=False"
                )

            # -- context_budget --
            context_budget = int(candidate.get("context_budget", 0))
            if context_budget <= 0:
                candidate_errors.append(
                    f"context_budget must be > 0, got {context_budget}"
                )
            elif context_budget > max_budget:
                candidate_errors.append(
                    f"context_budget {context_budget} exceeds conservative budget {max_budget}"
                )

            # -- confidence --
            confidence = float(candidate.get("confidence", 0.0))
            if not (0.0 <= confidence <= 1.0):
                candidate_errors.append(
                    f"confidence must be in [0, 1], got {confidence}"
                )

            # -- path safety for allowed_files / forbidden_files --
            allowed_files = list(candidate.get("allowed_files", []))
            forbidden_files = list(candidate.get("forbidden_files", []))
            for f in allowed_files + forbidden_files:
                if not self._is_safe_path(str(f)):
                    candidate_errors.append(f"Unsafe path: {f}")
                if self._is_sensitive_path(str(f)):
                    candidate_errors.append(f"Sensitive path not allowed: {f}")

            # -- executable coding task rules --
            if executable and task_kind == "coding":
                if not allowed_files:
                    candidate_errors.append(
                        "executable coding task must have non-empty allowed_files"
                    )
                verification_data = candidate.get("verification", {})
                if not isinstance(verification_data, dict):
                    candidate_errors.append("verification must be a dict")
                else:
                    verif_kind = str(verification_data.get("kind", ""))
                    if verif_kind not in {"command", "artifact"}:
                        candidate_errors.append(
                            f"executable coding task requires verification kind 'command' or 'artifact', got '{verif_kind}'"
                        )
                    if verif_kind == "command" and not list(
                        verification_data.get("command", [])
                    ):
                        candidate_errors.append(
                            "verification kind='command' requires non-empty command list"
                        )
                    if verif_kind == "artifact" and not list(
                        verification_data.get("expected_artifacts", [])
                    ):
                        candidate_errors.append(
                            "verification kind='artifact' requires non-empty expected_artifacts"
                        )
                done_definition = list(candidate.get("done_definition", []))
                if not done_definition:
                    candidate_errors.append(
                        "executable coding task must have non-empty done_definition"
                    )

            # -- planning task rules --
            if task_kind == "planning" and not executable:
                verification_data = candidate.get("verification", {})
                if isinstance(verification_data, dict):
                    verif_kind = str(verification_data.get("kind", ""))
                    if verif_kind == "contract":
                        pass  # allowed

            # -- depends_on safety --
            depends_on = list(candidate.get("depends_on", []))
            for dep in depends_on:
                dep_str = str(dep)
                if not self._is_safe_id(dep_str):
                    candidate_errors.append(f"Unsafe depends_on id: {dep_str}")
                elif dep_str not in known_ids:
                    candidate_warnings.append(
                        f"depends_on references unknown task id: {dep_str}"
                    )

            # -- low confidence on executable task --
            low_confidence_executable = False
            if executable and confidence < 0.6:
                low_confidence_executable = True
                candidate_warnings.append(
                    f"confidence {confidence} < 0.6 on executable task; downgrading to planning_required"
                )

            # Record issues
            for msg in candidate_errors:
                result.issues.append(
                    PlannerCandidateIssue(
                        candidate_id=cid,
                        severity="error",
                        field="candidate",
                        message=msg,
                    )
                )
                result.errors.append(msg)
            for msg in candidate_warnings:
                result.issues.append(
                    PlannerCandidateIssue(
                        candidate_id=cid,
                        severity="warning",
                        field="candidate",
                        message=msg,
                    )
                )
                result.warnings.append(msg)

            if candidate_errors:
                result.invalid_candidates.append(
                    {"raw": candidate, "errors": candidate_errors}
                )
                continue

            # Build TaskSpec
            try:
                spec = TaskSpec.from_dict(candidate)
            except Exception as exc:
                result.issues.append(
                    PlannerCandidateIssue(
                        candidate_id=cid,
                        severity="error",
                        field="candidate",
                        message=f"Failed to build TaskSpec: {exc}",
                    )
                )
                result.errors.append(str(exc))
                result.invalid_candidates.append(
                    {"raw": candidate, "errors": [str(exc)]}
                )
                continue

            # Downgrade low-confidence executable tasks
            if low_confidence_executable:
                spec.executable = False
                spec.planning_required = True
                result.requires_user_review = True

            # Final TaskSpec-level validation
            task_errors = spec.validate()
            if task_errors:
                for msg in task_errors:
                    result.issues.append(
                        PlannerCandidateIssue(
                            candidate_id=cid,
                            severity="error",
                            field="task_spec",
                            message=msg,
                        )
                    )
                    result.errors.append(msg)
                result.invalid_candidates.append(
                    {"raw": candidate, "errors": task_errors}
                )
                continue

            result.valid_tasks.append(spec)

        return result

    def plan_goal(
        self,
        goal: str,
        planner_engine: Any,
        repo_mode: str = "unknown",
        plan_graph: PlanGraph | None = None,
    ) -> PlannerResult:
        """Plan a goal into candidate TaskSpecs, validate, save, and optionally update PlanGraph."""
        run_id = self.run_id
        result = PlannerResult(run_id=run_id, goal=goal)

        # 1. Build prompt
        prompt = self.build_planning_prompt(goal, repo_mode=repo_mode)

        # 2. Save prompt artifact
        prompt_path = self._write_artifact("planning-prompt.md", prompt)
        result.planning_prompt_path = str(prompt_path)

        # 3. Call planner engine once
        raw_response = self._call_planner_engine(planner_engine, prompt)

        # 4. Save raw response artifact
        raw_ext = "json" if raw_response.strip().startswith(("[", "{")) else "txt"
        raw_path = self._write_artifact(f"planner-raw-response.{raw_ext}", raw_response)
        result.raw_response_path = str(raw_path)

        # 5. Parse JSON
        candidates, parse_errors = self.parse_candidate_task_specs(raw_response)
        if parse_errors:
            result.status = "invalid_response"
            result.next_action = "Refine goal and retry planning"
            result.errors.extend(parse_errors)
            result.issues = [{"severity": "error", "message": e} for e in parse_errors]
            self._save_result_artifact(result)
            self._update_plan_graph_on_failure(plan_graph, result)
            return result

        result.candidate_count = len(candidates)

        # 6. Save candidates artifact
        candidates_path = self._write_artifact(
            "planner-candidates.json",
            json.dumps(candidates, ensure_ascii=False, indent=2) + "\n",
        )
        result.candidate_artifact_path = str(candidates_path)

        # 7. Validate
        validation = self.validate_candidate_task_specs(candidates)

        # 8. Save validation artifact
        validation_path = self._write_artifact(
            "planner-validation.json",
            json.dumps(validation.to_dict(), ensure_ascii=False, indent=2) + "\n",
        )
        result.validation_artifact_path = str(validation_path)

        result.warnings = list(validation.warnings)
        result.errors = list(validation.errors)
        result.issues = [i.to_dict() for i in validation.issues]

        # 9. Save valid tasks to TaskSpecStore
        saved_paths: list[str] = []
        valid_ids: list[str] = []
        for spec in validation.valid_tasks:
            try:
                path = self.task_store.save_task_spec(spec, allow_overwrite=True)
                saved_paths.append(str(path))
                valid_ids.append(spec.id)
            except Exception as exc:
                validation.errors.append(f"Failed to save {spec.id}: {exc}")
                result.errors.append(f"Failed to save {spec.id}: {exc}")

        result.valid_task_ids = valid_ids
        result.saved_task_paths = saved_paths
        result.invalid_candidate_count = len(validation.invalid_candidates)

        # Determine status
        if not valid_ids and candidates:
            result.status = "blocked"
            result.next_action = "Review validation errors and refine goal"
        elif not candidates:
            result.status = "needs_planning"
            result.next_action = "Refine goal; planner returned no candidates"
        elif validation.requires_user_review:
            result.status = "requires_review"
            result.next_action = "Review candidate tasks before execution"
        else:
            result.status = "planned"
            result.next_action = "Review or run candidate tasks"

        # 10. Update PlanGraph
        if plan_graph is not None:
            self._update_plan_graph(plan_graph, validation, result)

        # 11. Save result artifact and return
        self._save_result_artifact(result)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_run_id(self) -> str:
        if self.runtime_store is not None:
            return self.runtime_store.run_id
        return self.task_store.base_dir.name

    def _runtime_base_dir(self) -> Path:
        if self.runtime_store is not None:
            return self.runtime_store.base_dir
        return self.workspace / ".ai-dev" / "runtime" / self.run_id

    def _write_artifact(self, name: str, content: str) -> Path:
        if self.runtime_store is not None:
            return self.runtime_store.write_artifact(name, content)
        base = self._runtime_base_dir() / "artifacts"
        base.mkdir(parents=True, exist_ok=True)
        path = base / name
        path.write_text(content, encoding="utf-8")
        return path

    def _save_result_artifact(self, result: PlannerResult) -> Path:
        return self._write_artifact(
            "planner-result.json",
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
        )

    def _call_planner_engine(self, planner_engine: Any, prompt: str) -> str:
        if hasattr(planner_engine, "run"):
            return str(planner_engine.run(prompt))
        if hasattr(planner_engine, "submit"):
            events = []
            for event in planner_engine.submit(prompt):
                if isinstance(event, (list, tuple)) and len(event) >= 2:
                    events.append(str(event[1]))
                else:
                    events.append(str(event))
            return "\n".join(events)
        raise ValueError(
            "planner_engine must have a 'run' or 'submit' method"
        )

    @staticmethod
    def _try_parse_json(text: str) -> tuple[list[dict] | None, str]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            return None, f"JSON decode error: {exc}"
        except Exception as exc:
            return None, f"Unexpected error parsing JSON: {exc}"

        if isinstance(data, list):
            parsed = [item for item in data if isinstance(item, dict)]
            return parsed, ""
        if isinstance(data, dict):
            if "tasks" in data and isinstance(data["tasks"], list):
                parsed = [item for item in data["tasks"] if isinstance(item, dict)]
                return parsed, ""
            return [data], ""
        return None, "JSON root is neither a list nor a dict with 'tasks'"

    @classmethod
    def _is_safe_id(cls, value: str) -> bool:
        if not value:
            return False
        if value.startswith("/") or value.startswith("\\"):
            return False
        if ".." in value.split("/") or ".." in value.split("\\"):
            return False
        if "/" in value or "\\" in value:
            return False
        return True

    @classmethod
    def _is_safe_path(cls, value: str) -> bool:
        if not value:
            return True  # empty path is not a traversal risk
        if value.startswith("/") or value.startswith("\\"):
            return False
        parts = value.replace("\\", "/").split("/")
        if ".." in parts:
            return False
        return True

    @classmethod
    def _is_sensitive_path(cls, value: str) -> bool:
        parts = value.replace("\\", "/").split("/")
        for part in parts:
            lowered = part.lower()
            for sensitive in cls._SENSITIVE_PARTS:
                if sensitive in lowered:
                    return True
        return False

    def _update_plan_graph(
        self,
        plan_graph: PlanGraph,
        validation: PlannerValidationResult,
        result: PlannerResult,
    ) -> None:
        # Add valid tasks as TaskNodes (avoid duplicates)
        existing_ids = {n.id for n in plan_graph.task_dag}
        for spec in validation.valid_tasks:
            if spec.id not in existing_ids:
                node = TaskNode(
                    id=spec.id,
                    goal=spec.goal,
                    depends_on=list(spec.depends_on),
                    allowed_files=list(spec.allowed_files),
                    forbidden_files=list(spec.forbidden_files),
                    test_strategy=" ".join(spec.verification.command)
                    if spec.verification.command
                    else "",
                    context_budget_hint=spec.context_budget,
                    acceptance_criteria=list(spec.done_definition),
                )
                plan_graph.add_task(node)

        # Add invalid reasons to risks
        for invalid in validation.invalid_candidates:
            errors = invalid.get("errors", [])
            for err in errors:
                plan_graph.add_risk(f"Invalid candidate: {err}")

        # Set next_action based on status
        plan_graph.set_next_action(result.next_action)

    def _update_plan_graph_on_failure(
        self,
        plan_graph: PlanGraph | None,
        result: PlannerResult,
    ) -> None:
        if plan_graph is None:
            return
        plan_graph.set_next_action(result.next_action)
