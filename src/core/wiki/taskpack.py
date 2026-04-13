"""
TaskPack / EditSpec / Goal Stack 正式对象定义 (Phase 3)
符合 memory-bank/schema/taskpack_policy.md 规则
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from enum import Enum


class TaskStatus(str, Enum):
    """TaskPack 状态枚举"""
    PENDING = "pending"           # 待处理
    PRIMED = "primed"             # 已预热（TaskPack 已生成）
    PLANNED = "planned"           # 已规划（EditSpec 已生成）
    IN_PROGRESS = "in_progress"   # 执行中
    COMPLETED = "completed"       # 已完成
    DEFERRED = "deferred"         # 已延后
    FAILED = "failed"             # 失败


class EntityStatus(str, Enum):
    """关联 Entity 的状态"""
    RAW_AST = "raw_ast"
    PARTIALLY_DIGESTED = "partially_digested"
    DIGESTED = "digested"
    STALE = "stale"
    ERROR = "error"


@dataclass
class GoalStack:
    """
    Goal Stack 正式对象
    四层目标锚点 + 当前动作 + 完成定义 + 越界声明
    """
    global_goal: str = ""           # 全局目标（当前 session 的总目标）
    step_goal: str = ""             # 当前步骤目标（由 coordinator 或 plan 设定）
    task_goal: str = ""             # 当前任务目标（当前正在执行的子任务）
    current_action: str = ""        # 正在执行的具体动作
    done_definition: str = ""       # 完成定义（什么样的状态算完成）
    out_of_scope: str = ""          # 明确不在当前步骤范围内的事项

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> GoalStack:
        return cls(**data)

    def validate(self) -> tuple[bool, str]:
        """验证 Goal Stack 是否完整"""
        if not self.global_goal:
            return False, "global_goal is required"
        if not self.task_goal:
            return False, "task_goal is required"
        if not self.done_definition:
            return False, "done_definition is required"
        return True, ""


@dataclass
class EditSpec:
    """
    EditSpec 正式对象
    结构化修改意图与边界
    """
    target_file: str = ""           # 目标文件路径
    target_symbol: str = ""         # 目标符号（类名/函数名）
    target_span: tuple[int, int] | None = None  # 目标行号范围 (start, end)
    anchor_text: str = ""           # 定位锚文本（用于匹配）
    operation: str = ""             # 操作类型: create, update, delete, move
    description: str = ""           # 修改描述
    old_string: str = ""            # 原字符串（用于 Edit 匹配）
    new_string: str = ""            # 新字符串（用于替换）
    constraints: list[str] = field(default_factory=list)  # 约束条件
    verification: list[str] = field(default_factory=list)  # 验证命令

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EditSpec:
        return cls(**data)

    def is_valid(self) -> tuple[bool, str]:
        """验证 EditSpec 是否足够具体"""
        if not self.target_file:
            return False, "target_file is required"
        if not self.operation:
            return False, "operation is required"
        if not self.description:
            return False, "description is required"
        if self.operation == "update" and not self.old_string:
            return False, "old_string is required for update operation"
        return True, ""


@dataclass
class TaskPack:
    """
    TaskPack 正式对象
    当前任务相关的最小知识压缩包
    """
    # 标识
    task_id: str = ""               # 唯一标识符
    title: str = ""                 # 任务标题
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 核心内容
    summary: str = ""               # 任务摘要
    goal_stack: GoalStack = field(default_factory=GoalStack)

    # 目标定位
    target_files: list[str] = field(default_factory=list)      # 目标文件列表
    primary_symbols: list[str] = field(default_factory=list)   # 主要符号
    related_symbols: list[str] = field(default_factory=list)   # 相关符号

    # 知识来源
    digest_pages: list[str] = field(default_factory=list)      # 关联的 digest 页面

    # 风险与控制
    hotspots: list[str] = field(default_factory=list)          # 热点/风险点
    constraints: list[str] = field(default_factory=list)       # 约束条件
    verification_steps: list[str] = field(default_factory=list)  # 验证建议

    # 编辑规范
    edit_specs: list[EditSpec] = field(default_factory=list)   # EditSpec 列表

    # 状态检查
    entity_status: dict[str, EntityStatus] = field(default_factory=dict)  # 关联 entity 状态

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        data = asdict(self)
        # 处理枚举类型
        data['status'] = self.status.value
        data['goal_stack'] = self.goal_stack.to_dict()
        data['edit_specs'] = [es.to_dict() for es in self.edit_specs]
        data['entity_status'] = {k: v.value for k, v in self.entity_status.items()}
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskPack:
        """从字典反序列化"""
        data = dict(data)  # 复制
        data['status'] = TaskStatus(data.get('status', 'pending'))
        data['goal_stack'] = GoalStack.from_dict(data.get('goal_stack', {}))
        data['edit_specs'] = [EditSpec.from_dict(es) for es in data.get('edit_specs', [])]
        entity_status = data.get('entity_status', {})
        data['entity_status'] = {k: EntityStatus(v) for k, v in entity_status.items()}
        return cls(**data)

    def compute_hash(self) -> str:
        """计算任务哈希"""
        content = f"{self.task_id}:{self.title}:{self.summary}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_ready_for_plan(self) -> tuple[bool, str]:
        """检查是否准备好进入 plan 阶段"""
        valid, msg = self.goal_stack.validate()
        if not valid:
            return False, f"Goal Stack invalid: {msg}"
        if not self.target_files:
            return False, "No target files specified"
        if not self.primary_symbols:
            return False, "No primary symbols specified"
        return True, ""

    def is_ready_for_patch(self) -> tuple[bool, str]:
        """检查是否准备好进入 patch 阶段"""
        ready, msg = self.is_ready_for_plan()
        if not ready:
            return False, msg
        if not self.edit_specs:
            return False, "No EditSpecs defined"
        for i, es in enumerate(self.edit_specs):
            valid, msg = es.is_valid()
            if not valid:
                return False, f"EditSpec[{i}] invalid: {msg}"
        return True, ""


@dataclass
class DeferredIssue:
    """
    Deferred Issue Log 条目
    记录延后处理的问题
    """
    issue_id: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    path: str = ""                  # 问题路径/文件
    reason: str = ""                # 延后原因
    error: str | None = None        # 错误信息
    retry_count: int = 0            # 重试次数
    suggested_action: str = ""      # 建议的后续动作
    status: str = "open"            # open, resolved, wontfix

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MicroForkNote:
    """
    Micro-Fork Note
    轻量分叉记录
    """
    fork_id: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parent_task_id: str = ""        # 父任务 ID
    branch_reason: str = ""         # 分叉原因
    original_goal: str = ""         # 原始目标
    forked_goal: str = ""           # 分叉后目标
    resolved: bool = False          # 是否已解决
    resolution: str = ""            # 解决方案

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TaskPackManager:
    """
    TaskPack 管理器
    负责 TaskPack 的持久化、加载和管理
    """

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve()
        self.taskpacks_dir = self.workspace / ".cc-mini" / "wiki" / "taskpacks"
        self.taskpacks_dir.mkdir(parents=True, exist_ok=True)

        self.reports_dir = self.workspace / ".cc-mini" / "wiki" / "reports"
        self.deferred_dir = self.reports_dir / "deferred-issues"
        self.forks_dir = self.reports_dir / "micro-forks"
        self.deferred_dir.mkdir(parents=True, exist_ok=True)
        self.forks_dir.mkdir(parents=True, exist_ok=True)

    def save_taskpack(self, taskpack: TaskPack) -> Path:
        """保存 TaskPack 到磁盘"""
        taskpack.updated_at = datetime.now(timezone.utc).isoformat()
        filename = f"{taskpack.task_id or 'taskpack'}.json"
        filepath = self.taskpacks_dir / filename

        filepath.write_text(
            json.dumps(taskpack.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return filepath

    def load_taskpack(self, task_id: str) -> TaskPack | None:
        """从磁盘加载 TaskPack"""
        filepath = self.taskpacks_dir / f"{task_id}.json"
        if not filepath.exists():
            return None
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            return TaskPack.from_dict(data)
        except Exception:
            return None

    def list_taskpacks(self) -> list[str]:
        """列出所有 TaskPack ID"""
        return [f.stem for f in self.taskpacks_dir.glob("*.json")]

    def save_deferred_issue(self, issue: DeferredIssue) -> Path:
        """保存 Deferred Issue"""
        filename = f"{issue.issue_id}.json"
        filepath = self.deferred_dir / filename

        filepath.write_text(
            json.dumps(issue.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return filepath

    def load_deferred_issues(self, status: str | None = None) -> list[DeferredIssue]:
        """加载 Deferred Issues"""
        issues = []
        for f in self.deferred_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                issue = DeferredIssue(**data)
                if status is None or issue.status == status:
                    issues.append(issue)
            except Exception:
                continue
        return issues

    def save_micro_fork(self, fork: MicroForkNote) -> Path:
        """保存 Micro-Fork Note"""
        filename = f"{fork.fork_id}.json"
        filepath = self.forks_dir / filename

        filepath.write_text(
            json.dumps(fork.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return filepath

    def load_micro_forks(self, parent_task_id: str | None = None) -> list[MicroForkNote]:
        """加载 Micro-Fork Notes"""
        forks = []
        for f in self.forks_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                fork = MicroForkNote(**data)
                if parent_task_id is None or fork.parent_task_id == parent_task_id:
                    forks.append(fork)
            except Exception:
                continue
        return forks

    def generate_taskpack_from_digest(
        self,
        task_id: str,
        title: str,
        target_files: list[str],
        digest_dir: Path | None = None,
    ) -> TaskPack:
        """
        从 digest 生成 TaskPack（/prime 的核心逻辑）
        """
        if digest_dir is None:
            digest_dir = self.workspace / ".cc-mini" / "wiki" / "entities"

        taskpack = TaskPack(
            task_id=task_id,
            title=title,
            status=TaskStatus.PRIMED,
            target_files=target_files,
        )

        # 检查关联 entity 状态
        for fpath in target_files:
            entity_file = digest_dir / f"{Path(fpath).name}.md"
            if entity_file.exists():
                content = entity_file.read_text(encoding="utf-8")
                # 解析 frontmatter 获取状态
                import re
                status_match = re.search(r'^status:\s*(\w+)', content, re.MULTILINE)
                if status_match:
                    status_str = status_match.group(1)
                    try:
                        taskpack.entity_status[fpath] = EntityStatus(status_str)
                    except ValueError:
                        taskpack.entity_status[fpath] = EntityStatus.RAW_AST

                # 提取 primary symbols
                symbol_matches = re.findall(r'\*\*(class|def)\s+(\w+)', content)
                for _, name in symbol_matches:
                    if name not in taskpack.primary_symbols:
                        taskpack.primary_symbols.append(name)

                taskpack.digest_pages.append(str(entity_file.relative_to(self.workspace)))

        # 自动设置默认 Goal Stack
        taskpack.goal_stack = GoalStack(
            global_goal=f"Implement changes for {title}",
            step_goal="Analyze and plan modifications",
            task_goal=f"Prime task {task_id}",
            current_action="Generating TaskPack from digest",
            done_definition=f"TaskPack created with target files: {target_files}",
            out_of_scope="Actual implementation (patch phase)",
        )

        return taskpack
