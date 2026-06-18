<p align="center">
  <a href="README.md">한국어</a> ·
  <a href="README.en.md">English</a>
</p>

# Agent Team Protocol

A protocol and plugin for running AI coding work through role-based agent teams.

<p align="center">
  <a href="docs/usage/setup-checklist.en.md">Install</a> ·
  <a href="docs/index.en.md">Docs</a> ·
  <a href="plugins/atp/docs/development/agent-team-protocol.md">Protocol</a> ·
  <a href="docs/usage/faq.en.md">FAQ</a>
</p>

## Supported Platforms

| Platform | Status | Invocation | Instruction file | Verification level |
|---|---|---|---|---|
| Claude Code | Supported | `/atp:task` | `CLAUDE.md` | Reference implementation; continuously used and verified |
| Codex CLI | Supported | `$atp:task` or `$task` | `AGENTS.md` | Install, skill exposure, invocation, and body loading verified on 2026-06-10 with codex-cli 0.138.0; subagent spawn is based on cited official docs, so team-mode E2E smoke testing is recommended |
| Gemini CLI | Planned | `/atp:task` planned | `GEMINI.md` | Design documented as Tier A-flat; release artifact not generated yet |

The canonical capability-tier definitions and host self-assessment rules live in [plugins/atp/docs/development/platform-adapters.md](plugins/atp/docs/development/platform-adapters.md). The per-platform invocation syntax and verification markers in the table above are frozen as history in the appendices of [docs/adr/ADR-0009](docs/adr/ADR-0009-bundle-runtime-platform-neutralization.md) — the bundled runtime no longer enumerates platforms and works by capability self-assessment, so ATP can also run on host CLIs not listed here.

---

## 1. Why ATP Exists

When a single agent handles research, design, implementation, and verification in one continuous context, three problems tend to appear.

- **Context contamination**: verification can become biased by the implementation context that produced the change.
- **Model mismatch**: simple work may use an expensive model, while design work may use a smaller model than the decision needs.
- **File contention**: parallel work can write the same file twice or break dependency order.

ATP addresses those problems structurally.

| Problem | ATP approach |
|---|---|
| Context contamination | Isolate work by advisor; `verification-advisor` is especially separated from implementation context |
| Model mismatch | The orchestrator chooses the model per invocation based on phase, scale, and risk |
| File contention | `implementation-advisor` owns the file map and keeps one file under one worker |

---

## 2. Concept — 3-Tier Roles

```
Orchestrator  <- the only user-facing role; delegates, mediates, and reports.
    |
    +-- Tier-2 Advisor   <- completes one domain in a single invocation.
    |
    +-- Tier-3 Advisor   <- can coordinate parallel Workers for research or implementation.
          +-- Worker A --+
          +-- Worker B --+-- advisor merges the results
          +-- Worker C --+
```

The role names remain intentionally stable:

- **Orchestrator**: interprets the request, chooses advisors, manages shared session state, resolves conflicts, and reports to the user.
- **Advisor**: owns one domain such as requirements, design, implementation, verification, documentation, or retrospective.
- **Worker**: performs one narrow task under an advisor-owned scope.

The full protocol is in [plugins/atp/docs/development/agent-team-protocol.md](plugins/atp/docs/development/agent-team-protocol.md).

---

## 3. Installation

Use [docs/usage/setup-checklist.en.md](docs/usage/setup-checklist.en.md) for the current installation and smoke-test flow. The exact command syntax differs by platform.

For this repository's self-dogfooding flow, see [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md). The graphify knowledge graph integration is an optional add-on; see [plugins/atp-graphify/docs/graphify-usage.md](plugins/atp-graphify/docs/graphify-usage.md).

---

## 4. Repository Layout

The detailed file map is maintained in [docs/architecture/file-map.md](docs/architecture/file-map.md).

```
agent-team-protocol/
├── .claude-plugin/marketplace.json       Claude Code marketplace manifest
├── .codex-plugin/marketplace.json        Claude mirror
├── .agents/plugins/marketplace.json      Codex marketplace manifest
├── plugins/
│   ├── atp/                              base plugin root — only this subtree ships in the bundle
│   │   ├── .claude-plugin/ .codex-plugin/  plugin manifests
│   │   ├── agents/                       base agent definitions
│   │   ├── skills/                       atp:init and atp:task skills
│   │   ├── docs/development/             runtime reference docs
│   │   └── templates/                    atp:init scaffolding sources
│   └── atp-graphify/                     optional atp-graphify add-on
└── docs/                                 human-facing docs — excluded from the bundle
```

---

## 5. Further Reading

| Topic | Link |
|---|---|
| Documentation index | [docs/index.en.md](docs/index.en.md) |
| Protocol reference | [plugins/atp/docs/development/agent-team-protocol.md](plugins/atp/docs/development/agent-team-protocol.md) |
| Agent catalog | [plugins/atp/docs/development/agent-catalog.md](plugins/atp/docs/development/agent-catalog.md) |
| Platform adapters | [plugins/atp/docs/development/platform-adapters.md](plugins/atp/docs/development/platform-adapters.md) |
| File map | [docs/architecture/file-map.md](docs/architecture/file-map.md) |
| FAQ | [docs/usage/faq.en.md](docs/usage/faq.en.md) |
| Init skill | [plugins/atp/skills/init/SKILL.md](plugins/atp/skills/init/SKILL.md) |
| Task skill | [plugins/atp/skills/task/SKILL.md](plugins/atp/skills/task/SKILL.md) |
| graphify add-on | [plugins/atp-graphify/docs/graphify-usage.md](plugins/atp-graphify/docs/graphify-usage.md) |

The English README is an entry point. Linked canonical documents may currently be Korean-first.

---

## 6. Credits

Originally created by 이정수 (WEMADE PLAY, DevOps). See [AUTHORS](AUTHORS) for details.

## 7. Security

See [SECURITY.md](SECURITY.md) for security reporting.

## 8. License

Released under the MIT License. See [LICENSE](LICENSE).

## 9. Changes, Backlog, and Contributions

Template improvement history and backlog live in [TEMPLATE_DEV.md](TEMPLATE_DEV.md). Hard-to-reverse decisions are tracked in [docs/adr/](docs/adr/index.md).
