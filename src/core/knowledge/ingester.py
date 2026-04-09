from __future__ import annotations
import os
import ast
import re
from pathlib import Path

class WikiIngester:
    """
    大一统知识基座引擎：将代码和文本降维映射为 Markdown 实体图谱。
    """
    def __init__(self, workspace_root: str):
        self.workspace = Path(workspace_root).resolve()
        self.wiki_dir = self.workspace / ".cc-mini" / "wiki"
        self.entities_dir = self.wiki_dir / "entities"
        
        # 初始化目录
        self.entities_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.wiki_dir / "index.md"

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
        ext = filepath.suffix.lower()
        rel_path = filepath.relative_to(self.workspace)
        entity_file = self.entities_dir / f"{rel_path.name}.md"

        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            return None # 忽略二进制或无法读取的文件

        summary = ""
        # === 插件化解析路由 ===
        if ext == '.py':
            summary = self._parse_python_ast(content, rel_path, entity_file)
        elif ext in ('.md', '.txt'):
            summary = self._parse_markdown(content, rel_path, entity_file)
        elif ext in ('.js', '.ts', '.java'):
            summary = self._parse_with_tree_sitter(content, rel_path, entity_file, ext)
        
        return summary

    def _parse_python_ast(self, content: str, rel_path: Path, entity_file: Path) -> str:
        """原生 Python AST 解析器 (无需 C 依赖，开箱即用)"""
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

        # 写入独立的 Entity 笔记
        entity_content = f"# Entity: {rel_path}\n\n## Classes\n"
        entity_content += "\n".join(f"- {c}" for c in classes) + "\n\n## Functions\n"
        entity_content += "\n".join(f"- {f}" for f in functions)
        entity_file.write_text(entity_content, encoding="utf-8")

        return f"包含 {len(classes)} 个类, {len(functions)} 个顶层函数。"

    def _parse_markdown(self, content: str, rel_path: Path, entity_file: Path) -> str:
        """Markdown 文本降维：只提取标题骨架"""
        headers = re.findall(r'^(#{1,3})\s+(.*)', content, re.MULTILINE)
        if not headers:
            return None
            
        entity_content = f"# 文献大纲: {rel_path}\n\n"
        for level, text in headers:
            indent = "  " * (len(level) - 1)
            entity_content += f"{indent}- {text}\n"
            
        entity_file.write_text(entity_content, encoding="utf-8")
        return f"包含 {len(headers)} 个章节章节。"

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