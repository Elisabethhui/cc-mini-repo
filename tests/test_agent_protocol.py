from pathlib import Path

import pytest

from core.agent_protocol import (
    AgentRegistry,
    AgentResult,
    AgentSpec,
    PermissionBlocked,
    PermissionEnforcer,
    SpawnGuard,
    build_prompt,
)


# ---------------------------------------------------------------------------
# AgentSpec
# ---------------------------------------------------------------------------

def test_spec_requires_positive_budget():
    with pytest.raises(ValueError, match="budget_tokens"):
        AgentSpec(
            role="Test",
            goal="Test",
            input_schema={},
            output_schema={},
            budget_tokens=0,
        )


def test_spec_round_trip():
    spec = AgentSpec(
        role="Implementer",
        goal="Add feature",
        input_schema={"task": "string"},
        output_schema={"status": "string"},
        budget_tokens=5000,
        allowed_actions=["read_file", "write_file"],
        forbidden_actions=["commit", "push"],
        stop_condition="Return JSON",
    )
    assert spec.role == "Implementer"
    assert spec.budget_tokens == 5000
    assert "commit" in spec.forbidden_actions


# ---------------------------------------------------------------------------
# AgentResult
# ---------------------------------------------------------------------------

def test_result_round_trip():
    result = AgentResult(
        status="done",
        changed_files=["src/core/x.py"],
        test_commands=["pytest"],
        risks=["low"],
        next_action="next",
        notes="ok",
    )
    d = result.to_dict()
    restored = AgentResult.from_dict(d)
    assert restored.status == "done"
    assert restored.changed_files == ["src/core/x.py"]
    assert restored.next_action == "next"


def test_result_defaults():
    r = AgentResult()
    assert r.status == ""
    assert r.changed_files == []
    assert r.to_dict() == {
        "status": "",
        "changed_files": [],
        "test_commands": [],
        "risks": [],
        "next_action": "",
        "notes": "",
    }


# ---------------------------------------------------------------------------
# PermissionEnforcer
# ---------------------------------------------------------------------------

def test_enforcer_blocks_exact_forbidden():
    spec = AgentSpec(
        role="Test",
        goal="test",
        input_schema={},
        output_schema={},
        budget_tokens=1000,
        forbidden_actions=["commit", "push"],
    )
    with pytest.raises(PermissionBlocked):
        PermissionEnforcer.check(spec, "commit")


def test_enforcer_blocks_substring_forbidden():
    spec = AgentSpec(
        role="Test",
        goal="test",
        input_schema={},
        output_schema={},
        budget_tokens=1000,
        forbidden_actions=["commit"],
    )
    with pytest.raises(PermissionBlocked):
        PermissionEnforcer.check(spec, "git commit -m msg")


def test_enforcer_allows_safe_action():
    spec = AgentSpec(
        role="Test",
        goal="test",
        input_schema={},
        output_schema={},
        budget_tokens=1000,
        forbidden_actions=["commit"],
        allowed_actions=["read_file"],
    )
    PermissionEnforcer.check(spec, "read_file")  # does not raise


def test_enforcer_validate_warns_on_missing_forbidden():
    spec = AgentSpec(
        role="Test",
        goal="test",
        input_schema={},
        output_schema={},
        budget_tokens=1000,
        forbidden_actions=["commit"],
    )
    warnings = PermissionEnforcer.validate(spec)
    assert any("push" in w for w in warnings)
    assert any("reset --hard" in w for w in warnings)


def test_enforcer_validate_no_warnings_when_fully_guarded():
    spec = AgentSpec(
        role="Test",
        goal="test",
        input_schema={},
        output_schema={},
        budget_tokens=1000,
        forbidden_actions=[
            "commit", "push", "reset --hard", "rm -rf", "delete", "drop",
        ],
    )
    warnings = PermissionEnforcer.validate(spec)
    assert warnings == []


# ---------------------------------------------------------------------------
# SpawnGuard
# ---------------------------------------------------------------------------

def test_spawn_guard_allows_within_limit():
    guard = SpawnGuard(max_depth=2)
    with guard:
        with guard:
            pass


def test_spawn_guard_blocks_at_limit():
    guard = SpawnGuard(max_depth=1)
    with guard:
        with pytest.raises(PermissionBlocked):
            with guard:
                pass


def test_spawn_guard_tracks_depth_correctly():
    guard = SpawnGuard(max_depth=3)
    assert guard._depth == 0
    guard.enter()
    assert guard._depth == 1
    guard.enter()
    assert guard._depth == 2
    guard.exit()
    assert guard._depth == 1
    guard.exit()
    assert guard._depth == 0


# ---------------------------------------------------------------------------
# AgentRegistry
# ---------------------------------------------------------------------------

def test_registry_all_specs():
    specs = AgentRegistry.all_specs()
    assert set(specs.keys()) == {
        "coordinator", "planner", "retriever", "implementer", "tester", "reviewer"
    }
    for name, spec in specs.items():
        assert spec.role.lower() == name
        assert spec.budget_tokens > 0
        assert spec.forbidden_actions
        assert spec.stop_condition


def test_coordinator_cannot_spawn():
    spec = AgentRegistry.coordinator()
    assert "spawn_agent" in spec.forbidden_actions
    assert "run_shell" in spec.forbidden_actions


def test_implementer_cannot_commit():
    spec = AgentRegistry.implementer()
    assert "commit" in spec.forbidden_actions
    assert "push" in spec.forbidden_actions


def test_reviewer_cannot_auto_merge():
    spec = AgentRegistry.reviewer()
    assert "auto_merge" in spec.forbidden_actions
    assert "modify_product_code" in spec.forbidden_actions


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------

def test_build_prompt_with_template(tmp_path):
    template = tmp_path / "implementer.md"
    template.write_text(
        "Role: {{ROLE}}\nGoal: {{GOAL}}\nBudget: {{BUDGET}}\nContext: {{CONTEXT}}",
        encoding="utf-8",
    )
    spec = AgentRegistry.implementer()
    prompt = build_prompt(spec, "ctx", templates_dir=tmp_path)
    assert "Role: " in prompt
    assert spec.goal in prompt
    assert "ctx" in prompt
    assert str(spec.budget_tokens) in prompt


def test_build_prompt_fallback_without_template():
    spec = AgentRegistry.planner()
    prompt = build_prompt(spec, "test context")
    assert spec.role in prompt
    assert "test context" in prompt
    assert "Forbidden Actions" in prompt
    assert "Output Schema" in prompt


def test_build_prompt_uses_builtin_agents_dir():
    agents_dir = Path(".ai-dev/agents")
    if not agents_dir.exists():
        pytest.skip(".ai-dev/agents not present")
    spec = AgentRegistry.retriever()
    prompt = build_prompt(spec, "retrieve symbols", templates_dir=agents_dir)
    assert spec.role in prompt
    assert "retrieve symbols" in prompt
    assert "Rules:" in prompt


# ---------------------------------------------------------------------------
# Permission integration
# ---------------------------------------------------------------------------

def test_agent_spec_enforces_no_spawn():
    """All agent specs must forbid spawning to prevent infinite agents."""
    for name, spec in AgentRegistry.all_specs().items():
        forbidden = {f.lower().strip() for f in spec.forbidden_actions}
        assert "spawn_agent" in forbidden, f"{name} must forbid spawn_agent"


def test_agent_spec_enforces_no_destructive_shell():
    """Destructive actions should be forbidden."""
    for name, spec in AgentRegistry.all_specs().items():
        forbidden = {f.lower().strip() for f in spec.forbidden_actions}
        assert "commit" in forbidden, f"{name} must forbid commit"
        assert "push" in forbidden, f"{name} must forbid push"


def test_agent_result_status_values():
    """AgentResult.status should support expected workflow values."""
    for status in ("done", "revise", "blocked", "error"):
        r = AgentResult(status=status)
        assert r.to_dict()["status"] == status


def test_build_prompt_replaces_all_placeholders():
    """Template placeholders should all be replaced."""
    agents_dir = Path(".ai-dev/agents")
    if not agents_dir.exists():
        pytest.skip(".ai-dev/agents not present")

    for name, spec in AgentRegistry.all_specs().items():
        prompt = build_prompt(spec, "ctx", templates_dir=agents_dir)
        assert "{{" not in prompt, f"{name} prompt has unreplaced placeholders"
        assert spec.goal in prompt
        assert spec.stop_condition in prompt
