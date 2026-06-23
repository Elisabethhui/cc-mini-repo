# State Router Design

## Current Mode

Human-driven and AI-assisted.

## Future Mode

AI-assisted router recommends next step but does not silently write, commit, delete, or rollback.

## States

no_goal, needs_macro_plan, needs_task_slice, needs_surface_search, needs_code_intel, needs_context_pack, ready_to_implement, implementation_done, needs_map_sync, needs_test_gate, needs_fresh_review, needs_review_decision, needs_work_log, ready_to_commit, blocked, done.
