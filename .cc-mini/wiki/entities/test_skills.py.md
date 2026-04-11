# Entity: tests/test_skills.py

## Classes
- **class TestParseFrontmatter**: 无文档说明
  - Methods: test_full_frontmatter, test_no_frontmatter, test_quoted_values, test_boolean_variants, test_comment_lines_ignored
- **class TestSkill**: 无文档说明
  - Methods: test_from_frontmatter, test_arguments_substitution, test_skill_dir_substitution, test_prompt_fn, test_prompt_fn_takes_priority
- **class TestRegistry**: 无文档说明
  - Methods: test_register_and_get, test_list_all, test_bundled_sorted_first, test_clear_all, test_clear_by_source
- **class TestBundledSkills**: 无文档说明
  - Methods: test_registers_four_skills, test_simplify_no_args, test_simplify_with_args, test_review_prompt, test_commit_prompt, test_test_prompt, test_all_bundled_are_user_invocable, test_all_bundled_source_is_bundled
- **class TestLoadFromDisk**: 无文档说明
  - Methods: test_directory_format_skill_md, test_directory_without_skill_md_has_fallback, test_legacy_single_file, test_empty_dir_skipped, test_no_md_dir_skipped, test_nonexistent_dir, test_prompt_substitution_from_disk, test_skill_root_set_correctly
- **class TestDiscoverSkills**: 无文档说明
  - Methods: test_project_level, test_nonexistent_path_safe
- **class TestPromptSection**: 无文档说明
  - Methods: test_empty_when_no_skills, test_lists_skills
- **class TestAutocomplete**: 无文档说明
  - Methods: _completions, test_slash_s_includes_skills_and_simplify, test_slash_co_includes_compact_and_commit, test_slash_re_includes_resume_and_review, test_no_completions_without_slash, test_project_skill_appears
- **class TestCommandParsing**: 无文档说明
  - Methods: test_skill_as_slash_command, test_non_slash_not_parsed

## Functions
- **def _clean_registry()**: Ensure each test starts with a clean skill registry.