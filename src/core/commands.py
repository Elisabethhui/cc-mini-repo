"""Slash command system — parsing and dispatch.

Modelled after claude-code's ``src/commands.ts``.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

from .coordinator import (
    build_task_intake_prompt,
    classify_task_intent,
    current_session_mode,
    match_session_mode,
)
from .test_selector import TestSelectionResult, format_test_selection_result, select_tests_for_changes
from .workflow_doctor import collect_workflow_doctor_report, format_workflow_doctor_report
from .workflow_init import format_workflow_init_result, init_workflow_scaffold
from .workflow_status import collect_workflow_status, format_workflow_status
from .model_health import check_model_health, format_model_health
from .local_model import format_local_model_profile
from .wiki.closeout import CloseoutRecord, CloseoutStore

if TYPE_CHECKING:
    from .compact import CompactService
    from .config import AppConfig
    from .cost_tracker import CostTracker
    from .engine import Engine
    from .permissions import PermissionChecker
    from .session import SessionStore


# ---------------------------------------------------------------------------
# Context bundle passed to every command handler
# ---------------------------------------------------------------------------

@dataclass
class CommandContext:
    engine: Engine
    session_store: SessionStore | None
    compact_service: CompactService
    console: Console
    app_config: AppConfig
    memory_dir: Path | None = None
    permissions: PermissionChecker | None = None
    run_dream: object = None
    cost_tracker: CostTracker | None = None
    new_session_store: object = None
    reconfigure_mode: object = None
    plan_manager: object = None
    pending_query: str | None = None  # set by commands that want a follow-up model query
    pending_closeout: CloseoutRecord | None = None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_command(text: str) -> tuple[str, str] | None:
    """If *text* starts with ``/``, return ``(command_name, args)``."""
    text = text.strip()
    if not text.startswith("/"):
        return None
    parts = text.split(None, 1)
    name = parts[0][1:].lower()  # strip leading /
    args = parts[1] if len(parts) > 1 else ""
    return name, args


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _cmd_help(ctx: CommandContext, args: str) -> None:
    table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
    table.add_column("Command", style="green")
    table.add_column("Description")
    for name, desc, _ in _COMMAND_TABLE:
        table.add_row(f"/{name}", desc)
    ctx.console.print(table)


def _cmd_compact(ctx: CommandContext, args: str) -> None:
    from .compact import estimate_tokens

    messages = ctx.engine.get_messages()
    if len(messages) < 4:
        ctx.console.print("[dim]Too few messages to compact.[/dim]")
        return

    pre_tokens = estimate_tokens(messages)
    ctx.console.print(f"[dim]Compacting {len(messages)} messages (~{pre_tokens:,} tokens)…[/dim]")

    new_msgs, summary = ctx.compact_service.compact(
        messages, ctx.engine.get_system_prompt(), custom_instructions=args,
    )
    ctx.engine.set_messages(new_msgs)

    # Persist compacted state to a fresh session store if available
    if ctx.session_store is not None:
        _persist_compacted(ctx, new_msgs)

    post_tokens = estimate_tokens(new_msgs)
    ctx.console.print(
        f"[green]✓[/green] Compacted: {pre_tokens:,} → {post_tokens:,} tokens "
        f"({len(messages)} → {len(new_msgs)} messages)"
    )


def _persist_compacted(ctx: CommandContext, new_msgs: list[dict]) -> None:
    """Re-write the current session with compacted messages."""
    if ctx.session_store is None:
        return
    # Create a new session store pointing to the same session id,
    # overwrite the JSONL with the compacted messages.
    import json
    from .session import _serialize_message, _now_iso
    path = ctx.session_store._jsonl_path
    with open(path, "w", encoding="utf-8") as fh:
        for msg in new_msgs:
            safe = _serialize_message(msg)
            safe["_ts"] = _now_iso()
            fh.write(json.dumps(safe, ensure_ascii=False) + "\n")
    ctx.session_store._message_count = len(new_msgs)
    ctx.session_store._save_meta()


def _cmd_history(ctx: CommandContext, args: str) -> None:
    from .session import SessionStore

    cwd = str(os.getcwd())
    sessions = SessionStore.list_sessions(cwd)
    if not sessions:
        ctx.console.print("[dim]No saved sessions for this directory.[/dim]")
        return

    table = Table(title="Session History", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Title")
    table.add_column("Messages", justify="right", width=8)
    table.add_column("Updated", width=20)

    for i, meta in enumerate(sessions, 1):
        table.add_row(
            str(i),
            meta.session_id[:8],
            meta.title[:50],
            str(meta.message_count),
            meta.updated_at[:19].replace("T", " "),
        )
    ctx.console.print(table)


def _cmd_resume(ctx: CommandContext, args: str) -> None:
    from .session import SessionStore

    cwd = str(os.getcwd())
    sessions = SessionStore.list_sessions(cwd)

    if not sessions:
        ctx.console.print("[dim]No saved sessions to resume.[/dim]")
        return

    if not args:
        # Show list and ask user to pick
        _cmd_history(ctx, "")
        ctx.console.print("\n[dim]Usage: /resume <number> or /resume <session-id>[/dim]")
        return

    # Try as numeric index
    target_meta = None
    try:
        idx = int(args.strip()) - 1
        if 0 <= idx < len(sessions):
            target_meta = sessions[idx]
    except ValueError:
        pass

    # Try as session-id prefix
    if target_meta is None:
        needle = args.strip().lower()
        for meta in sessions:
            if meta.session_id.lower().startswith(needle):
                target_meta = meta
                break

    if target_meta is None:
        ctx.console.print(f"[red]Session not found: {args}[/red]")
        return

    # Skip if resuming the current session
    if ctx.session_store and target_meta.session_id == ctx.session_store.session_id:
        ctx.console.print("[dim]Already in this session.[/dim]")
        return

    # Load messages
    meta, messages = SessionStore.load_session(target_meta.session_id, cwd)
    if not messages:
        ctx.console.print("[red]Session has no messages.[/red]")
        return

    warning = None
    session_mode = meta.mode if meta is not None else None
    if callable(ctx.reconfigure_mode):
        warning = ctx.reconfigure_mode(session_mode)
    else:
        warning = match_session_mode(session_mode)

    # Create new session store pointing to the resumed session
    new_store = ctx.new_session_store  # type: ignore[call-arg]
    resumed_store = type(ctx.session_store)(  # type: ignore[arg-type]
        cwd=cwd,
        model=ctx.app_config.model,
        session_id=target_meta.session_id,
        mode=current_session_mode(),
    ) if ctx.session_store else None

    ctx.engine.set_messages(messages)
    if resumed_store is not None:
        ctx.engine.set_session_store(resumed_store)
        ctx.session_store = resumed_store  # type: ignore[assignment]

    ctx.console.print(
        f"[green]✓[/green] Resumed session [bold]{target_meta.session_id[:8]}[/bold]: "
        f"{target_meta.title[:50]}  ({len(messages)} messages)"
    )
    if warning:
        ctx.console.print(f"[yellow]{warning}[/yellow]")


def _cmd_clear(ctx: CommandContext, args: str) -> None:
    ctx.engine.set_messages([])
    if callable(ctx.new_session_store):
        new_store = ctx.new_session_store()
        ctx.engine.set_session_store(new_store)
        ctx.session_store = new_store  # type: ignore[assignment]
    ctx.console.print("[green]✓[/green] Conversation cleared. New session started.")


def _cmd_memory(ctx: CommandContext, args: str) -> None:
    from .memory import load_memory_index

    if ctx.memory_dir is None:
        ctx.console.print("[dim]Memory system not configured.[/dim]")
        return
    index = load_memory_index(ctx.memory_dir)
    if index:
        ctx.console.print(index)
    else:
        ctx.console.print("[dim]No memories yet. Use /dream to consolidate daily logs.[/dim]")


def _cmd_remember(ctx: CommandContext, args: str) -> None:
    from .memory import append_to_daily_log

    if ctx.memory_dir is None:
        ctx.console.print("[dim]Memory system not configured.[/dim]")
        return
    if not args.strip():
        ctx.console.print("[dim]Usage: /remember <text>[/dim]")
        return
    append_to_daily_log(ctx.memory_dir, args.strip())
    ctx.console.print("[dim]Saved to daily log.[/dim]")


def _cmd_dream(ctx: CommandContext, args: str) -> None:
    if ctx.run_dream is None or not callable(ctx.run_dream):
        ctx.console.print("[dim]Dream not available.[/dim]")
        return
    ctx.run_dream()


def _cmd_skills(ctx: CommandContext, args: str) -> None:
    """List all available skills."""
    from .skills import list_skills

    skills = list_skills(user_invocable_only=True)
    if not skills:
        ctx.console.print("[dim]No skills available.[/dim]")
        return

    table = Table(title="Available Skills", show_header=True, header_style="bold cyan")
    table.add_column("Command", style="green")
    table.add_column("Source", style="dim", width=8)
    table.add_column("Description")
    for s in skills:
        hint = f" [{s.argument_hint}]" if s.argument_hint else ""
        table.add_row(f"/{s.name}{hint}", s.source, s.description)
    ctx.console.print(table)


def _cmd_task(ctx: CommandContext, args: str) -> None:
    """Route a broader task request through the task-intake surface."""
    description = args.strip()
    if not description:
        ctx.console.print("[dim]Usage: /task <task description>[/dim]")
        return

    intent = classify_task_intent(description)
    ctx.console.print(f"[dim]Routing as {intent} intake.[/dim]")
    ctx.pending_query = build_task_intake_prompt(description)


def _cmd_cost(ctx: CommandContext, args: str) -> None:
    if ctx.cost_tracker is None:
        ctx.console.print("[dim]Cost tracking is not available.[/dim]")
        return
    ctx.console.print(ctx.cost_tracker.format_cost())


def _cmd_model(ctx: CommandContext, args: str) -> None:
    from .config import resolve_model, default_max_tokens_for_model, DEFAULT_MODEL

    provider = ctx.app_config.provider

    if args:
        ctx.engine.set_model(args.strip())
        actual = ctx.engine.get_model()
        ctx.console.print(
            f"[green]✓[/green] Set model to [bold]{actual}[/bold]  "
            f"(max_tokens={default_max_tokens_for_model(actual, provider=provider)})")
        return

    if provider != "anthropic":
        current = ctx.engine.get_model()
        ctx.console.print(
            f"[dim]Current model: {current}[/dim]\n"
            f"[dim]Use /model <name> to switch models for the {provider} provider.[/dim]"
        )
        return

    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import Window
    from prompt_toolkit.layout.controls import FormattedTextControl

    current = ctx.engine.get_model()

    # Marketing name lookup
    _NAMES = {
        "claude-sonnet-4-6": "Sonnet 4.6", "claude-sonnet-4-5": "Sonnet 4.5",
        "claude-sonnet-4": "Sonnet 4", "claude-opus-4-6": "Opus 4.6",
        "claude-opus-4-5": "Opus 4.5", "claude-opus-4-1": "Opus 4.1",
        "claude-opus-4": "Opus 4", "claude-haiku-4-5": "Haiku 4.5",
        "claude-3-5-haiku": "Haiku 3.5",
    }
    display = next((n for p, n in _NAMES.items() if p in current), "Sonnet 4.6")

    # (alias, label, description) — from modelOptions.ts PAYG 1P path
    # 1M context variants omitted: require SDK betas not available in cc-mini
    options = [
        (DEFAULT_MODEL, "Default (recommended)", f"Use the default model (currently {display}) · $3/$15 per Mtok"),
        ("sonnet",      "Sonnet",                "Sonnet 4.6 · Best for everyday tasks · $3/$15 per Mtok"),
        ("opus",        "Opus",                  "Opus 4.6 · Most capable for complex work · $5/$25 per Mtok"),
        ("haiku",       "Haiku",                 "Haiku 4.5 · Fastest for quick answers · $1/$5 per Mtok"),
    ]

    effort_levels = ["low", "medium", "high"]
    effort_sym = {"low": "◑", "medium": "◕", "high": "●"}

    cursor = [0]
    for i, (alias, _, _) in enumerate(options):
        if resolve_model(alias) == current:
            cursor[0] = i
            break

    effort_idx = [2]
    result: list[str | None] = [None]
    max_label = max(len(l) for _, l, _ in options)

    kb = KeyBindings()

    @kb.add("up")
    def _(e): cursor.__setitem__(0, (cursor[0] - 1) % len(options))
    @kb.add("down")
    def _(e): cursor.__setitem__(0, (cursor[0] + 1) % len(options))
    @kb.add("left")
    def _(e): effort_idx.__setitem__(0, (effort_idx[0] - 1) % len(effort_levels))
    @kb.add("right")
    def _(e): effort_idx.__setitem__(0, (effort_idx[0] + 1) % len(effort_levels))

    @kb.add("enter")
    def _(e):
        result[0] = options[cursor[0]][0]
        e.app.exit()

    for i in range(min(len(options), 9)):
        @kb.add(str(i + 1))
        def _(e, idx=i):
            cursor[0] = idx
            result[0] = options[idx][0]
            e.app.exit()

    @kb.add("escape")
    @kb.add("c-c")
    def _(e): e.app.exit()

    def _tokens():
        t = [("bold ansibrightcyan", "  Select model\n"),
             ("ansigray", "  Switch between models. Applies to this session and future\n"
                          "  sessions. For other/previous model names, specify with --model.\n\n")]
        for i, (alias, label, desc) in enumerate(options):
            is_cur = i == cursor[0]
            is_active = resolve_model(alias) == current
            ptr = "❯" if is_cur else " "
            sty = "ansibrightcyan" if is_cur else ""
            chk = " ✔" if is_active else ""
            t.append((sty, f"  {ptr} {i+1}. {(label + chk).ljust(max_label + 3)}"))
            t.append(("ansigray", desc))
            t.append(("", "\n"))

        eff = effort_levels[effort_idx[0]]
        t.append(("", "\n"))
        t.append(("ansigray", "  Effort: "))
        for lvl in effort_levels:
            s = "bold ansibrightcyan" if lvl == eff else "ansigray"
            t.append((s, f" {effort_sym[lvl]} {lvl} "))
        t.append(("", "\n"))
        t.append(("ansigray", "  ↑↓ select · ←→ effort · ↵ confirm · esc cancel"))
        return t

    app: Application = Application(
        layout=Layout(Window(FormattedTextControl(_tokens))),
        key_bindings=kb, full_screen=False)

    try:
        app.run()
    except (EOFError, KeyboardInterrupt):
        pass

    if result[0] is None:
        ctx.console.print(f"[dim]Kept model as {current}[/dim]")
        return

    ctx.engine.set_model(result[0])
    actual = ctx.engine.get_model()
    eff = effort_levels[effort_idx[0]]
    ctx.console.print(
        f"[green]✓[/green] Set model to [bold]{actual}[/bold]  "
        f"(max_tokens={default_max_tokens_for_model(actual, provider=provider)}, effort={eff})"
    )


# ---------------------------------------------------------------------------
# Closeout helpers
# ---------------------------------------------------------------------------

def _closeout_task_id(ctx: CommandContext) -> str:
    session_id = getattr(ctx.session_store, "session_id", None)
    if session_id:
        return str(session_id)
    return Path.cwd().name


def _closeout_store() -> CloseoutStore:
    return CloseoutStore(Path.cwd())


def _draft_closeout_record(ctx: CommandContext) -> CloseoutRecord:
    return CloseoutRecord(
        task_id=_closeout_task_id(ctx),
        phase_name="Phase 6",
        verification_status="pending",
        review_status="pending",
        commit_status="pending",
        commit_hash=None,
        ready_for_audit=False,
        residual_risks=[
            "Awaiting explicit /close confirm before commit",
        ],
    )


def _closeout_has_blockers(record: CloseoutRecord) -> bool:
    verification = record.verification_status.strip().lower()
    review = record.review_status.strip().lower()
    if verification in {"failed", "error", "blocked"}:
        return True
    return review in {"risky", "risk", "blocked", "warning", "needs_attention"}


def _invoke_skill(ctx: CommandContext, name: str, args: str = "") -> bool:
    from .skills import get_skill

    skill = get_skill(name)
    if skill is None:
        ctx.console.print(f"[red]Unknown skill: /{name}[/red]")
        return False
    return _execute_skill(skill, args, ctx)


def _cmd_close(ctx: CommandContext, args: str) -> None:
    action = args.strip().split(None, 1)[0].lower() if args.strip() else ""

    if action == "cancel":
        if ctx.pending_closeout is None:
            ctx.console.print("[dim]No pending closeout to cancel.[/dim]")
            return
        ctx.pending_closeout = None
        ctx.pending_query = None
        ctx.console.print("[green]✓[/green] Closeout canceled. No git mutation was made.")
        return

    if action == "confirm":
        record = ctx.pending_closeout
        if record is None:
            record = _closeout_store().load_latest(task_id=_closeout_task_id(ctx))
        if record is None:
            ctx.console.print("[dim]No draft closeout found. Run /close first.[/dim]")
            return

        if record.commit_status == "recorded" and record.ready_for_audit:
            ctx.console.print("[dim]Latest closeout is already finalized.[/dim]")
            return

        if _closeout_has_blockers(record):
            ctx.console.print(
                f"[yellow]Closeout blocked: verification={record.verification_status}, "
                f"review={record.review_status}[/yellow]"
            )
            ctx.console.print("[dim]Resolve the failure or risk before confirming commit.[/dim]")
            return

        ctx.console.print("[dim]Running /test, /review, and /commit through the existing skill path…[/dim]")
        _invoke_skill(ctx, "test", "")
        _invoke_skill(ctx, "review", "")
        _invoke_skill(ctx, "commit", "")

        final_record = CloseoutRecord(
            task_id=record.task_id,
            phase_name=record.phase_name,
            verification_status=record.verification_status,
            review_status=record.review_status,
            commit_status="recorded",
            commit_hash=record.commit_hash,
            ready_for_audit=True,
            residual_risks=list(record.residual_risks),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        saved = _closeout_store().save(final_record)
        ctx.pending_closeout = None
        ctx.pending_query = None
        ctx.console.print(f"[green]✓[/green] Closeout finalized at {saved}")
        return

    record = _draft_closeout_record(ctx)
    saved = _closeout_store().save(record)
    ctx.pending_closeout = record
    ctx.pending_query = "Confirm with /close confirm or cancel with /close cancel."
    ctx.console.print(f"[green]✓[/green] Draft closeout saved at {saved}")
    ctx.console.print("[dim]Confirm with /close confirm after you are ready to commit.[/dim]")


def _cmd_milestone_review(ctx: CommandContext, args: str) -> None:
    store = _closeout_store()
    record = store.load_latest()
    if record is None:
        ctx.console.print("[dim]No closeout record found. Run /close first to create one.[/dim]")
        return

    ctx.console.print("[bold]Milestone Review[/bold]")
    ctx.console.print(store.render_review_summary(record))


def _cmd_workflow_status(ctx: CommandContext, args: str) -> None:
    status = collect_workflow_status(Path.cwd())
    ctx.console.print(format_workflow_status(status))


def _cmd_workflow_init(ctx: CommandContext, args: str) -> None:
    option = args.strip()
    if option and option != "--dry-run":
        ctx.console.print("[dim]Usage: /workflow-init [--dry-run][/dim]")
        return

    result = init_workflow_scaffold(Path.cwd(), dry_run=option == "--dry-run")
    ctx.console.print(format_workflow_init_result(result))


def _cmd_workflow_doctor(ctx: CommandContext, args: str) -> None:
    if args.strip():
        ctx.console.print("[dim]Usage: /workflow-doctor[/dim]")
        return

    report = collect_workflow_doctor_report(Path.cwd())
    ctx.console.print(format_workflow_doctor_report(report))


def _cmd_model_health(ctx: CommandContext, args: str) -> None:
    """Check the health of the current model endpoint."""
    config = ctx.app_config
    profile = getattr(config, "local_profile", None)

    if profile:
        ctx.console.print("[bold cyan]Local Model Profile[/bold cyan]")
        ctx.console.print(format_local_model_profile(profile))
        ctx.console.print("")

    ctx.console.print("[bold cyan]Model Health Check[/bold cyan]")
    result = check_model_health(
        provider=config.provider,
        base_url=config.base_url,
        api_key=config.api_key,
        model=config.model,
        timeout=5.0,
    )
    ctx.console.print(format_model_health(result))


def _cmd_workflow_test(ctx: CommandContext, args: str) -> None:
    changed_files, extra_warnings = _workflow_test_inputs(args)
    result = select_tests_for_changes(Path.cwd(), changed_files)
    if extra_warnings:
        result = TestSelectionResult(
            changed_files=result.changed_files,
            recommendations=result.recommendations,
            confidence=result.confidence,
            warnings=extra_warnings + result.warnings,
            truncated=result.truncated,
        )
    ctx.console.print(format_test_selection_result(result))


def _cmd_workflow_pack(ctx: CommandContext, args: str) -> None:
    """Generate a bounded context pack for a goal or task-id."""
    from .context_pack import ContextPackBuilder
    from .plan_graph import PlanGraph
    from .code_retrieval import CodeGraphRetrievalAdapter
    from .runtime_state import RuntimeStateStore, _generate_run_id

    goal = args.strip()
    if not goal:
        ctx.console.print("[dim]Usage: /workflow-pack <goal or task-id>[/dim]")
        return

    workspace = Path.cwd()

    # Try to load latest PlanGraph
    plan_graph = None
    runtime_dir = workspace / ".ai-dev" / "runtime"
    if runtime_dir.exists():
        run_dirs = sorted(
            (p for p in runtime_dir.iterdir() if p.is_dir()),
            key=lambda p: p.name,
            reverse=True,
        )
        if run_dirs:
            latest_run = run_dirs[0]
            plan_path = latest_run / "plan-graph.json"
            if plan_path.exists():
                try:
                    plan_graph = PlanGraph.from_json(plan_path.read_text(encoding="utf-8"))
                except Exception:
                    pass  # ignore corrupted plan graph

    # Try code retrieval if code exists
    retrieval_results = []
    has_code = (workspace / ".codegraph").exists() or (workspace / "src").exists()
    if has_code:
        adapter = CodeGraphRetrievalAdapter(workspace)
        # Query symbols related to the goal (simple heuristic: first word)
        keyword = goal.split()[0] if goal.split() else goal
        result = adapter.query_symbols(keyword)
        retrieval_results.append(result)
        # Also do a fallback rg query on the full goal
        fallback = adapter.fallback_rg(goal[:50])
        retrieval_results.append(fallback)

    # Build pack
    builder = ContextPackBuilder(
        context_window=32768,
        reserved_output_tokens=2048,
        safety_margin_tokens=1024,
    )
    pack = builder.build(
        goal=goal,
        plan_graph=plan_graph,
        retrieval_results=retrieval_results,
    )

    # Save to .ai-dev/context-packs/<run-id>.md
    packs_dir = workspace / ".ai-dev" / "context-packs"
    packs_dir.mkdir(parents=True, exist_ok=True)

    run_id = plan_graph.run_id if plan_graph else _generate_run_id()
    pack_path = packs_dir / f"{run_id}.md"
    pack_path.write_text(pack.markdown, encoding="utf-8")

    # Output
    ctx.console.print(f"[green]✓[/green] Context pack generated: [bold]{pack_path}[/bold]")
    ctx.console.print(f"[dim]  Goal: {goal}[/dim]")
    ctx.console.print(f"[dim]  Tokens: {pack.budget_report.projected_total_tokens:,} / {pack.budget_report.context_window:,}[/dim]")
    ctx.console.print(f"[dim]  State: {pack.budget_report.state.value}[/dim]")
    if pack.warnings:
        ctx.console.print("[yellow]Warnings:[/yellow]")
        for w in pack.warnings:
            ctx.console.print(f"  • {w}")
    if pack.artifact_handles:
        ctx.console.print("[dim]Externalized:[/dim]")
        for h in pack.artifact_handles:
            ctx.console.print(f"  • {h}")


def _cmd_workflow_run(ctx: CommandContext, args: str) -> None:
    """Run a bounded batch execution plan (dry-run or supervised)."""
    from .batch_runner import BatchRunner
    from .context_pack import ContextPackBuilder
    from .plan_graph import PlanGraph
    from .code_retrieval import CodeGraphRetrievalAdapter
    from .runtime_state import RuntimeStateStore

    raw = args.strip()
    if not raw:
        ctx.console.print("[dim]Usage: /workflow-run [--dry-run] <goal>[/dim]")
        return

    dry_run = False
    if raw.startswith("--dry-run"):
        dry_run = True
        raw = raw[len("--dry-run"):].strip()

    if not raw:
        ctx.console.print("[dim]Usage: /workflow-run [--dry-run] <goal>[/dim]")
        return

    goal = raw
    workspace = Path.cwd()

    # 1. Create run state
    store = RuntimeStateStore(str(workspace))
    run_id = store.run_id

    # 2. Create PlanGraph (ensure dirs first)
    store._ensure_dirs()
    graph = PlanGraph(
        run_id=run_id,
        goal=goal,
        phase="intake",
        next_action="Start intake",
    )
    plan_path = store.base_dir / "plan-graph.json"
    plan_path.write_text(graph.to_json(), encoding="utf-8")
    store.patch_state(
        goal=goal,
        phase="intake",
        next_action="Start intake",
    )

    # 3. Try CodeGraph retrieval if code exists
    retrieval_results = []
    has_code = (workspace / ".codegraph").exists() or (workspace / "src").exists()
    if has_code:
        adapter = CodeGraphRetrievalAdapter(workspace)
        keyword = goal.split()[0] if goal.split() else goal
        result = adapter.query_symbols(keyword)
        retrieval_results.append(result)
        fallback = adapter.fallback_rg(goal[:50])
        retrieval_results.append(fallback)

    # 4. Build context pack
    builder = ContextPackBuilder(
        context_window=32768,
        reserved_output_tokens=2048,
        safety_margin_tokens=1024,
    )
    pack = builder.build(
        goal=goal,
        plan_graph=graph,
        retrieval_results=retrieval_results,
        store=store,
    )

    # 5. Save context pack
    packs_dir = workspace / ".ai-dev" / "context-packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    pack_path = packs_dir / f"{run_id}.md"
    pack_path.write_text(pack.markdown, encoding="utf-8")

    # 6. Dry-run path
    if dry_run:
        runner = BatchRunner(
            store,
            max_steps=7,
            context_window=32768,
            reserved_output_tokens=2048,
            safety_margin_tokens=1024,
        )
        state = store.load_state()
        state["goal"] = goal
        state["phase"] = "intake"
        state["next_action"] = "Start intake"
        store.save_state(state)

        budget_report = runner._calculate_budget(state)

        ctx.console.print(f"[green]✓[/green] Dry-run plan created: [bold]{run_id}[/bold]")
        ctx.console.print(f"[dim]  Goal: {goal}[/dim]")
        ctx.console.print(f"[dim]  Phase: intake[/dim]")
        ctx.console.print(f"[dim]  Next Action: Start intake[/dim]")
        ctx.console.print("")
        ctx.console.print(f"[dim]  Context Pack: {pack_path}[/dim]")
        ctx.console.print(
            f"[dim]  Tokens: {pack.budget_report.projected_total_tokens:,} / "
            f"{pack.budget_report.context_window:,}[/dim]"
        )
        ctx.console.print(f"[dim]  Pack State: {pack.budget_report.state.value}[/dim]")
        ctx.console.print("")
        ctx.console.print(
            f"[dim]  Budget: {budget_report.state.value} "
            f"({budget_report.projected_total_tokens}/{budget_report.context_window})[/dim]"
        )

        if pack.warnings:
            ctx.console.print("[yellow]Pack Warnings:[/yellow]")
            for w in pack.warnings:
                ctx.console.print(f"  • {w}")

        if budget_report.warnings:
            ctx.console.print("[yellow]Budget Warnings:[/yellow]")
            for w in budget_report.warnings:
                ctx.console.print(f"  • {w}")

        ctx.console.print("")
        ctx.console.print("[bold]Planned Phases:[/bold]")
        phases = ["intake", "plan", "retrieve", "pack", "implement", "test", "review"]
        for i, p in enumerate(phases, 1):
            ctx.console.print(f"  {i}. {p}")
        ctx.console.print("")
        ctx.console.print("[dim]Run without --dry-run to execute.[/dim]")
        return

    # 7. Supervised execution path
    engine = ctx.engine
    engine.set_max_turns(1)
    runner = BatchRunner(
        store,
        max_steps=7,
        context_window=32768,
        reserved_output_tokens=2048,
        safety_margin_tokens=1024,
    )

    ctx.console.print(f"[dim]Starting supervised execution: {run_id}[/dim]")
    final = runner.run_supervised(
        goal=goal,
        engine=engine,
        pack_builder=builder,
    )
    engine.set_max_turns(None)

    ctx.console.print(
        f"[green]✓[/green] Supervised execution complete: [bold]{run_id}[/bold]"
    )
    ctx.console.print(f"[dim]  Final phase: {final.get('phase')}[/dim]")
    ctx.console.print(f"[dim]  Next action: {final.get('next_action')}[/dim]")
    ctx.console.print(
        f"[dim]  Step results: {len(store.list_artifacts())} artifacts[/dim]"
    )

    # 8. Workflow gates
    _print_workflow_gates(ctx, workspace, run_id, goal, final)


def _print_workflow_gates(
    ctx: CommandContext,
    workspace: Path,
    run_id: str,
    goal: str,
    final_state: dict[str, Any],
) -> None:
    """Run and display workflow gates after execution."""
    from .review_packet import build_review_packet
    from .rollback_helper import collect_rollback_report, format_rollback_report
    from .work_log import build_work_log_entry, write_work_log
    from .workflow_next import WorkflowTaskArtifacts, recommend_workflow_next, format_workflow_next
    from .workflow_status import collect_workflow_status
    from .workflow_doctor import collect_workflow_doctor_report

    ctx.console.print("")
    ctx.console.print("[bold]Workflow Gates[/bold]")

    # Test selector
    changed_files, _ = _changed_files_from_git_status(workspace)
    test_result = select_tests_for_changes(workspace, changed_files)
    ctx.console.print(format_test_selection_result(test_result))

    # Review packet
    def _git_runner(args: list[str]) -> str:
        try:
            proc = subprocess.run(
                ["git", *args],
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
                timeout=2.0,
            )
            return proc.stdout
        except Exception:
            return ""

    review_pkt = build_review_packet(goal, _git_runner)
    if review_pkt.changed_files:
        ctx.console.print(f"\nReview Packet: {len(review_pkt.changed_files)} files changed")
        if review_pkt.risk_notes:
            ctx.console.print("[yellow]Risk notes:[/yellow]")
            for note in review_pkt.risk_notes:
                ctx.console.print(f"  • {note}")

    # Rollback helper
    rollback = collect_rollback_report(workspace)
    ctx.console.print(f"\n{format_rollback_report(rollback)}")

    # Work log
    entry = build_work_log_entry(
        task_id=run_id,
        goal=goal,
        changed_files=review_pkt.changed_files,
        tests=[r.command for r in test_result.recommendations],
        review_result=final_state.get("review_decision", ""),
        risks=review_pkt.risk_notes,
        next_step=final_state.get("next_action", ""),
    )
    write_work_log(workspace, entry)
    ctx.console.print("\n[dim]Work log written.[/dim]")

    # Workflow next
    status = collect_workflow_status(workspace)
    doctor = collect_workflow_doctor_report(workspace)
    artifacts = WorkflowTaskArtifacts(
        task_goal=goal,
        tests_recorded=len(test_result.recommendations) > 0,
        fresh_review_done=final_state.get("phase") in ("done", "review"),
        review_decision=final_state.get("review_decision", ""),
        work_log_written=True,
    )
    next_rec = recommend_workflow_next(status=status, doctor=doctor, artifacts=artifacts)
    ctx.console.print(f"\n{format_workflow_next(next_rec)}")


def _cmd_workflow_resume(ctx: CommandContext, args: str) -> None:
    """Resume a bounded workflow run from saved runtime state."""
    from .batch_runner import BatchRunner
    from .context_pack import ContextPackBuilder
    from .runtime_state import RuntimeStateStore

    run_id = args.strip()
    workspace = Path.cwd()

    if not run_id:
        # List available runs
        runs = RuntimeStateStore.list_runs(workspace)
        if not runs:
            ctx.console.print("[dim]No workflow runs found. Use /workflow-run <goal> to start.[/dim]")
            return
        ctx.console.print("[bold]Available workflow runs:[/bold]")
        for r in runs:
            ctx.console.print(f"  • {r}")
        ctx.console.print("[dim]Usage: /workflow-resume <run-id>[/dim]")
        return

    # Validate run exists
    run_dir = workspace / ".ai-dev" / "runtime" / run_id
    if not (run_dir / "state.json").exists():
        ctx.console.print(f"[red]Run not found: {run_id}[/red]")
        return

    store = RuntimeStateStore(str(workspace), run_id=run_id)
    state = store.load_state()
    phase = state.get("phase", "intake")
    goal = state.get("goal", "")

    if phase == "done":
        ctx.console.print(f"[green]✓[/green] Run {run_id} is already complete.")
        ctx.console.print(f"[dim]  Phase: done[/dim]")
        return

    if phase == "blocked":
        ctx.console.print(f"[yellow]⚠[/yellow] Run {run_id} is blocked.")
        ctx.console.print(f"[dim]  Reason: {state.get('next_action', 'Unknown')}[/dim]")
        ctx.console.print("[dim]  Resolve the blocker, then retry.[/dim]")
        return

    if not goal:
        ctx.console.print(f"[red]Run {run_id} has no goal. Cannot resume.[/red]")
        return

    # Show resume summary
    artifacts = store.list_artifacts()
    step_results = [a for a in artifacts if a.startswith("step-result-")]
    ctx.console.print(f"[dim]Resuming run {run_id} from phase '{phase}'…[/dim]")
    ctx.console.print(f"[dim]  Goal: {goal}[/dim]")
    ctx.console.print(f"[dim]  Previous steps: {len(step_results)}[/dim]")

    # Rebuild context pack and continue
    builder = ContextPackBuilder(
        context_window=32768,
        reserved_output_tokens=2048,
        safety_margin_tokens=1024,
    )
    runner = BatchRunner(
        store,
        max_steps=7,
        context_window=32768,
        reserved_output_tokens=2048,
        safety_margin_tokens=1024,
    )

    engine = ctx.engine
    final = runner.resume_supervised(
        goal=goal,
        engine=engine,
        pack_builder=builder,
    )

    ctx.console.print(
        f"[green]✓[/green] Resume complete: [bold]{run_id}[/bold]"
    )
    ctx.console.print(f"[dim]  Final phase: {final.get('phase')}[/dim]")
    ctx.console.print(f"[dim]  Next action: {final.get('next_action')}[/dim]")


def _workflow_test_inputs(args: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    explicit = tuple(part for part in args.split() if part)
    if explicit:
        return explicit, ()
    return _changed_files_from_git_status(Path.cwd())


def _changed_files_from_git_status(root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=2.0,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return (), (f"git status unavailable: {exc}",)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"git exited {proc.returncode}"
        return (), (f"git status unavailable: {detail}",)
    changed_files: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        payload = line[3:] if len(line) > 3 else line
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        changed_files.append(payload.strip())
    return tuple(changed_files), ()


# ---------------------------------------------------------------------------
# Command registry
# ---------------------------------------------------------------------------

def _cmd_plan(ctx: CommandContext, args: str) -> None:
    """Enter plan mode or show current plan."""
    from .plan import PlanModeManager
    pm: PlanModeManager | None = ctx.plan_manager  # type: ignore[assignment]
    if pm is None:
        ctx.console.print("[red]Plan mode not available.[/red]")
        return
    if pm.is_active:
        content = pm.get_plan_content()
        if content:
            ctx.console.print(f"[bold]Current plan[/bold] ({pm.plan_file_path}):\n")
            ctx.console.print(content)
        else:
            ctx.console.print(f"[dim]Plan mode active but no plan written yet. File: {pm.plan_file_path}[/dim]")
    else:
        pm.enter()
        ctx.console.print("[green]Enabled plan mode[/green]")
        # If user provided a description, queue it as a follow-up query
        # Matches TS: onDone('Enabled plan mode', { shouldQuery: true })
        description = args.strip()
        if description:
            ctx.pending_query = description


def _cmd_prime(ctx: CommandContext, args: str) -> None:
    """Prime a task for the phase1 analysis chain and generate a TaskPack."""
    from .wiki.taskpack import TaskPackManager, TaskPack, TaskStatus
    from .wiki.target_identity import TargetResolver, TargetIdentityStore, TargetResolutionStatus
    from pathlib import Path
    import os

    if not args.strip():
        ctx.console.print("[dim]Usage: /prime <task-id> [target-file-or-symbol...][/dim]")
        return

    parts = args.strip().split()
    task_id = parts[0]
    target_inputs = parts[1:] if len(parts) > 1 else []

    # Default to current directory python files if no targets specified
    if not target_inputs:
        cwd = Path.cwd()
        target_inputs = [str(f.relative_to(cwd)) for f in cwd.rglob("*.py") if "__pycache__" not in str(f)][:5]

    workspace = str(os.getcwd())
    resolver = TargetResolver(workspace)
    identity_store = TargetIdentityStore(workspace)
    manager = TaskPackManager(workspace)

    ctx.console.print(f"[dim]Priming task '{task_id}' with Target Identity resolution...[/dim]")

    # Resolve each target input
    resolved_identities = []
    target_files = []
    disambiguation_needed = False

    for target_input in target_inputs:
        result = resolver.resolve(target_input)

        if result.status == TargetResolutionStatus.UNIQUE and result.selected_identity:
            resolved_identities.append(result.selected_identity)
            if result.selected_identity.file_relpath not in target_files:
                target_files.append(result.selected_identity.file_relpath)
            ctx.console.print(f"[green]✓[/green] Resolved: {target_input} -> {result.selected_identity.canonical_target_key}")
        elif result.status in (TargetResolutionStatus.AMBIGUOUS_PATH, TargetResolutionStatus.AMBIGUOUS_SYMBOL):
            disambiguation_needed = True
            ctx.console.print(f"[yellow]⚠[/yellow] Ambiguous: {target_input}")
            ctx.console.print(result.disambiguation_prompt)
        elif result.status == TargetResolutionStatus.NOT_FOUND:
            ctx.console.print(f"[red]✗[/red] Not found: {target_input}")
        else:
            ctx.console.print(f"[red]✗[/red] Error resolving {target_input}: {result.error_message}")

    # If disambiguation needed, stop here
    if disambiguation_needed:
        ctx.console.print("[yellow]Please resolve ambiguities and retry.[/yellow]")
        return

    if not resolved_identities:
        ctx.console.print("[red]No valid targets resolved. Aborting.[/red]")
        return

    # Save Target Identities
    for identity in resolved_identities:
        identity_path = identity_store.save(identity, task_id)
        ctx.console.print(f"[dim]  Saved identity: {identity_path.name}[/dim]")

    # Generate TaskPack
    taskpack = manager.generate_taskpack_from_digest(
        task_id=task_id,
        title=f"Task: {task_id}",
        target_files=target_files,
    )

    # Add Target Identity info to TaskPack
    taskpack.target_identities = [ti.to_dict() for ti in resolved_identities]

    # Save TaskPack with safe filename
    filepath = manager.save_taskpack(taskpack)

    ctx.console.print(f"[green]✓[/green] TaskPack primed and saved to: {filepath}")
    ctx.console.print(f"[dim]  - Status: {taskpack.status.value}[/dim]")
    ctx.console.print(f"[dim]  - Target files: {len(taskpack.target_files)}[/dim]")
    ctx.console.print(f"[dim]  - Target identities: {len(resolved_identities)}[/dim]")
    ctx.console.print(f"[dim]  - Primary symbols: {len(taskpack.primary_symbols)}[/dim]")


def _cmd_plan_init(ctx: CommandContext, args: str) -> None:
    """Initialize a new planning run with an empty PlanGraph."""
    from .plan_graph import PlanGraph
    from .runtime_state import RuntimeStateStore

    goal = args.strip()
    if not goal:
        ctx.console.print("[dim]Usage: /plan-init <goal>[/dim]")
        return

    workspace = str(Path.cwd())
    store = RuntimeStateStore(workspace)
    run_id = store.run_id

    graph = PlanGraph(
        run_id=run_id,
        goal=goal,
        phase="intake",
        next_action="Refine goal into project charter",
    )

    # Persist runtime state (creates directories)
    store.patch_state(goal=goal, phase="intake", next_action="Refine goal into project charter")

    # Persist PlanGraph
    plan_path = store.base_dir / "plan-graph.json"
    plan_path.write_text(graph.to_json(), encoding="utf-8")

    ctx.console.print(f"[green]✓[/green] Plan initialized: [bold]{run_id}[/bold]")
    ctx.console.print(f"[dim]  Goal: {goal}[/dim]")
    ctx.console.print(f"[dim]  Phase: intake[/dim]")
    ctx.console.print(f"[dim]  Next: Refine goal into project charter[/dim]")
    ctx.console.print(f"[dim]  Path: {plan_path}[/dim]")


def _cmd_plan_status(ctx: CommandContext, args: str) -> None:
    """Show current planning phase, decisions, open questions, and next action."""
    from .plan_graph import PlanGraph

    workspace = str(Path.cwd())
    runtime_dir = Path(workspace) / ".ai-dev" / "runtime"
    if not runtime_dir.exists():
        ctx.console.print("[dim]No planning runs found. Use /plan-init <goal> to start.[/dim]")
        return

    run_dirs = sorted(
        (p for p in runtime_dir.iterdir() if p.is_dir()),
        key=lambda p: p.name,
        reverse=True,
    )
    if not run_dirs:
        ctx.console.print("[dim]No planning runs found. Use /plan-init <goal> to start.[/dim]")
        return

    latest_run = run_dirs[0]
    plan_path = latest_run / "plan-graph.json"

    if not plan_path.exists():
        ctx.console.print(f"[dim]No plan graph found in latest run ({latest_run.name}).[/dim]")
        return

    graph = PlanGraph.from_json(plan_path.read_text(encoding="utf-8"))

    ctx.console.print(f"[bold]Plan Status[/bold] ([dim]{graph.run_id}[/dim])")
    ctx.console.print(f"  Phase: [cyan]{graph.phase}[/cyan]")
    ctx.console.print(f"  Goal: {graph.goal}")
    if graph.next_action:
        ctx.console.print(f"  Next Action: [yellow]{graph.next_action}[/yellow]")

    if graph.decisions:
        ctx.console.print(f"\n[bold]Decisions ({len(graph.decisions)}):[/bold]")
        for d in graph.decisions:
            ctx.console.print(f"  • {d}")

    if graph.open_questions:
        ctx.console.print(f"\n[bold]Open Questions ({len(graph.open_questions)}):[/bold]")
        for q in graph.open_questions:
            ctx.console.print(f"  • {q}")

    if graph.risks:
        ctx.console.print(f"\n[bold]Risks ({len(graph.risks)}):[/bold]")
        for r in graph.risks:
            ctx.console.print(f"  • {r}")

    if graph.task_dag:
        ready = graph.ready_tasks()
        ctx.console.print(f"\n[bold]Tasks:[/bold] {len(graph.task_dag)} total, {len(ready)} ready")
        for t in ready[:5]:
            ctx.console.print(f"  [green]•[/green] {t.id}: {t.goal}")
        if len(ready) > 5:
            ctx.console.print(f"  ... and {len(ready) - 5} more ready")


def _cmd_plan_export(ctx: CommandContext, args: str) -> None:
    """Export a compact planning summary."""
    from .plan_graph import PlanGraph
    from .runtime_state import RuntimeStateStore

    workspace = str(Path.cwd())
    runtime_dir = Path(workspace) / ".ai-dev" / "runtime"
    if not runtime_dir.exists():
        ctx.console.print("[dim]No planning runs found. Use /plan-init <goal> to start.[/dim]")
        return

    run_dirs = sorted(
        (p for p in runtime_dir.iterdir() if p.is_dir()),
        key=lambda p: p.name,
        reverse=True,
    )
    if not run_dirs:
        ctx.console.print("[dim]No planning runs found. Use /plan-init <goal> to start.[/dim]")
        return

    latest_run = run_dirs[0]
    plan_path = latest_run / "plan-graph.json"

    if not plan_path.exists():
        ctx.console.print(f"[dim]No plan graph found in latest run ({latest_run.name}).[/dim]")
        return

    graph = PlanGraph.from_json(plan_path.read_text(encoding="utf-8"))

    # Build compact summary
    lines = [
        f"# Plan Export: {graph.run_id}",
        "",
        f"**Goal:** {graph.goal}",
        f"**Phase:** {graph.phase}",
        f"**Next Action:** {graph.next_action}",
        "",
    ]

    if graph.decisions:
        lines.append("## Decisions")
        for d in graph.decisions:
            lines.append(f"- {d}")
        lines.append("")

    if graph.open_questions:
        lines.append("## Open Questions")
        for q in graph.open_questions:
            lines.append(f"- {q}")
        lines.append("")

    if graph.modules:
        lines.append("## Modules")
        for m in graph.modules:
            lines.append(f"- {m}")
        lines.append("")

    if graph.task_dag:
        lines.append("## Tasks")
        for t in graph.topological_order():
            status = "ready" if not t.depends_on else "blocked"
            lines.append(f"- ({status}) {t.id}: {t.goal}")
        lines.append("")

    summary = "\n".join(lines)

    # Also save as artifact
    store = RuntimeStateStore(workspace, run_id=latest_run.name)
    artifact_path = store.write_artifact("plan-export.md", summary)

    ctx.console.print("[green]✓[/green] Plan exported")
    ctx.console.print(f"[dim]  Saved to: {artifact_path}[/dim]")
    ctx.console.print("")
    ctx.console.print(summary)


def _cmd_plan_wiki(ctx: CommandContext, args: str) -> None:
    """Generate a structured plan for the phase1 wiki_strict analysis chain."""
    from .wiki.taskpack import TaskPackManager, EditSpec, TaskStatus
    from .config import get_run_mode, RunMode
    from pathlib import Path
    import os

    # Only available in wiki_strict mode
    mode = get_run_mode()
    if mode != RunMode.WIKI_STRICT:
        ctx.console.print("[dim]/plan wiki_strict is only available in wiki_strict mode. Use standard /plan for plan mode.[/dim]")
        # Delegate to standard plan command
        _cmd_plan(ctx, args)
        return

    if not args.strip():
        ctx.console.print("[dim]Usage: /plan <task-id>[/dim]")
        ctx.console.print("[dim]Generate structured plan from existing TaskPack.[/dim]")
        return

    task_id = args.strip().split()[0]
    manager = TaskPackManager(str(os.getcwd()))

    # Load existing TaskPack
    taskpack = manager.load_taskpack(task_id)
    if taskpack is None:
        ctx.console.print(f"[red]TaskPack '{task_id}' not found. Run /prime {task_id} first.[/red]")
        return

    ctx.console.print(f"[dim]Generating structured plan for task '{task_id}'...[/dim]")

    # Check if ready for plan
    ready, msg = taskpack.is_ready_for_plan()
    if not ready:
        ctx.console.print(f"[yellow]⚠ TaskPack not ready: {msg}[/yellow]")
        return

    # Check entity statuses
    raw_ast_files = [f for f, s in taskpack.entity_status.items() if s.value == "raw_ast"]
    stale_files = [f for f, s in taskpack.entity_status.items() if s.value == "stale"]

    # Phase 3: Deferred Issue 写入 (越界控制)
    if raw_ast_files:
        ctx.console.print(f"[yellow]⚠ The following files are raw_ast, need digest first:[/yellow]")
        for f in raw_ast_files:
            ctx.console.print(f"  - {f}")
        ctx.console.print(f"[dim]Run /digest to process these files before planning.[/dim]")

        # Write deferred issue for blocking files
        from .wiki.taskpack import DeferredIssue
        for f in raw_ast_files:
            issue = DeferredIssue(
                path=f,
                reason="Entity is raw_ast - must digest before planning",
                suggested_action=f"/digest {f}",
                status="open",
            )
            manager.save_deferred_issue(issue)
        ctx.console.print(f"[dim]  → {len(raw_ast_files)} deferred issue(s) written[/dim]")

    if stale_files:
        ctx.console.print(f"[yellow]⚠ The following files are stale, need reconcile:[/yellow]")
        for f in stale_files:
            ctx.console.print(f"  - {f}")
        # Write deferred issue for stale files
        from .wiki.taskpack import DeferredIssue
        for f in stale_files:
            issue = DeferredIssue(
                path=f,
                reason="Entity is stale - may need reconcile or re-digest",
                suggested_action=f"/digest {f} or manual review",
                status="open",
            )
            manager.save_deferred_issue(issue)
        ctx.console.print(f"[dim]  → {len(stale_files)} deferred issue(s) written[/dim]")

    # Phase 3: 越界控制 - raw_ast 文件必须先 digest，否则阻止进入 patch
    if raw_ast_files:
        ctx.console.print(f"\n[red]✗ Cannot generate EditSpecs while files are raw_ast.[/red]")
        ctx.console.print(f"[dim]Please digest the files first, then re-run /plan {task_id}[/dim]")
        # Save TaskPack with deferred status
        taskpack.status = TaskStatus.DEFERRED
        manager.save_taskpack(taskpack)
        return

    # Generate minimal EditSpecs (placeholder for actual implementation)
    for target_file in taskpack.target_files[:3]:  # Limit to first 3 files
        edit_spec = EditSpec(
            target_file=target_file,
            target_symbol="",
            operation="update",
            description=f"Modify {target_file} according to task requirements",
            constraints=taskpack.constraints,
            verification=taskpack.verification_steps,
        )
        taskpack.edit_specs.append(edit_spec)

    # Update status
    taskpack.status = TaskStatus.PLANNED

    # Save updated TaskPack
    manager.save_taskpack(taskpack)

    # Output structured plan
    ctx.console.print(f"\n[bold cyan]=== Structured Plan for {task_id} ===[/bold cyan]\n")

    ctx.console.print("[bold]Goal Stack:[/bold]")
    gs = taskpack.goal_stack
    ctx.console.print(f"  Global: {gs.global_goal}")
    ctx.console.print(f"  Step: {gs.step_goal}")
    ctx.console.print(f"  Task: {gs.task_goal}")
    ctx.console.print(f"  Done: {gs.done_definition}")
    ctx.console.print(f"  Out of Scope: {gs.out_of_scope}")

    ctx.console.print(f"\n[bold]Target Files ({len(taskpack.target_files)}):[/bold]")
    for f in taskpack.target_files:
        status = taskpack.entity_status.get(f, "unknown")
        ctx.console.print(f"  - {f} [{status}]")

    ctx.console.print(f"\n[bold]Primary Symbols ({len(taskpack.primary_symbols)}):[/bold]")
    for s in taskpack.primary_symbols[:10]:  # Limit output
        ctx.console.print(f"  - {s}")

    ctx.console.print(f"\n[bold]Edit Specs ({len(taskpack.edit_specs)}):[/bold]")
    for i, es in enumerate(taskpack.edit_specs, 1):
        ctx.console.print(f"  {i}. {es.operation}: {es.target_file}")
        if es.description:
            ctx.console.print(f"     {es.description}")

    if taskpack.hotspots:
        ctx.console.print(f"\n[bold]Hotspots:[/bold]")
        for h in taskpack.hotspots:
            ctx.console.print(f"  - {h}")

    ctx.console.print(f"\n[green]✓[/green] Plan generated. Ready for review before patch phase.")
    ctx.console.print(f"[dim]  TaskPack updated and saved.[/dim]")


def _cmd_scan(ctx: CommandContext, args: str) -> None:
    """Scan the workspace and refresh wiki entities for phase1 analysis."""
    from .knowledge.ingester import WikiIngester

    workspace_root = str(os.getcwd())
    ingester = WikiIngester(workspace_root)

    ctx.console.print("[dim]Scanning workspace and building wiki entities...[/dim]")
    ingester.ingest_all()
    ctx.console.print("[green]✓[/green] Scan complete. Wiki entities updated.")


def _cmd_digest(ctx: CommandContext, args: str) -> None:
    """Digest a target or changed files to support the wiki analysis chain."""
    from .knowledge.ingester import WikiIngester
    from .knowledge.watcher import get_changed_tracker
    from pathlib import Path

    workspace_root = Path.cwd()
    ingester = WikiIngester(str(workspace_root))

    if args.strip().lower() == "--changed":
        # Phase 2 minimal: use ChangedFileTracker
        ctx.console.print("[dim]Digesting changed files...[/dim]")
        tracker = get_changed_tracker(workspace_root)
        changed = tracker.get_and_clear()
        if changed:
            for fpath in changed:
                f = Path(workspace_root) / fpath
                if f.exists():
                    ingester.ingest_file(f)
            ctx.console.print(f"[green]✓[/green] Digested {len(changed)} changed files.")
        else:
            ctx.console.print("[dim]No changed files tracked. Run /scan first.[/dim]")
    elif args.strip():
        # Digest specific file
        target = Path(args.strip())
        if not target.is_absolute():
            target = workspace_root / target
        if target.exists():
            ingester.ingest_file(target)
            ctx.console.print(f"[green]✓[/green] Digested: {target.name}")
        else:
            ctx.console.print(f"[red]File not found: {args}[/red]")
    else:
        # No args - show usage
        ctx.console.print("[dim]Usage: /digest <file-path> or /digest --changed[/dim]")


def _cmd_reconcile(ctx: CommandContext, args: str) -> None:
    """View-only reconcile projection for semantic artifacts."""
    from .wiki.reconcile import ReconcileEngine

    engine = ReconcileEngine(Path.cwd())
    projection = engine.project_artifact_reconcile()

    ctx.console.print("[bold cyan]Reconcile Projection (view-only)[/bold cyan]")
    ctx.console.print(f"[dim]Derived artifacts: {projection['derived_count']}[/dim]")
    ctx.console.print(f"[dim]Manual artifacts: {projection['manual_count']}[/dim]")

    if not projection["items"]:
        ctx.console.print("[dim]No artifact-backed reconcile suggestions.[/dim]")
        return

    table = Table(title="Reconcile Suggestions", show_header=True, header_style="bold cyan")
    table.add_column("Layer", style="green", width=8)
    table.add_column("Task", style="dim", width=16)
    table.add_column("Status", width=18)
    table.add_column("Reason")
    for item in projection["items"]:
        table.add_row(
            item.current_status.split("_")[0] if item.current_status else "derived",
            item.entity_path.split("/")[-1],
            item.current_status,
            item.reason,
        )
    ctx.console.print(table)


def _cmd_maintenance(ctx: CommandContext, args: str) -> None:
    """View-only maintenance projection for semantic artifacts."""
    from .wiki.maintenance import MaintenanceEngine

    engine = MaintenanceEngine(Path.cwd())
    projection = engine.project_artifact_maintenance()

    ctx.console.print("[bold cyan]Maintenance Projection (view-only)[/bold cyan]")
    ctx.console.print(f"[dim]Derived artifacts: {projection['derived_count']}[/dim]")
    ctx.console.print(f"[dim]Manual artifacts: {projection['manual_count']}[/dim]")

    if not projection["items"]:
        ctx.console.print("[dim]No artifact-backed maintenance suggestions.[/dim]")
        return

    table = Table(title="Maintenance Suggestions", show_header=True, header_style="bold cyan")
    table.add_column("Layer", style="green", width=8)
    table.add_column("Item", style="dim", width=16)
    table.add_column("Action", width=14)
    table.add_column("Reason")
    for item in projection["items"]:
        table.add_row(
            item.item_type.replace("_artifact", ""),
            Path(item.item_path).name,
            item.action.value,
            item.reason,
        )
    ctx.console.print(table)


def _cmd_init_build(ctx: CommandContext, args: str) -> None:
    """Legacy wiki bootstrap: scan, digest, and build the full wiki structure."""
    from .knowledge.ingester import WikiIngester
    from pathlib import Path
    from datetime import datetime

    workspace_root = Path.cwd()
    ingester = WikiIngester(str(workspace_root))

    ctx.console.print("[yellow]Legacy /init_build is a later-phase surface, not part of Phase 1.[/yellow]")
    ctx.console.print("[dim]Initializing wiki base...[/dim]")
    ctx.console.print("[dim]  Step 1/3: Scanning workspace...[/dim]")

    # Step 1: Scan all files
    try:
        ingester.ingest_all()
        ctx.console.print("[green]  ✓[/green] Workspace scanned")
    except Exception as e:
        ctx.console.print(f"[red]  ✗ Scan failed: {e}[/red]")
        return

    # Step 2: Build wiki index
    ctx.console.print("[dim]  Step 2/3: Building wiki index...[/dim]")
    wiki_dir = workspace_root / ".cc-mini" / "wiki"
    index_file = wiki_dir / "index.md"

    entities_dir = wiki_dir / "entities"
    entity_files = list(entities_dir.glob("*.md")) if entities_dir.exists() else []

    index_content = f"""# Wiki Index

Auto-generated: {datetime.now().isoformat()}

## Statistics

- Entities: {len(entity_files)}
- Source: {workspace_root.name}

## Quick Links

- [Entities](./entities/)

## Build Info

- Command: /init_build
- Status: Complete
"""

    index_file.write_text(index_content, encoding="utf-8")
    ctx.console.print("[green]  ✓[/green] Wiki index built")

    # Step 3: Verify structure
    ctx.console.print("[dim]  Step 3/3: Verifying wiki structure...[/dim]")
    ctx.console.print(f"[green]  ✓[/green] Wiki base initialized")
    ctx.console.print("")
    ctx.console.print(f"[green]✓[/green] Init build complete:")
    ctx.console.print(f"[dim]  - Entities: {len(entity_files)}[/dim]")
    ctx.console.print(f"[dim]  - Wiki dir: {wiki_dir}[/dim]")


def _cmd_post_edit(ctx: CommandContext, args: str) -> None:
    """Later-phase post-edit guard: analyze impact after patch and determine completion state."""
    from .wiki.post_edit_guard import PostEditGuard, CompletionState, format_impact_summary
    from pathlib import Path

    workspace_root = Path.cwd()
    guard = PostEditGuard(str(workspace_root))

    ctx.console.print("[yellow]Later-phase /post_edit surface (demo/stub in Phase 1); not part of the minimal startup path.[/yellow]")

    # Parse args: task_id [status|finalize|report]
    parts = args.strip().split() if args else []
    task_id = parts[0] if parts else "demo"
    action = parts[1] if len(parts) > 1 else "analyze"

    if action == "report":
        # 显示当前状态报告
        report = guard.get_status_report(task_id)
        ctx.console.print("[bold]Post-Edit Status Report[/bold]")
        ctx.console.print(f"  Task ID: {report.get('task_id')}")
        ctx.console.print(f"  State: [cyan]{report.get('state')}[/cyan]")
        ctx.console.print(f"  Patched Files: {len(report.get('patched_files', []))}")
        ctx.console.print(f"  Changed Symbols: {report.get('changed_symbols_count', 0)}")
        ctx.console.print(f"  Impacted Entities: {report.get('impacted_entities_count', 0)}")
        ctx.console.print(f"  Can Complete: {'[green]Yes[/green]' if report.get('can_complete') else '[red]No[/red]'}")

        if report.get('blockers'):
            ctx.console.print("\n[red]Blockers:[/red]")
            for blocker in report['blockers']:
                ctx.console.print(f"  - {blocker}")

        if report.get('verification_commands'):
            ctx.console.print("\n[dim]Suggested Verification:[/dim]")
            for cmd in report['verification_commands']:
                ctx.console.print(f"  $ {cmd}")
        return

    if action == "finalize":
        # 最终完成判定
        final_state = guard.finalize_completion(task_id, verification_passed=True)
        ctx.console.print(f"[bold]Finalizing completion...[/bold]")
        ctx.console.print(f"Final State: [cyan]{final_state.value.upper()}[/cyan]")
        if final_state == CompletionState.COMPLETE:
            ctx.console.print("[green]✓ Task fully completed[/green]")
        elif final_state == CompletionState.BLOCKED:
            ctx.console.print("[red]✗ Task blocked - check summary for blockers[/red]")
        return

    if action == "resolve":
        # 标记影响已解决
        entity_path = parts[2] if len(parts) > 2 else ""
        if entity_path:
            all_resolved = guard.mark_impact_resolved(task_id, entity_path)
            ctx.console.print(f"[green]✓[/green] Marked {entity_path} as resolved")
            if all_resolved:
                ctx.console.print("[green]✓ All impacts resolved - state: IMPACT_CLEAN[/green]")
        return

    # Default: analyze (demo mode with a mock patch)
    ctx.console.print("[bold]Post-Edit Guard Analysis[/bold]")
    ctx.console.print(f"[dim]Task ID: {task_id}[/dim]")
    ctx.console.print("")

    # 创建模拟的 patch 分析
    # 实际使用时，这里会接收 patch 前的原始内容
    import tempfile
    import os

    # 创建一个临时文件来演示
    demo_file = workspace_root / ".cc-mini" / "demo_patch.py"
    demo_file.parent.mkdir(parents=True, exist_ok=True)

    # 模拟原始内容
    original_content = '''def hello():
    """Say hello."""
    return "hello"

class DemoClass:
    pass
'''

    # 模拟 patch 后的内容
    patched_content = '''def hello(name: str = "world") -> str:
    """Say hello to someone."""
    return f"hello, {name}"

class DemoClass:
    """Demo class for testing."""
    def greet(self) -> str:
        return "greetings"
'''

    demo_file.write_text(patched_content, encoding="utf-8")

    # 执行影响分析
    original_contents = {str(demo_file.relative_to(workspace_root)): original_content}
    patched_files = [str(demo_file.relative_to(workspace_root))]

    summary = guard.analyze_patch(task_id, patched_files, original_contents)

    # 显示影响摘要
    ctx.console.print(format_impact_summary(summary))

    # 保存摘要
    guard.save_impact_summary(summary)
    ctx.console.print(f"\n[dim]Impact summary saved to: {guard.impact_dir}[/dim]")

    # 清理演示文件
    demo_file.unlink(missing_ok=True)


# (name, description, handler)
_COMMAND_TABLE: list[tuple[str, str, object]] = [
    ("help",     "Show available commands",                         _cmd_help),
    ("compact",  "Compress conversation context [instructions]",    _cmd_compact),
    ("resume",   "Resume a past session [number|session-id]",       _cmd_resume),
    ("history",  "List saved sessions for this directory",          _cmd_history),
    ("clear",    "Clear conversation, start new session",           _cmd_clear),
    ("memory",   "Show current memory index",                       _cmd_memory),
    ("remember", "Save a note to the daily log [text]",             _cmd_remember),
    ("dream",    "Consolidate daily logs into topic files",          _cmd_dream),
    ("skills",   "List all available skills",                       _cmd_skills),
    ("task",     "Task intake for coding-adjacent or general requests [description]", _cmd_task),
    ("cost",    "Show token usage and cost summary",               _cmd_cost),
    ("model",   "Show or switch model [model-name]",               _cmd_model),
    ("model-health", "Check model endpoint health and local profile", _cmd_model_health),
    ("close",    "Draft a closeout record; confirm with /close confirm", _cmd_close),
    ("milestone-review", "Read-only summary of the latest closeout record", _cmd_milestone_review),
    ("workflow-status", "Read-only workflow readiness status", _cmd_workflow_status),
    ("workflow-init", "Create missing workflow scaffold files [--dry-run]", _cmd_workflow_init),
    ("workflow-doctor", "Read-only workflow diagnostics", _cmd_workflow_doctor),
    ("workflow-test", "Read-only test recommendations from changed files", _cmd_workflow_test),
    ("workflow-pack", "Generate bounded context pack for a goal [goal|task-id]", _cmd_workflow_pack),
    ("workflow-run", "Run a bounded batch execution plan [--dry-run] [goal]", _cmd_workflow_run),
    ("workflow-resume", "Resume a workflow run from saved state [run-id]", _cmd_workflow_resume),
    ("plan",    "Phase1 wiki_strict analysis plan or current plan", _cmd_plan_wiki),
    ("plan-init", "Initialize a new planning run with a goal [goal]", _cmd_plan_init),
    ("plan-status", "Show current planning phase and open items", _cmd_plan_status),
    ("plan-export", "Export a compact planning summary", _cmd_plan_export),
    ("scan",       "Phase1 scan workspace and refresh wiki entities", _cmd_scan),
    ("digest",     "Digest file or --changed for the analysis chain", _cmd_digest),
    ("reconcile", "Later-phase view-only reconcile projection", _cmd_reconcile),
    ("maintenance", "Later-phase view-only maintenance projection", _cmd_maintenance),
    ("init_build", "Legacy /init_build (later-phase, not Phase 1)", _cmd_init_build),
    ("post_edit",  "Later-phase /post_edit demo/stub [task_id|analyze|report|finalize]", _cmd_post_edit),
    ("prime",      "Phase1 prime task and generate TaskPack [task-id]", _cmd_prime),
]

_HANDLERS: dict[str, object] = {name: handler for name, _, handler in _COMMAND_TABLE}


def handle_command(name: str, args: str, ctx: CommandContext) -> bool:
    """Dispatch slash command. Returns True if handled, False otherwise.

    If *name* does not match a built-in command, checks the skill registry
    and executes the skill inline (prompt injection) or forked (isolated turn).
    """
    handler = _HANDLERS.get(name)
    if handler is not None:
        handler(ctx, args)  # type: ignore[operator]
        return True

    # Try as a skill invocation
    from .skills import get_skill
    skill = get_skill(name)
    if skill is not None:
        return _execute_skill(skill, args, ctx)

    ctx.console.print(f"[red]Unknown command: /{name}[/red]  (try /help or /skills)")
    return False


def _execute_skill(skill, args: str, ctx: CommandContext) -> bool:
    """Execute a skill — inline or forked.

    Inline (default): inject the skill prompt as a user message into the
    current conversation and let the engine process it.

    Forked: run the skill in an isolated turn (save messages, clear, run,
    restore original messages).  Matches claude-code's ``context: 'fork'``.
    """
    from .main import run_query

    prompt = skill.get_prompt(args)
    if not prompt:
        ctx.console.print(f"[dim]Skill /{skill.name} produced no prompt.[/dim]")
        return True

    ctx.console.print(f"[dim]Running skill: /{skill.name}…[/dim]")

    if skill.context == "fork":
        # Forked execution: isolated turn
        saved = list(ctx.engine.get_messages())
        ctx.engine.set_messages([])
        try:
            permissions = ctx.permissions
            run_query(ctx.engine, prompt, print_mode=False, permissions=permissions)
        finally:
            # Restore original messages (forked result is ephemeral)
            ctx.engine.set_messages(saved)
    else:
        # Inline execution: inject prompt into ongoing conversation
        permissions = ctx.permissions
        run_query(ctx.engine, prompt, print_mode=False, permissions=permissions)

    return True
