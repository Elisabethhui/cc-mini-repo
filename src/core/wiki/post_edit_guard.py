"""
Post Edit Guard + Completion State
Phase 6-A / Module 3: patch 后自动影响分析与完成判定

关键原则：
- patch 成功不等于完成
- 必须分析影响范围
- 必须输出明确的 completion_state
"""

from __future__ import annotations

import json
import ast
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from enum import Enum


class CompletionState(str, Enum):
    """
    完成状态枚举

    状态流转：
    PATCHED -> VERIFYING -> IMPACT_PENDING -> (IMPACT_CLEAN | BLOCKED) -> COMPLETE
    """
    PATCHED = "patched"           # 刚完成 patch，尚未验证
    VERIFYING = "verifying"       # 正在验证中
    IMPACT_PENDING = "impact_pending"  # 影响分析中，有待处理的影响
    IMPACT_CLEAN = "impact_clean"      # 影响已清理
    COMPLETE = "complete"         # 完全完成（patch + 验证 + 影响清理）
    BLOCKED = "blocked"           # 被阻塞（有未解决的 blocker）


@dataclass
class ChangedSymbol:
    """变更的符号信息"""
    name: str = ""                # 符号名称
    symbol_type: str = ""         # 类型: class, function, variable, import
    file_path: str = ""           # 所在文件
    line_start: int = 0           # 起始行号
    line_end: int = 0             # 结束行号
    change_type: str = ""         # 变更类型: added, modified, removed
    old_signature: str = ""       # 原签名（函数/类）
    new_signature: str = ""       # 新签名（函数/类）


@dataclass
class ImpactedEntity:
    """受影响的实体"""
    entity_path: str = ""         # entity 文件路径
    source_path: str = ""         # 源文件路径
    reason: str = ""              # 影响原因
    severity: str = "low"         # 严重程度: low, medium, high
    suggested_action: str = ""    # 建议动作


@dataclass
class ImpactSummary:
    """
    影响分析摘要

    patch 后自动生成，包含：
    - 变更的符号
    - 受影响的文件/entity
    - 需要更新的依赖
    - 建议的验证步骤
    """
    # 基本信息
    task_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 变更信息
    patched_files: list[str] = field(default_factory=list)
    changed_symbols: list[ChangedSymbol] = field(default_factory=list)

    # 影响分析
    impacted_entities: list[ImpactedEntity] = field(default_factory=list)
    impacted_count: int = 0

    # 状态标记
    has_circular_dependency: bool = False
    has_public_api_change: bool = False
    has_test_impact: bool = False

    # 验证建议
    verification_commands: list[str] = field(default_factory=list)
    suggested_tests: list[str] = field(default_factory=list)

    # 最终状态
    completion_state: CompletionState = CompletionState.PATCHED
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "created_at": self.created_at,
            "patched_files": self.patched_files,
            "changed_symbols": [asdict(s) for s in self.changed_symbols],
            "impacted_entities": [asdict(e) for e in self.impacted_entities],
            "impacted_count": len(self.impacted_entities),
            "has_circular_dependency": self.has_circular_dependency,
            "has_public_api_change": self.has_public_api_change,
            "has_test_impact": self.has_test_impact,
            "verification_commands": self.verification_commands,
            "suggested_tests": self.suggested_tests,
            "completion_state": self.completion_state.value,
            "blockers": self.blockers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImpactSummary:
        data = dict(data)
        data["changed_symbols"] = [ChangedSymbol(**s) for s in data.get("changed_symbols", [])]
        data["impacted_entities"] = [ImpactedEntity(**e) for e in data.get("impacted_entities", [])]
        data["completion_state"] = CompletionState(data.get("completion_state", "patched"))
        return cls(**data)

    def is_complete(self) -> bool:
        """检查是否可以标记为 COMPLETE"""
        if self.completion_state == CompletionState.BLOCKED:
            return False
        if self.blockers:
            return False
        if self.impacted_entities and self.completion_state != CompletionState.IMPACT_CLEAN:
            return False
        return self.completion_state in (CompletionState.IMPACT_CLEAN, CompletionState.COMPLETE)


class PostEditGuard:
    """
    Patch 后守卫

    职责：
    1. 分析 patch 造成的变更
    2. 识别受影响的 entities
    3. 生成 ImpactSummary
    4. 判定 CompletionState
    """

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve()
        self.wiki_dir = self.workspace / ".cc-mini" / "wiki"
        self.entities_dir = self.wiki_dir / "entities"
        self.reports_dir = self.wiki_dir / "reports"
        self.impact_dir = self.reports_dir / "impact-summaries"
        self.impact_dir.mkdir(parents=True, exist_ok=True)

    def analyze_patch(
        self,
        task_id: str,
        patched_files: list[str],
        original_contents: dict[str, str],
    ) -> ImpactSummary:
        """
        分析 patch 的影响

        Args:
            task_id: 任务 ID
            patched_files: 被修改的文件列表
            original_contents: 原始文件内容映射 {file_path: content}

        Returns:
            ImpactSummary 影响分析摘要
        """
        summary = ImpactSummary(
            task_id=task_id,
            patched_files=patched_files,
            completion_state=CompletionState.VERIFYING,
        )

        # 1. 提取变更的符号
        for file_path in patched_files:
            changed = self._extract_changed_symbols(file_path, original_contents.get(file_path, ""))
            summary.changed_symbols.extend(changed)

        # 2. 检测公开 API 变更
        summary.has_public_api_change = any(
            s.symbol_type in ("class", "function") and s.change_type == "modified"
            for s in summary.changed_symbols
        )

        # 3. 识别受影响的 entities
        impacted = self._find_impacted_entities(summary.changed_symbols)
        summary.impacted_entities = impacted
        summary.impacted_count = len(impacted)

        # 4. 检测测试影响
        summary.has_test_impact = any(
            "test" in e.entity_path.lower() or "test" in e.source_path.lower()
            for e in impacted
        )

        # 5. 生成验证建议
        summary.verification_commands = self._generate_verification_commands(patched_files)
        summary.suggested_tests = self._suggest_tests(summary.changed_symbols)

        # 6. 判定状态
        if summary.impacted_count > 0:
            summary.completion_state = CompletionState.IMPACT_PENDING
        else:
            summary.completion_state = CompletionState.IMPACT_CLEAN

        return summary

    def _extract_changed_symbols(
        self,
        file_path: str,
        original_content: str,
    ) -> list[ChangedSymbol]:
        """提取文件的变更符号"""
        symbols = []
        current_path = self.workspace / file_path

        if not current_path.exists():
            return symbols

        current_content = current_path.read_text(encoding="utf-8")

        # 尝试 AST 分析（Python 文件）
        if file_path.endswith(".py"):
            try:
                old_tree = ast.parse(original_content) if original_content else None
                new_tree = ast.parse(current_content)

                old_symbols = self._extract_ast_symbols(old_tree) if old_tree else {}
                new_symbols = self._extract_ast_symbols(new_tree)

                # 检测新增、修改、删除
                for name, info in new_symbols.items():
                    if name not in old_symbols:
                        symbols.append(ChangedSymbol(
                            name=name,
                            symbol_type=info["type"],
                            file_path=file_path,
                            line_start=info["line_start"],
                            line_end=info["line_end"],
                            change_type="added",
                        ))
                    elif old_symbols[name] != info:
                        symbols.append(ChangedSymbol(
                            name=name,
                            symbol_type=info["type"],
                            file_path=file_path,
                            line_start=info["line_start"],
                            line_end=info["line_end"],
                            change_type="modified",
                            old_signature=old_symbols[name].get("signature", ""),
                            new_signature=info.get("signature", ""),
                        ))

                for name, info in old_symbols.items():
                    if name not in new_symbols:
                        symbols.append(ChangedSymbol(
                            name=name,
                            symbol_type=info["type"],
                            file_path=file_path,
                            change_type="removed",
                        ))

            except SyntaxError:
                # AST 解析失败，使用简单行数比较
                old_lines = len(original_content.splitlines()) if original_content else 0
                new_lines = len(current_content.splitlines())
                if old_lines != new_lines:
                    symbols.append(ChangedSymbol(
                        name=f"<file_structure>",
                        symbol_type="file",
                        file_path=file_path,
                        change_type="modified",
                    ))

        return symbols

    def _extract_ast_symbols(self, tree: ast.AST) -> dict[str, dict[str, Any]]:
        """从 AST 提取符号信息"""
        symbols = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbols[node.name] = {
                    "type": "class",
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "signature": f"class {node.name}",
                }
            elif isinstance(node, ast.FunctionDef):
                args_str = ", ".join(arg.arg for arg in node.args.args)
                symbols[node.name] = {
                    "type": "function",
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "signature": f"def {node.name}({args_str})",
                }
        return symbols

    def _find_impacted_entities(self, changed_symbols: list[ChangedSymbol]) -> list[ImpactedEntity]:
        """查找受影响的 entities"""
        impacted = []

        if not self.entities_dir.exists():
            return impacted

        changed_names = {s.name for s in changed_symbols}

        for entity_file in self.entities_dir.glob("*.md"):
            content = entity_file.read_text(encoding="utf-8")

            # 检查是否引用了变更的符号
            for symbol in changed_symbols:
                if symbol.name in content:
                    # 解析 frontmatter 获取源文件路径
                    source_path = self._extract_source_path(content)

                    impacted.append(ImpactedEntity(
                        entity_path=str(entity_file.relative_to(self.workspace)),
                        source_path=source_path or "",
                        reason=f"References changed symbol: {symbol.name}",
                        severity="high" if symbol.symbol_type == "class" else "medium",
                        suggested_action="Re-digest to update entity",
                    ))
                    break  # 避免重复添加同一个 entity

        return impacted

    def _extract_source_path(self, entity_content: str) -> str | None:
        """从 entity frontmatter 提取源文件路径"""
        import re
        match = re.search(r'^source:\s*(.+)$', entity_content, re.MULTILINE)
        return match.group(1).strip() if match else None

    def _generate_verification_commands(self, patched_files: list[str]) -> list[str]:
        """生成验证命令建议"""
        commands = []

        # 如果有 Python 文件，建议运行 pytest
        if any(f.endswith(".py") for f in patched_files):
            commands.append("pytest tests/ -v --tb=short")

        # 建议语法检查
        for f in patched_files:
            if f.endswith(".py"):
                commands.append(f"python -m py_compile {f}")

        return commands

    def _suggest_tests(self, changed_symbols: list[ChangedSymbol]) -> list[str]:
        """建议需要运行的测试"""
        tests = []

        for symbol in changed_symbols:
            if symbol.symbol_type == "function":
                tests.append(f"test_{symbol.name}")
            elif symbol.symbol_type == "class":
                tests.append(f"Test{symbol.name}")

        return tests

    def save_impact_summary(self, summary: ImpactSummary) -> Path:
        """保存影响分析摘要"""
        filename = f"{summary.task_id}_impact.json"
        filepath = self.impact_dir / filename

        filepath.write_text(
            json.dumps(summary.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return filepath

    def load_impact_summary(self, task_id: str) -> ImpactSummary | None:
        """加载影响分析摘要"""
        filepath = self.impact_dir / f"{task_id}_impact.json"
        if not filepath.exists():
            return None

        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            return ImpactSummary.from_dict(data)
        except Exception:
            return None

    def mark_impact_resolved(self, task_id: str, entity_path: str) -> bool:
        """
        标记某个影响已解决

        Returns:
            True 如果所有影响都已解决，可以进入 IMPACT_CLEAN
        """
        summary = self.load_impact_summary(task_id)
        if not summary:
            return False

        # 移除已解决的影响
        summary.impacted_entities = [
            e for e in summary.impacted_entities
            if e.entity_path != entity_path
        ]

        # 更新计数
        summary.impacted_count = len(summary.impacted_entities)

        # 如果所有影响都已解决，更新状态
        if summary.impacted_count == 0 and summary.completion_state == CompletionState.IMPACT_PENDING:
            summary.completion_state = CompletionState.IMPACT_CLEAN

        self.save_impact_summary(summary)
        return summary.impacted_count == 0

    def finalize_completion(self, task_id: str, verification_passed: bool = True) -> CompletionState:
        """
        最终完成判定

        Args:
            task_id: 任务 ID
            verification_passed: 验证是否通过

        Returns:
            最终的 CompletionState
        """
        summary = self.load_impact_summary(task_id)
        if not summary:
            return CompletionState.BLOCKED

        if not verification_passed:
            summary.completion_state = CompletionState.BLOCKED
            summary.blockers.append("Verification failed")
            self.save_impact_summary(summary)
            return CompletionState.BLOCKED

        if summary.blockers:
            summary.completion_state = CompletionState.BLOCKED
            self.save_impact_summary(summary)
            return CompletionState.BLOCKED

        if summary.impacted_entities:
            summary.completion_state = CompletionState.IMPACT_PENDING
            self.save_impact_summary(summary)
            return CompletionState.IMPACT_PENDING

        summary.completion_state = CompletionState.COMPLETE
        self.save_impact_summary(summary)
        return CompletionState.COMPLETE

    def get_status_report(self, task_id: str) -> dict[str, Any]:
        """获取状态报告"""
        summary = self.load_impact_summary(task_id)
        if not summary:
            return {
                "task_id": task_id,
                "state": "unknown",
                "message": "No impact summary found for this task",
            }

        return {
            "task_id": task_id,
            "state": summary.completion_state.value,
            "patched_files": summary.patched_files,
            "changed_symbols_count": len(summary.changed_symbols),
            "impacted_entities_count": summary.impacted_count,
            "has_public_api_change": summary.has_public_api_change,
            "has_test_impact": summary.has_test_impact,
            "blockers": summary.blockers,
            "can_complete": summary.is_complete(),
            "verification_commands": summary.verification_commands,
        }


def format_impact_summary(summary: ImpactSummary) -> str:
    """格式化影响摘要供显示"""
    lines = [
        "=" * 50,
        "POST-EDIT IMPACT ANALYSIS",
        "=" * 50,
        f"Task ID: {summary.task_id}",
        f"State: {summary.completion_state.value.upper()}",
        "",
        f"Changed Files: {len(summary.patched_files)}",
    ]

    if summary.changed_symbols:
        lines.append("\nChanged Symbols:")
        for sym in summary.changed_symbols:
            lines.append(f"  - {sym.name} ({sym.symbol_type}): {sym.change_type}")

    if summary.impacted_entities:
        lines.append(f"\nImpacted Entities: {summary.impacted_count}")
        for ent in summary.impacted_entities:
            lines.append(f"  - {ent.entity_path}")
            lines.append(f"    Severity: {ent.severity}")
            lines.append(f"    Action: {ent.suggested_action}")
    else:
        lines.append("\nImpacted Entities: None")

    if summary.verification_commands:
        lines.append("\nSuggested Verification:")
        for cmd in summary.verification_commands:
            lines.append(f"  $ {cmd}")

    if summary.blockers:
        lines.append("\nBlockers:")
        for blocker in summary.blockers:
            lines.append(f"  ⚠️  {blocker}")

    lines.append("")
    lines.append("=" * 50)

    return "\n".join(lines)
