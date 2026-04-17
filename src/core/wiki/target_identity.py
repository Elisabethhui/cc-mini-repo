"""
Target Identity 模块 (Phase 6-A / Module 1)
解决 /prime 在路径 target / 同名文件 / 同名 symbol / 多定义场景下的不稳定行为
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
from enum import Enum


class SymbolKind(str, Enum):
    """符号类型"""
    MODULE = "module"           # 模块/文件
    CLASS = "class"             # 类
    FUNCTION = "function"       # 函数
    METHOD = "method"           # 方法
    VARIABLE = "variable"       # 变量
    UNKNOWN = "unknown"         # 未知


class TargetResolutionStatus(str, Enum):
    """目标解析状态"""
    UNIQUE = "unique"           # 唯一确定
    AMBIGUOUS_PATH = "ambiguous_path"      # 路径不明确
    AMBIGUOUS_SYMBOL = "ambiguous_symbol"  # 符号不明确
    NOT_FOUND = "not_found"     # 未找到
    ERROR = "error"             # 错误


@dataclass
class SymbolLocation:
    """符号位置信息"""
    name: str = ""                      # 符号名称
    kind: SymbolKind = SymbolKind.UNKNOWN
    qualname: str = ""                  # 完全限定名 (e.g., "module.Class.method")
    span_start: int = 0                 # 起始行号
    span_end: int = 0                   # 结束行号
    docstring: str = ""                 # 文档字符串摘要

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "qualname": self.qualname,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "docstring": self.docstring[:200] if self.docstring else "",  # 限制长度
        }


@dataclass
class TargetCandidate:
    """目标候选"""
    file_relpath: str = ""              # 文件相对路径
    content_hash: str = ""              # 内容哈希 (SHA-256 前16位)
    symbol: SymbolLocation | None = None  # 符号信息（可选）

    @property
    def canonical_target_key(self) -> str:
        """生成规范目标键"""
        key_parts = [self.file_relpath, self.content_hash[:8]]
        if self.symbol:
            key_parts.extend([self.symbol.qualname or self.symbol.name, self.symbol.kind.value])
        return "::".join(key_parts)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "file_relpath": self.file_relpath,
            "content_hash": self.content_hash,
            "canonical_target_key": self.canonical_target_key,
        }
        if self.symbol:
            result["symbol"] = self.symbol.to_dict()
        return result


@dataclass
class TargetIdentity:
    """
    Target Identity 正式对象
    唯一标识一个代码目标，用于稳定的任务追踪
    """
    # 核心标识
    file_relpath: str = ""              # 文件相对路径 (从 workspace root)
    content_hash: str = ""              # 文件内容哈希 (SHA-256 前16位)

    # 符号信息（可选）
    symbol_qualname: str | None = None  # 完全限定名
    symbol_kind: SymbolKind = SymbolKind.UNKNOWN
    symbol_span: tuple[int, int] | None = None  # (start_line, end_line)

    # 派生标识
    canonical_target_key: str = ""      # 规范目标键 (自动生成)

    # 原始输入（保留用于调试）
    original_input: str = ""            # 用户原始输入
    resolution_method: str = ""         # 解析方法: "path", "symbol", "ambiguous"

    def __post_init__(self):
        """生成规范目标键"""
        if not self.canonical_target_key:
            key_parts = [self.file_relpath, self.content_hash[:8]]
            if self.symbol_qualname:
                key_parts.extend([self.symbol_qualname, self.symbol_kind.value])
            self.canonical_target_key = "::".join(key_parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_relpath": self.file_relpath,
            "content_hash": self.content_hash,
            "symbol_qualname": self.symbol_qualname,
            "symbol_kind": self.symbol_kind.value,
            "symbol_span": self.symbol_span,
            "canonical_target_key": self.canonical_target_key,
            "original_input": self.original_input,
            "resolution_method": self.resolution_method,
        }

    @classmethod
    def from_candidate(cls, candidate: TargetCandidate, original_input: str = "") -> TargetIdentity:
        """从 TargetCandidate 创建 TargetIdentity"""
        return cls(
            file_relpath=candidate.file_relpath,
            content_hash=candidate.content_hash,
            symbol_qualname=candidate.symbol.qualname if candidate.symbol else None,
            symbol_kind=candidate.symbol.kind if candidate.symbol else SymbolKind.UNKNOWN,
            symbol_span=(candidate.symbol.span_start, candidate.symbol.span_end) if candidate.symbol else None,
            original_input=original_input,
            resolution_method="unique",
        )


@dataclass
class TargetResolutionResult:
    """目标解析结果"""
    status: TargetResolutionStatus = TargetResolutionStatus.NOT_FOUND
    candidates: list[TargetCandidate] = field(default_factory=list)
    selected_identity: TargetIdentity | None = None
    disambiguation_prompt: str = ""     # 当 status != UNIQUE 时的提示信息
    error_message: str = ""             # 错误信息

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "candidates": [c.to_dict() for c in self.candidates],
            "selected_identity": self.selected_identity.to_dict() if self.selected_identity else None,
            "disambiguation_prompt": self.disambiguation_prompt,
            "error_message": self.error_message,
        }


class TargetResolver:
    """
    目标解析器
    处理路径 target / 同名文件 / 同名 symbol / 多定义场景的解析
    """

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve()

    def _compute_content_hash(self, filepath: Path) -> str:
        """计算文件内容哈希"""
        try:
            content = filepath.read_bytes()
            return hashlib.sha256(content).hexdigest()[:16]
        except Exception:
            return ""

    EXCLUDED_DIRS = {'.git', '__pycache__', '.venv', 'node_modules', '.worktree'}

    def _is_in_excluded_dir(self, path: Path) -> bool:
        """检查路径是否在排除目录中"""
        path_parts = set(path.parts)
        return not path_parts.isdisjoint(self.EXCLUDED_DIRS)

    def _find_files_by_name(self, name: str) -> list[Path]:
        """根据文件名查找所有匹配的文件"""
        candidates = []
        seen_paths = set()  # 用于去重

        def add_candidate(path: Path) -> None:
            """添加候选，处理去重"""
            resolved = path.resolve()
            if resolved not in seen_paths:
                seen_paths.add(resolved)
                candidates.append(path)

        # 如果已经是相对路径或绝对路径
        direct_path = self.workspace / name
        if direct_path.exists() and direct_path.is_file():
            # 检查是否在排除目录中
            if not self._is_in_excluded_dir(direct_path):
                add_candidate(direct_path)

        # 在 workspace 中递归查找同名文件
        name_path = Path(name)
        file_name = name_path.name

        for found in self.workspace.rglob(file_name):
            if found.is_file():
                # 检查是否在排除目录中
                if self._is_in_excluded_dir(found):
                    continue
                add_candidate(found)

        return candidates

    def _extract_symbols_from_file(self, filepath: Path) -> list[SymbolLocation]:
        """从 Python 文件中提取符号信息"""
        symbols = []

        try:
            import ast
            content = filepath.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node) or ""
                    symbols.append(SymbolLocation(
                        name=node.name,
                        kind=SymbolKind.CLASS,
                        qualname=node.name,
                        span_start=node.lineno,
                        span_end=node.end_lineno or node.lineno,
                        docstring=docstring[:100],
                    ))
                elif isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node) or ""
                    # 判断是否方法需要额外上下文，这里简化处理
                    kind = SymbolKind.METHOD if self._is_method(node, tree) else SymbolKind.FUNCTION
                    symbols.append(SymbolLocation(
                        name=node.name,
                        kind=kind,
                        qualname=node.name,
                        span_start=node.lineno,
                        span_end=node.end_lineno or node.lineno,
                        docstring=docstring[:100],
                    ))
        except Exception:
            pass

        return symbols

    def _is_method(self, node: ast.FunctionDef, tree: ast.Module) -> bool:
        """简单判断是否可能是方法"""
        # 简化判断：如果函数名是 self 开头或在类内部
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                for item in parent.body:
                    if item is node:
                        return True
        return False

    def resolve(self, target_input: str) -> TargetResolutionResult:
        """
        解析目标输入，返回解析结果

        流程：
        1. 路径候选解析
        2. symbol 候选解析
        3. 若唯一，生成 TargetIdentity
        4. 若不唯一，返回 disambiguation list
        """
        result = TargetResolutionResult()
        result.candidates = []

        # 步骤1: 路径候选解析
        file_candidates = self._find_files_by_name(target_input)

        if not file_candidates:
            result.status = TargetResolutionStatus.NOT_FOUND
            result.error_message = f"No file found matching '{target_input}'"
            return result

        # 为每个文件候选创建 TargetCandidate
        for filepath in file_candidates:
            rel_path = str(filepath.relative_to(self.workspace))
            content_hash = self._compute_content_hash(filepath)

            # 提取符号
            symbols = self._extract_symbols_from_file(filepath)

            if symbols:
                # 如果文件中有符号，为每个符号创建一个候选
                for symbol in symbols:
                    candidate = TargetCandidate(
                        file_relpath=rel_path,
                        content_hash=content_hash,
                        symbol=symbol,
                    )
                    result.candidates.append(candidate)
            else:
                # 文件中没有可提取的符号，创建文件级候选
                candidate = TargetCandidate(
                    file_relpath=rel_path,
                    content_hash=content_hash,
                    symbol=None,
                )
                result.candidates.append(candidate)

        # 步骤2 & 3: 判断是否唯一
        if len(result.candidates) == 1:
            # 唯一候选
            result.status = TargetResolutionStatus.UNIQUE
            result.selected_identity = TargetIdentity.from_candidate(
                result.candidates[0],
                original_input=target_input,
            )
            return result

        # 步骤4: 不唯一，需要歧义消解
        # 检查是否路径歧义
        unique_paths = set(c.file_relpath for c in result.candidates)
        if len(unique_paths) > 1:
            result.status = TargetResolutionStatus.AMBIGUOUS_PATH
            result.disambiguation_prompt = self._generate_path_disambiguation_prompt(
                target_input, result.candidates
            )
        else:
            # 同一文件内有多个同名 symbol
            result.status = TargetResolutionStatus.AMBIGUOUS_SYMBOL
            result.disambiguation_prompt = self._generate_symbol_disambiguation_prompt(
                target_input, result.candidates
            )

        return result

    def _generate_path_disambiguation_prompt(self, target_input: str, candidates: list[TargetCandidate]) -> str:
        """生成路径歧义消解提示"""
        lines = [
            f"⚠ Multiple files match '{target_input}':",
            "",
            "Please specify which one:",
        ]

        seen_paths = set()
        for i, candidate in enumerate(candidates, 1):
            if candidate.file_relpath not in seen_paths:
                lines.append(f"  {i}. {candidate.file_relpath}")
                seen_paths.add(candidate.file_relpath)

        lines.append("")
        lines.append("Usage: /prime <task-id> <full-path>")

        return "\n".join(lines)

    def _generate_symbol_disambiguation_prompt(self, target_input: str, candidates: list[TargetCandidate]) -> str:
        """生成符号歧义消解提示"""
        lines = [
            f"⚠ Multiple symbols match '{target_input}' in {candidates[0].file_relpath}:",
            "",
            "Please specify which one:",
        ]

        for i, candidate in enumerate(candidates, 1):
            if candidate.symbol:
                symbol_info = f"{candidate.symbol.kind.value} {candidate.symbol.name}"
                if candidate.symbol.docstring:
                    symbol_info += f" - {candidate.symbol.docstring[:50]}..."
                lines.append(f"  {i}. Line {candidate.symbol.span_start}: {symbol_info}")

        lines.append("")
        lines.append("Usage: /prime <task-id> <file-path>::<symbol-name>")

        return "\n".join(lines)

    def resolve_explicit(self, target_input: str, selected_candidate: TargetCandidate) -> TargetResolutionResult:
        """
        使用用户明确选择的候选进行解析
        """
        result = TargetResolutionResult()
        result.status = TargetResolutionStatus.UNIQUE
        result.selected_identity = TargetIdentity.from_candidate(
            selected_candidate,
            original_input=target_input,
        )
        result.candidates = [selected_candidate]
        return result


class TargetIdentityStore:
    """
    Target Identity 存储管理
    负责 TargetIdentity 的持久化和查询
    """

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve()
        self.identities_dir = self.workspace / ".cc-mini" / "wiki" / "target-identities"
        self.identities_dir.mkdir(parents=True, exist_ok=True)

    def save(self, identity: TargetIdentity, task_id: str) -> Path:
        """保存 TargetIdentity"""
        filename = f"{task_id}_{identity.canonical_target_key.replace('::', '_')[:64]}.json"
        filepath = self.identities_dir / filename

        filepath.write_text(
            json.dumps(identity.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return filepath

    def load(self, task_id: str) -> TargetIdentity | None:
        """加载 TargetIdentity"""
        # 查找匹配 task_id 的文件
        for filepath in self.identities_dir.glob(f"{task_id}_*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                return TargetIdentity(**data)
            except Exception:
                continue
        return None
