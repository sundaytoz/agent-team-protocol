---
kind: usage
title: Usage Category Index (English)
description: English index for plugin installation, initialization, and operation guides.
owner: template-maintainer
stability: living
last_reviewed: 2026-06-10
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

4. Initialize — generates the docs skeleton plus the `CLAUDE.md` guidance block in your project

   ```
   /atp:init
   ```

5. Fill placeholders → run an `/atp:task` smoke test → done

See [setup-checklist.en.md](./setup-checklist.en.md) for details.

## Recommended Reading Order

1. [setup-checklist.en.md](./setup-checklist.en.md) — setup right after install (3 steps)
2. [faq.en.md](./faq.en.md) — when something goes wrong
3. Agent composition — [`../../plugins/atp/docs/development/agent-catalog.md`](../../plugins/atp/docs/development/agent-catalog.md) (Korean-first/canonical)
