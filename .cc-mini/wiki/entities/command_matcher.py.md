# Entity: src/core/sandbox/command_matcher.py

## Classes
- **class RuleType**: 无文档说明
  - Methods: 
- **class MatchRule**: 无文档说明
  - Methods: 

## Functions
- **def parse_rule()**: Parse an exclusion pattern into a MatchRule.
- **def matches_rule()**: Check whether a command matches a rule.
- **def _split_compound_command()**: Split compound commands on '&&'.
- **def _strip_env_prefix()**: Strip leading environment variable assignments.
- **def contains_excluded_command()**: Determine whether a command should be excluded from sandbox.