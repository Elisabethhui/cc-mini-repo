---
name: module-note
description: 32K-safe module summary that prefers existing file notes and avoids raw source rereads
context: fork
allowed-tools: Bash, Read, Glob, Grep, Write
arguments: [module name from module_candidates.json or manifest.json]
---

# Module Note (32K Safe)

You are producing one module-level summary.

## Goal
Summarize one module by aggregating file notes, not by rereading the source tree.

## Context safety rules
- Prefer reading file notes from `./code-reading-notes/10_file_notes/`.
- Read at most 1 raw source file for verification if absolutely necessary.
- Do not broaden scope to another module.
- Stop as soon as one module note is complete.

## Required tasks
1. Read:
   - `./code-reading-notes/manifest.json`
   - `./code-reading-notes/00_repo_scan/module_candidates.json`
   - relevant file notes under `./code-reading-notes/10_file_notes/`
2. Resolve the module from `$ARGUMENTS` or choose the next unfinished module.
3. Produce:
   `./code-reading-notes/20_module_notes/module_<MODULE_NAME>.md`
4. Update manifest/progress/TODO minimally.

## Required output structure
# 模块：<模块名>
## 1. 模块定位
## 2. 包含文件
## 3. 模块内部逻辑
## 4. 对外接口
## 5. 设计亮点
## 6. 学习总结
## 7. 面试表达

## Stop condition
Stop after one module note is written.
