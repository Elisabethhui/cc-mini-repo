# Entity: src/core/sandbox/config.py

## Classes
- **class SandboxFilesystemConfig**: Filesystem restriction configuration.
  - Methods: 
- **class SandboxConfig**: Top-level sandbox configuration.
  - Methods: 

## Functions
- **def load_sandbox_config()**: Load sandbox config from TOML [sandbox] section.
- **def save_sandbox_config()**: Save sandbox config to TOML [sandbox] section.
- **def _dict_to_config()**: Convert a flat/nested dict to SandboxConfig.
- **def _config_to_dict()**: Convert SandboxConfig to a serializable dict.
- **def _render_sandbox_section()**: Render [sandbox] and [sandbox.filesystem] as TOML text.
- **def _replace_sandbox_section()**: Replace or append [sandbox] block in TOML text, preserving everything else.
- **def _write_toml()**: Minimal TOML writer sufficient for our config structure.
- **def _format_kv()**: Format a single TOML key = value pair.