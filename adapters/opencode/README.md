# @atp/opencode

ATP (agent-team-protocol) opencode host adapter.

Generates opencode-compatible agent/command files from canonical ATP agent definitions.

## Install

```bash
npm install -g @atp/opencode
# or use npx:
npx @atp/opencode install
```

## Usage

### Install ATP agents to opencode

```bash
# Project scope (default: .opencode/)
atp-opencode install

# Global scope (~/.config/opencode/)
atp-opencode install --global

# With graphify agents (optional add-on)
atp-opencode install --with-graphify

# With specific provider model slugs baked in
atp-opencode install --provider amazon-bedrock

# Force overwrite existing files
atp-opencode install --force

# Require opencode binary to be present (default: warn only)
atp-opencode install --require-opencode
```

### Uninstall

```bash
atp-opencode uninstall
atp-opencode uninstall --global
```

### Options

| Option | Description |
|--------|-------------|
| `--global` | Install to `~/.config/opencode/` |
| `--project` | Install to `.opencode/` (default) |
| `--provider <id>` | Bake model slugs for provider (e.g. `amazon-bedrock`) |
| `--with-graphify` | Include graphify add-on agents |
| `--force` | Overwrite existing files |
| `--require-opencode` | Fail if opencode binary not found |

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | I/O error or permission denied |
| 2 | Invalid arguments |
| 3 | opencode binary not found (with --require-opencode) |
| 4 | Incomplete uninstall (residual files detected) |

## After Install

```bash
opencode run --command atp-task "작업 요청"
opencode agent list
```

## Notes

- Default install does NOT bake model slugs — agents inherit the primary model.
- Use `--provider amazon-bedrock` only when you want explicit Bedrock model slugs.
- Uninstall uses a manifest file (`.atp-opencode-manifest.json`) for exact cleanup.
