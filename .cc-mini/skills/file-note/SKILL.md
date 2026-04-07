---
name: file-note
description: 32K-safe file note that reads one file with strict limits and produces one markdown note
context: fork
allowed-tools: Bash, Read, Glob, Grep, Write
arguments: <repo-relative file path>
---

# File Note (32K Safe)

You are producing a note for exactly one source file.

## Goal
Read one target file and create one structured Markdown note.

## Arguments
`$ARGUMENTS` must be a repository-relative file path.

## Context safety rules
- Read only the target file.
- You may read at most 1 directly related supporting file if absolutely necessary.
- If the target file is large, read at most 3 sections.
- Each section should be as small as possible.
- Stop as soon as enough evidence exists to write the note.
- Do not perform project-level reasoning here.

## Required tasks
1. Read `./code-reading-notes/manifest.json` if it exists.
2. Resolve the target file using the helper script.
3. Read the target file carefully under the limits above.
4. Produce one markdown note under:
   `./code-reading-notes/10_file_notes/<AUTO_NUMBER>_<SAFE_FILENAME>.md`
5. Update manifest/progress/TODO through scripts or minimal edits only.

## Required output structure
# <file path> 代码笔记
## 1. 文件定位
## 2. 文件职责
## 3. 核心内容
## 4. 执行逻辑
## 5. 对外关系
## 6. 学习要点
## 7. 面试可讲点
## 8. 待确认点

## Stop condition
Stop after one file note is written.
Do not continue to another file.
