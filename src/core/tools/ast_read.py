from __future__ import annotations
import ast
import re
from pathlib import Path
from typing import Any
from .base import Tool, ToolResult

class ASTReadTool(Tool):
    name = "ASTRead"
    description = (
        "Reads a specific portion of code from a Python file using AST parsing or precise targeting. "
        "Use this instead of regular Read when you only need to inspect a specific component.\n\n"
        "Usage modes (mutually exclusive):\n"
        "1. symbol: Read by class/function name (e.g., 'Engine' or 'Engine.submit')\n"
        "2. span: Read by line range [start, end]\n"
        "3. anchor: Read by anchor text (exact match, returns surrounding context)\n"
        "- If none provided, returns the file's outline (classes and top-level functions)."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute path to the file"},
            "symbol": {"type": "string", "description": "Class or function name (e.g., 'MyClass', 'MyClass.my_method')"},
            "span": {"type": "array", "description": "Line range [start_line, end_line] (1-indexed, inclusive)"},
            "anchor": {"type": "string", "description": "Anchor text to locate (exact match, returns context around it)"},
            "context_lines": {"type": "integer", "description": "Number of context lines around anchor (default: 5)"},
        },
        "required": ["file_path"],
    }

    def is_read_only(self) -> bool:
        return True

    def get_activity_description(self, **kwargs) -> str | None:
        file_path = kwargs.get("file_path", "")
        symbol = kwargs.get("symbol", "")
        span = kwargs.get("span", "")
        anchor = kwargs.get("anchor", "")

        if symbol:
            mode = f"symbol:{symbol}"
        elif span:
            mode = f"span:{span}"
        elif anchor:
            mode = f"anchor"
        else:
            mode = "outline"
        return f"ASTRead {mode} from {Path(file_path).name}" if file_path else None

    def execute(
        self,
        file_path: str,
        symbol: str = "",
        span: list | None = None,
        anchor: str = "",
        context_lines: int = 5,
    ) -> ToolResult:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return ToolResult(content=f"Error: File not found: {file_path}", is_error=True)

        # Phase 4: Support non-Python files for span/anchor mode
        is_python = path.suffix == ".py"

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return ToolResult(content=f"Error reading file: {e}", is_error=True)

        lines = content.splitlines()
        tree = None
        if is_python:
            try:
                tree = ast.parse(content)
            except Exception as e:
                return ToolResult(content=f"Error parsing file: {e}", is_error=True)

        # Priority: anchor > span > symbol > outline
        if anchor:
            return self._read_by_anchor(lines, anchor, context_lines)

        if span:
            return self._read_by_span(lines, span)

        if symbol:
            if not is_python:
                return ToolResult(content="Error: symbol mode only supports .py files. Use anchor or span mode instead.", is_error=True)
            return self._read_by_symbol(lines, tree, symbol)

        # Default: return outline
        if not is_python:
            return ToolResult(content="Error: outline mode only supports .py files. Use anchor or span mode instead.", is_error=True)
        return self._read_outline(tree)

    def _read_by_anchor(self, lines: list[str], anchor: str, context_lines: int) -> ToolResult:
        """Read by anchor text - find exact match and return surrounding context."""
        content = "\n".join(lines)

        # Find the anchor in content
        idx = content.find(anchor)
        if idx == -1:
            return ToolResult(content=f"Error: Anchor text not found", is_error=True)

        # Convert to line number
        lines_before = content[:idx].count("\n")
        target_line = lines_before + 1

        # Calculate context range
        start_line = max(1, target_line - context_lines)
        end_line = min(len(lines), target_line + context_lines)

        # Extract with line numbers
        result_lines = []
        for i in range(start_line - 1, end_line):
            result_lines.append(f"{i + 1}\t{lines[i]}")

        header = f"[ASTRead: anchor found at line {target_line}, showing context {start_line}-{end_line}]\n"
        return ToolResult(content=header + "\n".join(result_lines))

    def _read_by_span(self, lines: list[str], span: list) -> ToolResult:
        """Read by line span [start, end] (1-indexed, inclusive)."""
        if len(span) != 2:
            return ToolResult(content="Error: span must be [start_line, end_line]", is_error=True)

        start_line, end_line = span
        if not isinstance(start_line, int) or not isinstance(end_line, int):
            return ToolResult(content="Error: span values must be integers", is_error=True)

        # Clamp to valid range
        start_line = max(1, min(start_line, len(lines)))
        end_line = max(1, min(end_line, len(lines)))

        if start_line > end_line:
            return ToolResult(content="Error: start_line must be <= end_line", is_error=True)

        # Extract with line numbers
        result_lines = []
        for i in range(start_line - 1, end_line):
            result_lines.append(f"{i + 1}\t{lines[i]}")

        header = f"[ASTRead: span {start_line}-{end_line}]\n"
        return ToolResult(content=header + "\n".join(result_lines))

    def _read_by_symbol(self, lines: list[str], tree: ast.AST, symbol: str) -> ToolResult:
        """Read by symbol name (class/function)."""
        # Parse symbol (support ClassName.method_name)
        target_class = None
        target_method = None
        if "." in symbol:
            target_class, target_method = symbol.split(".", 1)
        else:
            target_class = symbol

        # Traverse tree to find symbol
        for node in ast.walk(tree):
            if (isinstance(node, (ast.ClassDef, ast.FunctionDef))) and node.name == target_class:
                if not target_method:
                    return self._extract_snippet(lines, node)

                # Look for specific method in class
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name == target_method:
                        return self._extract_snippet(lines, child)

        return ToolResult(content=f"Error: Symbol '{symbol}' not found", is_error=True)

    def _read_outline(self, tree: ast.AST) -> ToolResult:
        """Return file outline (classes and top-level functions)."""
        outline = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods = [c.name for c in node.body if isinstance(c, ast.FunctionDef)]
                method_str = f" (methods: {', '.join(methods)})" if methods else ""
                outline.append(f"class {node.name} (Line {node.lineno}){method_str}")
            elif isinstance(node, ast.FunctionDef):
                outline.append(f"def {node.name} (Line {node.lineno})")

        content = "\n".join(outline) if outline else "No classes or functions found."
        return ToolResult(content=f"[ASTRead: file outline]\n{content}")

    def _extract_snippet(self, lines: list[str], node: Any) -> ToolResult:
        """根据 AST 节点的行号提取代码，并加上行号前缀"""
        start = node.lineno - 1
        end = node.end_lineno
        snippet = lines[start:end]
        
        numbered = "".join(f"{start + i + 1}\t{line}\n" for i, line in enumerate(snippet))
        return ToolResult(content=numbered)