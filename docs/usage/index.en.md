---
kind: usage
title: Usage Category Index (English)
description: English index for plugin installation, initialization, and operation guides.
owner: template-maintainer
stability: living
last_reviewed: 2026-09-08
---

<p align="center">
  <a href="index.md">한국어</a> ·
  <a href="index.en.md">English</a>
</p>

# Usage — User Guides

This category collects documents written from the perspective of a **user installing and operating** the `atp` / `atp-graphify` plugins. Internal structure is covered in `architecture/`, and development rules in `development/` (both Korean-first/canonical).

## Documents

- [setup-checklist.en.md](./setup-checklist.en.md) — 3-step setup checklist after plugin install: `/atp:init` → fill placeholders → `/atp:task` smoke test
- [faq.en.md](./faq.en.md) — troubleshooting FAQ: install failures, unrecognized commands, graphify skip, init re-run, and more
- [known-issues.en.md](./known-issues.en.md) — current platform limitations, impact, workarounds, and exit criteria
- [codex-connection-smoke.en.md](./codex-connection-smoke.en.md) — actual one-subagent connection check, 2026-09-08 observations, and validation limits
- [best-practices.md](./best-practices.md) — known workflow costs and recommended task-shaping practices (Korean-first/canonical)

## Installation Order

1. Register the marketplace

   ```
   /plugin marketplace add sundaytoz/agent-team-protocol
   ```

2. Install the base plugin (required)

   ```
   /plugin install atp@agent-team-protocol
   ```

3. Install the graphify add-on (opt-in)

   ```
   /plugin install atp-graphify@agent-team-protocol
   ```

   To turn on real team execution in Codex CLI, also install the `atp-codex-hooks` add-on and grant hook trust in the TUI (opt-in; consents to out-of-sandbox hook execution) — see [faq.en.md](./faq.en.md#codex-hooks-add-on).

4. Initialize — generates the docs skeleton plus the `CLAUDE.md` guidance block in your project

   ```
   /atp:init
   ```

5. Fill placeholders → run an `/atp:task` smoke test → done

See [setup-checklist.en.md](./setup-checklist.en.md) for details.

## Recommended Reading Order

1. [setup-checklist.en.md](./setup-checklist.en.md) — setup right after install (3 steps)
2. [known-issues.en.md](./known-issues.en.md) — check current limitations
3. [faq.en.md](./faq.en.md) — when something goes wrong
4. [best-practices.md](./best-practices.md) — before shaping a larger task (Korean-first/canonical)
5. Agent composition — [`../../plugins/atp/docs/development/agent-catalog.md`](../../plugins/atp/docs/development/agent-catalog.md) (Korean-first/canonical)
