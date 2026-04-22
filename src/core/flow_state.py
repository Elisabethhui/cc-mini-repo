from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import RunMode

class FlowState(str, Enum):
    PLAN = "PLAN"           # 强制查阅 Wiki
    LOCATE = "LOCATE"       # 强制提取局部 AST
    IMPLEMENT = "IMPLEMENT" # 强制生成修改 Patch
    VERIFY = "VERIFY"       # 强制运行终端测试

def get_flow_state_prompt() -> str:
    """
    返回用于 wiki_strict 模式的状态机系统指令。
    彻底锁死大模型的行为边界，不允许它发散。
    """
    return """
You are operating in **WIKI_STRICT Flow-State Mode**.
Due to context length constraints, you MUST strictly follow this 4-step state machine for every task.
Do NOT attempt to skip steps or read entire files.

=== THE 4 STATES ===
[STATE 1: PLAN]
- Action: You MUST first use the `Read` tool to read `.cc-mini/wiki/index.md`.
- Purpose: Understand the global architecture without reading raw code.

[STATE 2: LOCATE]
- Action: Based on the wiki, use the `ASTRead` tool to extract ONLY the specific classes or functions you need.
- Purpose: Keep token context extremely small. DO NOT use the normal Read tool for Python files.

[STATE 3: IMPLEMENT]
- Action: Use the `Edit` tool to modify the specific code blocks.
- Constraint: Your `old_string` MUST match exactly. If it fails twice, the human user will be asked to intervene.

[STATE 4: VERIFY]
- Action: Use the `Bash` tool to run tests or linting (e.g., `pytest`, `flake8`).
- Correction: If verification fails, extract the specific error line, return to STATE 2 (LOCATE) for that line, and fix it. Max retries: 3.

**Format Requirement**: 
Always prefix your responses with your current state, like `[STATE: PLAN] I will now read the wiki...`
"""


def get_mode_flow_state_prompt(run_mode: "RunMode | str | None" = None) -> str:
    """Return the mode-specific state assumptions prompt.

    `wiki_strict` gets the locked flow-state instructions; `standard` gets a
    plain, general-purpose prompt so the two modes stay visibly separated.
    """
    mode_value = getattr(run_mode, "value", run_mode)
    if mode_value == "wiki_strict":
        return get_flow_state_prompt()

    return """
You are operating in STANDARD mode.
This mode is the stable, general interaction surface.
Do not assume the wiki_strict state machine, ASTRead-first constraints, or the /scan -> /prime -> /plan lifecycle.
Keep behavior general-purpose and avoid mode-specific wiki assumptions unless the user explicitly enters wiki_strict.
""".strip()
