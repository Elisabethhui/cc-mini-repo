from __future__ import annotations
import ast
from pathlib import Path
from typing import Any
from .base import Tool, ToolResult

class ASTReadTool(Tool):
    name = "ASTRead"
    description = (
        "Reads a specific class or function from a Python file using AST parsing. "
        "Use this instead of regular Read when you only need to inspect a specific component.\n\n"
        "Usage:\n"
        "- symbol: The name of the class or function (e.g., 'Engine' or 'Engine.submit').\n"
        "- If symbol is omitted, it returns the file's outline (classes and top-level functions)."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute path to the file"},
            "symbol": {"type": "string", "description": "Class or function name (e.g., 'MyClass', 'MyClass.my_method')"},
        },
        "required": ["file_path"],
    }

    def is_read_only(self) -> bool:
        return True

    def get_activity_description(self, **kwargs) -> str | None:
        file_path = kwargs.get("file_path", "")
        symbol = kwargs.get("symbol", "outline")
        return f"Parsing {symbol} from {Path(file_path).name}" if file_path else None

    def execute(self, file_path: str, symbol: str = "") -> ToolResult:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return ToolResult(content=f"Error: File not found: {file_path}", is_error=True)
            
        if path.suffix != ".py":
            return ToolResult(content="Error: ASTRead currently only supports .py files. Use Read tool instead.", is_error=True)

        try:
            content = path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except Exception as e:
            return ToolResult(content=f"Error parsing file: {e}", is_error=True)

        lines = content.splitlines()

        # 如果没有提供 symbol，返回文件大纲
        if not symbol:
            outline = []
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    outline.append(f"class {node.name} (Line {node.lineno})")
                elif isinstance(node, ast.FunctionDef):
                    outline.append(f"def {node.name} (Line {node.lineno})")
            return ToolResult(content="\n".join(outline) if outline else "No classes or functions found.")

        # 解析 symbol (支持 ClassName.method_name)
        target_class = None
        target_method = None
        if "." in symbol:
            target_class, target_method = symbol.split(".", 1)
        else:
            target_class = symbol

        # 遍历提取代码块
        for node in ast.walk(tree):
            # 匹配独立函数或类
            if (isinstance(node, ast.ClassDef) or isinstance(node, ast.FunctionDef)) and node.name == target_class:
                if not target_method:
                    return self._extract_snippet(lines, node)
                
                # 如果需要类中的特定方法
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name == target_method:
                        return self._extract_snippet(lines, child)
                        
        return ToolResult(content=f"Error: Symbol '{symbol}' not found in {path.name}", is_error=True)

    def _extract_snippet(self, lines: list[str], node: Any) -> ToolResult:
        """根据 AST 节点的行号提取代码，并加上行号前缀"""
        start = node.lineno - 1
        end = node.end_lineno
        snippet = lines[start:end]
        
        numbered = "".join(f"{start + i + 1}\t{line}\n" for i, line in enumerate(snippet))
        return ToolResult(content=numbered)