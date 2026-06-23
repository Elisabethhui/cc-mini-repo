# Prompt Minimization Plan

## Purpose

Plan how to reduce system prompt/token overhead by moving detailed workflow behavior into skills and local files.

## Goal

Keep runtime prompts short while preserving workflow correctness.

## Strategy

- system prompt contains only router-level rules
- detailed steps live in skills
- project facts live in project map
- task specifics live in task/context pack
- logs stay local and ignored

## Risks

- model may not load skill when needed
- too many files create confusion
- critical safety rules may be hidden too deep

## Rule

Safety and file boundary rules stay visible. Long procedural detail moves into skills.
