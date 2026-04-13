"""
最小 dehydration + Runtime Snapshot 实现 (Phase 2)
整合 dehydration 和 checkpoint，在 token risk 临界时生成 Runtime Snapshot。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class RuntimeSnapshot:
    """Runtime Snapshot 数据结构 - 包含执行状态关键信息"""
    current_step: str           # 当前步骤
    active_goal: str            # 当前激活的目标
    target_files: list[str]     # 目标文件列表
    primary_symbols: list[str]  # 主要符号（类、函数名）
    last_error: str | None      # 最后错误信息
    next_action: str            # 下一步动作
    token_estimate: int | None  # 当前 token 估计
    budget_state: str | None    # 预算状态
    timestamp: str              # 时间戳


class RuntimeSnapshotWriter:
    """Runtime Snapshot 写入器 - 将执行状态写入 wiki/log.md 或 checkpoint"""

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve()
        self.wiki_dir = self.workspace / ".cc-mini" / "wiki"
        self.log_file = self.wiki_dir / "log.md"
        self.snapshot_dir = self.wiki_dir / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def write_to_wiki_log(self, snapshot: RuntimeSnapshot) -> None:
        """将 snapshot 追加到 wiki/log.md"""
        self.wiki_dir.mkdir(parents=True, exist_ok=True)

        entry = f"\n## Snapshot at {snapshot.timestamp}\n\n"
        entry += f"- **Step**: {snapshot.current_step}\n"
        entry += f"- **Goal**: {snapshot.active_goal}\n"
        entry += f"- **Next Action**: {snapshot.next_action}\n"
        if snapshot.token_estimate:
            entry += f"- **Tokens**: {snapshot.token_estimate} ({snapshot.budget_state})\n"
        if snapshot.last_error:
            entry += f"- **Error**: {snapshot.last_error}\n"
        if snapshot.target_files:
            entry += f"- **Files**: {', '.join(snapshot.target_files[:5])}\n"
        if snapshot.primary_symbols:
            entry += f"- **Symbols**: {', '.join(snapshot.primary_symbols[:5])}\n"
        entry += "\n---\n"

        if self.log_file.exists():
            existing = self.log_file.read_text(encoding="utf-8")
            content = existing + entry
        else:
            content = f"# Wiki Log\n{entry}"

        self.log_file.write_text(content, encoding="utf-8")

    def write_snapshot_file(self, snapshot: RuntimeSnapshot) -> Path:
        """将 snapshot 写入独立的 JSON 文件"""
        timestamp = self._now_iso().replace(":", "-")
        filename = f"snapshot_{timestamp}.json"
        filepath = self.snapshot_dir / filename

        filepath.write_text(
            json.dumps(asdict(snapshot), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return filepath

    def create_and_save(
        self,
        current_step: str,
        active_goal: str,
        target_files: list[str] | None = None,
        primary_symbols: list[str] | None = None,
        last_error: str | None = None,
        next_action: str = "",
        token_estimate: int | None = None,
        budget_state: str | None = None,
        write_to_log: bool = True,
    ) -> Path | None:
        """
        创建并保存 Runtime Snapshot
        返回保存的文件路径，或 None（如果不写入 log）
        """
        snapshot = RuntimeSnapshot(
            current_step=current_step,
            active_goal=active_goal,
            target_files=target_files or [],
            primary_symbols=primary_symbols or [],
            last_error=last_error,
            next_action=next_action,
            token_estimate=token_estimate,
            budget_state=budget_state,
            timestamp=self._now_iso(),
        )

        filepath = self.write_snapshot_file(snapshot)

        if write_to_log:
            self.write_to_wiki_log(snapshot)

        return filepath


class MinimalDehydrator:
    """
    最小 dehydrator - 在 token risk 临界时触发
    整合 dehydration 和 snapshot 写入
    """

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root)
        self.snapshot_writer = RuntimeSnapshotWriter(workspace_root)
        self.dehydration_count: int = 0

    def check_and_dehydrate(
        self,
        messages: list[dict],
        budget_state: str,
        token_estimate: int,
        current_step: str = "",
        active_goal: str = "",
    ) -> dict[str, Any]:
        """
        检查是否需要 dehydration，如果需要则执行并写入 snapshot
        返回操作结果字典
        """
        from ..dehydration import maybe_dehydrate_messages

        result = {
            "dehydrated": False,
            "replaced_count": 0,
            "snapshot_path": None,
        }

        # 只在 warning 及以上状态时触发
        if budget_state in ("warning", "compact", "checkpoint", "hard_stop"):
            # 执行 dehydration
            d_result = maybe_dehydrate_messages(messages)
            self.dehydration_count += d_result.replaced_count

            if d_result.replaced_count > 0:
                result["dehydrated"] = True
                result["replaced_count"] = d_result.replaced_count

                # 写入 Runtime Snapshot
                snapshot_path = self.snapshot_writer.create_and_save(
                    current_step=current_step or "dehydration_triggered",
                    active_goal=active_goal or "token_budget_protection",
                    next_action="/resume-from-checkpoint or /compact",
                    token_estimate=token_estimate,
                    budget_state=budget_state,
                    target_files=[],
                    primary_symbols=[],
                    last_error=None,
                )
                result["snapshot_path"] = str(snapshot_path) if snapshot_path else None

        return result
