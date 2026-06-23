---
name: fresh-review
description: Use when reviewing a completed implementation in a fresh, isolated context to avoid context-window overflow and self-review bias.
---

# Fresh Review

## Purpose

Review completed work in a clean context instead of the noisy implementation session.

## Inputs

Use only task goal, acceptance criteria, context summary, changed files, diff stat, focused diff, test result, map-sync freshness, and rollback path.

Do not include full chat history, full raw CodeGraph output, entire source files, or repeated logs.

## Recommendation

Return commit, revise, rollback, reslice, or hold.
