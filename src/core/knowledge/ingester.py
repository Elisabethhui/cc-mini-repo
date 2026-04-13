from __future__ import annotations
import os
import ast
import re
import hashlib
from pathlib import Path
from enum import Enum
from datetime import datetime
import json


class DigestStatus(str, Enum):
    """Entity 消化状态枚举"""
    RAW_AST = "raw_ast"                          # 仅 AST 提取，未语义消化
    PARTIALLY_DIGESTED = "partially_digested"   # 部分语义消化
    DIGESTED = "digested"                        # 完全消化
    STALE = "stale"                              # 可能过期，需要重新验证
    ERROR = "error"                              # 解析失败，记录漂移


class DriftTracker:
    """
    最小漂移跟踪器 (Phase 2)
    - 跟踪路径不存在或解析失败的次数
    - 超过阈值后停止重试，记录 deferred issue
    """
    MAX_RETRY = 3  # 最大重试次数

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root)
        self.drift_log = self.workspace / ".cc-mini" / "drift_log.json"
        self._failures: dict[str, int] = {}
        self._load()

    def _load(self) -> None:
        """加载历史失败记录"""
        if self.drift_log.exists():
            try:
                self._failures = json.loads(self.drift_log.read_text())
            except Exception:
                self._failures = {}

    def _save(self) -> None:
        """保存失败记录"""
        self.drift_log.parent.mkdir(parents=True, exist_ok=True)
        self.drift_log.write_text(json.dumps(self._failures, indent=2), encoding="utf-8")

    def should_stop(self, path: str | Path) -> tuple[bool, str]:
        """
        检查是否应该停止处理该路径
        返回: (should_stop, reason)
        """
        path_str = str(path)
        count = self._failures.get(path_str, 0)

        if count >= self.MAX_RETRY:
            return True, f"Path '{path_str}' has failed {count} times, stopping to prevent infinite retry"
        return False, ""

    def record_failure(self, path: str | Path, error: str | None = None) -> None:
        """记录一次失败"""
        path_str = str(path)
        self._failures[path_str] = self._failures.get(path_str, 0) + 1
        self._save()

        # 如果达到阈值，写入 deferred issue
        if self._failures[path_str] >= self.MAX_RETRY:
            self._write_deferred_issue(path_str, error)

    def record_success(self, path: str | Path) -> None:
        """记录成功，重置失败计数"""
        path_str = str(path)
        if path_str in self._failures:
            del self._failures[path_str]
            self._save()

    def _write_deferred_issue(self, path_str: str, error: str | None = None) -> None:
        """将问题写入 deferred issue log"""
        deferred_file = self.workspace / ".cc-mini" / "deferred_issues.md"
        timestamp = datetime.now().isoformat()

        lines = [
            f"\n## Deferred Issue at {timestamp}",
            f"",
            f"- **Path**: `{path_str}`",
            f"- **Reason**: Repeated failures (≥{self.MAX_RETRY} attempts)",
        ]
        if error:
            lines.append(f"- **Last Error**: {error}")
        lines.extend([
            f"- **Action**: Manual intervention required",
            f"",
            "---",
            "",
        ])

        if deferred_file.exists():
            existing = deferred_file.read_text(encoding="utf-8")
            content = existing + "\n".join(lines)
        else:
            content = f"# Deferred Issues\n\n" + "\n".join(lines)

        deferred_file.write_text(content, encoding="utf-8")


class WikiIngester:
    """
    大一统知识基座引擎：将代码和文本降维映射为 Markdown 实体图谱。
    支持状态升级：raw_ast → partially_digested → digested | stale
    集成漂移停止：路径不存在或解析失败时停止重试
    """
    def __init__(self, workspace_root: str, drift_tracker: DriftTracker | None = None):
        self.workspace = Path(workspace_root).resolve()
        self.wiki_dir = self.workspace / ".cc-mini" / "wiki"
        self.entities_dir = self.wiki_dir / "entities"

        # 初始化目录
        self.entities_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.wiki_dir / "index.md"

        # 漂移跟踪器 (Phase 2)
        self.drift_tracker = drift_tracker or DriftTracker(workspace_root)

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希用于变更检测"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _parse_entity_frontmatter(self, content: str) -> tuple[dict, str]:
        """解析 entity 文件的 frontmatter，返回 (meta, body)"""
        frontmatter_re = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
        m = frontmatter_re.match(content)
        if not m:
            return {}, content

        raw = m.group(1)
        body = content[m.end():]
        meta: dict = {}

        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            meta[key] = val

        return meta, body

    def _build_frontmatter(self, meta: dict) -> str:
        """从 meta 字典构建 frontmatter 字符串"""
        lines = ["---"]
        for key, val in sorted(meta.items()):
            lines.append(f"{key}: {val}")
        lines.append("---")
        return "\n".join(lines)

    def _update_entity_status(self, entity_file: Path, new_status: DigestStatus, source_hash: str) -> None:
        """更新 entity 文件的状态和元数据"""
        if entity_file.exists():
            old_content = entity_file.read_text(encoding="utf-8")
            meta, body = self._parse_entity_frontmatter(old_content)
            old_status = meta.get("status", DigestStatus.RAW_AST.value)
            # 如果状态已经是 digested，不降级到 raw_ast
            if old_status == DigestStatus.DIGESTED.value and new_status == DigestStatus.RAW_AST:
                new_status = DigestStatus.STALE
        else:
            meta = {}
            body = ""

        meta.update({
            "status": new_status.value,
            "source_hash": source_hash,
            "updated_at": str(Path.cwd().stat().st_mtime),  # 使用简单时间戳
        })

        new_content = self._build_frontmatter(meta) + "\n\n" + body.strip()
        entity_file.write_text(new_content, encoding="utf-8")

    def ingest_all(self):
        """全量扫描工作区，生成实体并重建全局索引"""
        print(f"[Ingester] 正在扫描工作区: {self.workspace}")
        entities_map = {}
        
        for root, dirs, files in os.walk(self.workspace):
            # 过滤掉不需要扫描的目录
            dirs[:] = [d for d in dirs if d not in ('.git', '.cc-mini', '__pycache__', 'node_modules', 'venv')]
            
            for file in files:
                filepath = Path(root) / file
                rel_path = filepath.relative_to(self.workspace)
                
                # 按文件类型路由解析器
                summary = self.ingest_file(filepath)
                if summary:
                    entities_map[str(rel_path)] = summary

        self._build_index(entities_map)
        print(f"[Ingester] Wiki 基座构建完成! 索引位置: {self.index_file}")

    def ingest_file(self, filepath: Path) -> str | None:
        """解析单个文件，生成对应的 entity.md，并返回其摘要"""
        # Phase 2: Drift stop - 检查是否应该停止处理
        should_stop, reason = self.drift_tracker.should_stop(filepath)
        if should_stop:
            print(f"[Drift Stop] {reason}")
            return f"[ERROR] {reason}"

        ext = filepath.suffix.lower()
        rel_path = filepath.relative_to(self.workspace)
        entity_file = self.entities_dir / f"{rel_path.name}.md"

        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception as e:
            # Phase 2: 记录失败并检查是否需要停止
            self.drift_tracker.record_failure(filepath, str(e))
            return None # 忽略二进制或无法读取的文件

        summary = ""
        try:
            # === 插件化解析路由 ===
            if ext == '.py':
                summary = self._parse_python_ast(content, rel_path, entity_file)
            elif ext in ('.md', '.txt'):
                summary = self._parse_markdown(content, rel_path, entity_file)
            elif ext in ('.js', '.ts', '.java'):
                summary = self._parse_with_tree_sitter(content, rel_path, entity_file, ext)

            # Phase 2: 成功则重置失败计数
            if summary:
                self.drift_tracker.record_success(filepath)
        except Exception as e:
            # Phase 2: 解析失败，记录漂移
            self.drift_tracker.record_failure(filepath, str(e))
            summary = f"[ERROR] Parse failed: {e}"

        return summary

    def _parse_python_ast(self, content: str, rel_path: Path, entity_file: Path) -> str | None:
        """原生 Python AST 解析器 (无需 C 依赖，开箱即用)
        包含状态升级：raw_ast -> partially_digested -> digested/stale
        """
        source_hash = self._compute_hash(content)

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return f"[{rel_path}] 存在语法错误"

        classes = []
        functions = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or "无文档说明"
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                classes.append(f"**class {node.name}**: {doc.split(chr(10))[0]}\n  - Methods: {', '.join(methods)}")
            elif isinstance(node, ast.FunctionDef):
                doc = ast.get_docstring(node) or "无文档说明"
                functions.append(f"**def {node.name}()**: {doc.split(chr(10))[0]}")

        if not classes and not functions:
            return None

        # 构建 Entity 内容（不含 frontmatter，frontmatter 由 _update_entity_status 处理）
        entity_body = f"# Entity: {rel_path}\n\n## Classes\n"
        entity_body += "\n".join(f"- {c}" for c in classes) + "\n\n## Functions\n"
        entity_body += "\n".join(f"- {f}" for f in functions)

        # 确定状态：如果有 docstring 认为至少是 partially_digested
        has_docs = any("无文档说明" not in c for c in classes) or any("无文档说明" not in f for f in functions)
        if has_docs and (classes or functions):
            status = DigestStatus.PARTIALLY_DIGESTED
        else:
            status = DigestStatus.RAW_AST

        # 检查是否需要更新（hash 变化或文件不存在）
        need_update = True
        if entity_file.exists():
            old_content = entity_file.read_text(encoding="utf-8")
            old_meta, _ = self._parse_entity_frontmatter(old_content)
            if old_meta.get("source_hash") == source_hash:
                need_update = False

        if need_update:
            entity_file.write_text(entity_body, encoding="utf-8")
            self._update_entity_status(entity_file, status, source_hash)

        return f"包含 {len(classes)} 个类, {len(functions)} 个顶层函数。"

    def _parse_markdown(self, content: str, rel_path: Path, entity_file: Path) -> str | None:
        """Markdown 文本降维：只提取标题骨架，包含状态升级"""
        source_hash = self._compute_hash(content)

        headers = re.findall(r'^(#{1,3})\s+(.*)', content, re.MULTILINE)
        if not headers:
            return None

        entity_body = f"# 文献大纲: {rel_path}\n\n"
        for level, text in headers:
            indent = "  " * (len(level) - 1)
            entity_body += f"{indent}- {text}\n"

        # Markdown 文件默认识别为 partially_digested（有结构信息）
        status = DigestStatus.PARTIALLY_DIGESTED

        # 检查是否需要更新
        need_update = True
        if entity_file.exists():
            old_content = entity_file.read_text(encoding="utf-8")
            old_meta, _ = self._parse_entity_frontmatter(old_content)
            if old_meta.get("source_hash") == source_hash:
                need_update = False

        if need_update:
            entity_file.write_text(entity_body, encoding="utf-8")
            self._update_entity_status(entity_file, status, source_hash)

        return f"包含 {len(headers)} 个章节。"

    def _parse_with_tree_sitter(self, content: str, rel_path: Path, entity_file: Path, ext: str) -> str:
        """
        预留的 Tree-sitter 解析槽位。
        未来只需 pip install tree-sitter，在此处实例化 Parser 即可。
        """
        # TODO: 接入 tree-sitter 逻辑
        return f"[{rel_path}] Tree-sitter 解析器待激活"

    def _build_index(self, entities_map: dict):
        """生成全局 L1 索引 (永远小于 2K Token)"""
        lines = ["# 🗺️ CC-MINI 全局架构知识地图 (The Wiki)", "\n## 核心模块与职责"]
        
        # 按照目录结构分组
        for rel_path, summary in sorted(entities_map.items()):
            lines.append(f"- **`{rel_path}`**: {summary}")
            
        lines.append("\n*注：这是系统的降维视图。当需要修改特定模块时，请调用工具读取 `.cc-mini/wiki/entities/` 下的对应笔记。*")
        self.index_file.write_text("\n".join(lines), encoding="utf-8")