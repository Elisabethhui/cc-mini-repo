from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEHYDRATABLE_TOOLS = {"Read", "Grep", "Bash"}


@dataclass
class DehydrationResult:
    replaced_count: int
    skipped_count: int


def maybe_dehydrate_messages(messages: list[dict[str, Any]]) -> DehydrationResult:
    """
    对历史消息做原地脱水。
    策略：
    - 只处理较早的 tool_result
    - 跳过最近 2 条消息，避免影响当前推理
    """
    if len(messages) <= 2:
        return DehydrationResult(replaced_count=0, skipped_count=0)

    replaced = 0
    skipped = 0
    candidate_slice = messages[:-2]

    for msg in candidate_slice:
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue

        new_blocks: list[Any] = []
        changed = False

        for block in content:
            if not isinstance(block, dict):
                new_blocks.append(block)
                continue

            if block.get("type") != "tool_result":
                new_blocks.append(block)
                continue

            if block.get("is_error"):
                new_blocks.append(block)
                skipped += 1
                continue

            dehydrated = _dehydrate_tool_result_block(block)
            if dehydrated is None:
                new_blocks.append(block)
                skipped += 1
                continue

            new_blocks.append(dehydrated)
            changed = True
            replaced += 1

        if changed:
            msg["content"] = new_blocks

    return DehydrationResult(replaced_count=replaced, skipped_count=skipped)


def _dehydrate_tool_result_block(block: dict[str, Any]) -> dict[str, Any] | None:
    """
    这里无法总是拿到 tool name，所以尽量从 content 里提炼。
    如果内容已经很短，就不脱水。
    """
    content = block.get("content", "")
    if isinstance(content, list):
        joined = "\n".join(str(x) for x in content)
    else:
        joined = str(content)

    if len(joined) < 1200:
        return None

    summary = _cheap_summary(joined)

    return {
        "type": "tool_result",
        "tool_use_id": block.get("tool_use_id"),
        "content": f"[tool_result dehydrated]\n{summary}",
        "is_error": False,
    }


def _cheap_summary(text: str, limit: int = 500) -> str:
    """
    低成本摘要，不再调模型。
    先保留头尾+长度信息。
    """
    text = text.strip()
    if len(text) <= limit:
        return text

    head = text[:250].rstrip()
    tail = text[-180:].lstrip()
    return (
        f"original_length={len(text)} chars\n"
        f"head:\n{head}\n\n"
        f"... [dehydrated] ...\n\n"
        f"tail:\n{tail}"
    )