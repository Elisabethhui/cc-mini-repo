from __future__ import annotations
import os
import shutil
import difflib
from pathlib import Path
from typing import Dict
from rich.console import Console
from rich.prompt import Confirm
from .base import Tool, ToolResult

console = Console()

class FileEditTool(Tool):
    name = "Edit"
    description = (
        "Performs EXACT string replacements in files.\n\n"
        "Usage:\n"
        "- Provide `old_string` exactly as it appears in the file (including all whitespace and indentation).\n"
        "- If your edit fails because of indentation or whitespace mismatch, the system will ask the human User to verify your intent.\n"
        "- Do NOT use this tool to write entire new files.\n"
    )
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute path to file"},
            "old_string": {"type": "string", "description": "Exact string to replace (Search Block)"},
            "new_string": {"type": "string", "description": "Replacement string (Replace Block)"},
            "replace_all": {"type": "boolean", "description": "Replace all occurrences", "default": False},
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    def __init__(self):
        super().__init__()
        # 记录每个文件的编辑失败次数
        self._fail_counts: Dict[str, int] = {}

    def get_activity_description(self, **kwargs) -> str | None:
        file_path = kwargs.get("file_path", "")
        return f"Safely Editing {Path(file_path).name}" if file_path else None

    def _backup_file(self, path: Path):
        """修改前自动备份文件"""
        backup_dir = path.parent / ".cc-mini" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{path.name}.bak"
        shutil.copy2(path, backup_path)

    def execute(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> ToolResult:
        path = Path(file_path)
        if not path.exists():
            return ToolResult(content=f"Error: File not found: {file_path}", is_error=True)
            
        content = path.read_text(encoding="utf-8")
        count = content.count(old_string)
        
        # 失败处理逻辑：严格匹配失败
        if count == 0:
            fails = self._fail_counts.get(file_path, 0) + 1
            self._fail_counts[file_path] = fails
            
            # 连续失败 2 次，触发人工兜底 (Ask User)
            if fails >= 2:
                console.print(f"\n[bold yellow]⚠️ Agent 尝试修改 {path.name} 失败 (严格匹配未命中)。[/bold yellow]")
                console.print("[dim]由于启用了 Wiki Strict 模式，已拦截此操作以防损坏代码库。[/dim]")
                console.print(f"\n[cyan]Agent 试图将以下内容：[/cyan]\n{old_string}")
                console.print(f"\n[green]替换为：[/green]\n{new_string}\n")
                
                # 模糊匹配辅助用户判断
                sim = difflib.SequenceMatcher(None, content, old_string).ratio()
                if sim > 0.6:
                    console.print(f"[dim]系统在文件中找到了相似度为 {sim:.1%} 的代码块。[/dim]")

                # 挂起流，等待人类指令
                apply_force = Confirm.ask("[bold red]是否由您强行批准并由系统尝试模糊替换？[/bold red]")
                if apply_force:
                    # TODO: 这里可以接入更高级的模糊替换算法，此处演示强行接管
                    self._fail_counts[file_path] = 0 # 重置计数
                    return ToolResult(content="User intervened. Please rewrite the code using standard python string replace with exact lines.")
                else:
                    return ToolResult(content="Error: Human user rejected the patch. You must rethink your approach or verify the AST.", is_error=True)
            else:
                return ToolResult(content=f"Error: Exact old_string not found. Check your indentation and try again. (Attempt {fails}/2)", is_error=True)

        if count > 1 and not replace_all:
            return ToolResult(content=f"Error: old_string found {count} times. Use replace_all=true or add context.", is_error=True)

        # 执行替换
        self._backup_file(path)
        new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
        path.write_text(new_content, encoding="utf-8")
        
        # 成功后重置计数
        self._fail_counts[file_path] = 0
        replaced = count if replace_all else 1
        return ToolResult(content=f"Successfully replaced {replaced} occurrence(s) in {file_path}. Backup saved.")