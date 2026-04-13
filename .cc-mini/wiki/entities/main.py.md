---
source_hash: 4667dacd032be6fe
status: partially_digested
updated_at: 1776054844.6630266
---

# Entity: src/core/main.py

## Classes
- **class _SlashCommandCompleter**: Autocomplete for slash commands. Triggers when input starts with "/".
  - Methods: _all_commands, get_completions
- **class _StreamingMarkdown**: Accumulates streamed text and renders markdown incrementally.
  - Methods: __init__, feed, _render, flush
- **class _SpinnerManager**: Manages a Rich Live spinner that shows while waiting for API/tool responses.
  - Methods: __init__, start, update, stop

## Functions
- **def _bordered_prompt()**: Prompt with bordered input box that adapts to content height.
- **def _tool_preview()**: 无文档说明
- **def _collapsed_tool_summary()**: Summarize tools by type, matching TS CollapsedReadSearchContent.
- **def _parse_input()**: Parse user input, extracting @path image references into content blocks.
- **def run_query()**: Run a single turn. Ctrl+C or Esc cancels the active turn.
- **def _run_dream()**: Run dream consolidation: snapshot messages, submit dream prompt, restore.
- **def main()**: 无文档说明
- **def _handle_sandbox_command()**: Handle /sandbox REPL command.
- **def _show_sandbox_status()**: Display sandbox status. Corresponds to SandboxConfigTab + SandboxDependenciesTab.
- **def _interactive_sandbox_setup()**: Interactive three-way mode selection. Corresponds to SandboxModeTab Select.