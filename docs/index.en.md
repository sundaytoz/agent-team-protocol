---
kind: docs-index
title: Agent Team Protocol Documentation Index (English)
description: English entry point for the bundled reference docs. Korean docs remain canonical unless an English page exists.
owner: template-maintainer
stability: living
last_reviewed: 2026-06-10
---

<p align="center">
  <a href="index.md">한국어</a> ·
  <a href="index.en.md">English</a>
</p>

# Documentation Index

This is the English entry point for the agent-team-protocol docs. English docs are an adoption path for first-time readers: the Korean documentation remains canonical unless an English page exists for a given topic.

## Categories

| Category | Audience | Index |
|---|---|---|
| Usage | Users installing the plugin and applying it to a consuming project | [docs/usage/index.en.md](./usage/index.en.md) |
| Development | Contributors maintaining the ATP protocol, agents, and skills — Korean-first/canonical | [docs/development/index.md](./development/index.md) |
| Architecture | Contributors checking repository structure and runtime artifact boundaries — Korean-first/canonical | [docs/architecture/index.md](./architecture/index.md) |
| ADR | Maintainers tracking hard-to-reverse technical and operational decisions — Korean-first/canonical | [docs/adr/index.md](./adr/index.md) |

## Boundary

`docs/` in this repository is human-facing documentation and is not shipped in the plugin bundle. The runtime reference docs that agents read via `${CLAUDE_PLUGIN_ROOT}/docs/...` live in [plugins/atp/docs/](../plugins/atp/docs/index.md). The editable documents that `/atp:init` generates inside a consuming project are scaffolded from [plugins/atp/templates/](../plugins/atp/templates/).

## Add-on

The graphify feature is an opt-in add-on. Installation, operation, and graph refresh rules are documented in [plugins/atp-graphify/docs/graphify-usage.md](../plugins/atp-graphify/docs/graphify-usage.md) (Korean-first/canonical).

## Quick Links

- Install and setup: [docs/usage/setup-checklist.en.md](./usage/setup-checklist.en.md)
- Troubleshooting: [docs/usage/faq.en.md](./usage/faq.en.md)
- Protocol reference (Korean-first/canonical): [plugins/atp/docs/development/agent-team-protocol.md](../plugins/atp/docs/development/agent-team-protocol.md)
- Agent catalog (Korean-first/canonical): [plugins/atp/docs/development/agent-catalog.md](../plugins/atp/docs/development/agent-catalog.md)
- File map (Korean-first/canonical): [docs/architecture/file-map.md](./architecture/file-map.md)
