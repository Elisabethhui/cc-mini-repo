---
name: context-tier-policy
description: Use when a task has more relevant code than the model context can safely hold. Classify context into core, support, and peripheral tiers instead of hard-dropping files.
---

# Context Tier Policy

## Purpose

Prevent context loss when a task touches more code than a small-context model can read.

## Tiers

- Core: likely edit targets; include short source snippets.
- Support: direct dependencies; include signatures, responsibilities, constraints.
- Peripheral: broad impact; include paths, symbol names, one-line responsibility, and risk note.

## Degradation Policy

Full snippet -> short snippet -> signature -> responsibility summary -> path plus risk note. Never silently drop high-risk dependencies.
