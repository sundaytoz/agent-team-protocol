<p align="center"><a href="CONTRIBUTING.md">한국어</a> · <a href="CONTRIBUTING.en.md">English</a></p>

# Contributing

This document complements the root [`CLAUDE.md`](../CLAUDE.md) and [`AGENTS.md`](../AGENTS.md). It does not restate the full conventions; it gives the gist of each topic plus a link to the canonical document.

## Before you start

docs-first principle: for any task, read [`docs/index.en.md`](../docs/index.en.md) first, then the relevant category `index.md`, then the specific document, before starting work.

## Repository layout / three-tree separation

Keep the three trees separate: `plugins/atp/docs/` (bundled runtime reference), root `docs/` (human-facing docs), and `plugins/atp/templates/` (editable sources). For the detailed layout, see [`CLAUDE.md`](../CLAUDE.md).

## Development & verification entry

Small tasks are handled directly by the main agent; the 3-tier team mode is entered only when you explicitly invoke `/atp:task` (Claude Code) or `$atp:task` (Codex). To self-dogfood in this repository, the local plugin must be enabled first ([`CLAUDE.md`](../CLAUDE.md) · [`AGENTS.md`](../AGENTS.md)).

## Commit convention

Use a Conventional Commits prefix (`feat` / `fix` / `docs` / `refactor` / `chore`; mark a breaking change with `!`). Every AI-collaboration commit must carry a `Co-Authored-By` trailer. The message body may mix Korean and English.

## Pull request flow

Do not push directly to the main branch. Work from a fork or a feature branch and merge through pull requests.

## ADR rules

Record hard-to-reverse decisions as `docs/adr/ADR-NNNN-kebab.md`. ADRs are append-only; to reverse a decision, do not edit the existing document — create a new ADR and link it with supersedes. The section structure is Context / Decision / Consequences / Alternatives ([`docs/adr/index.md`](../docs/adr/index.md)).

## Release trigger gate

When a user-facing `feat` in the `plugins/` bundle is merged into main, complete the release within the same unit of work: manifest version bump through to `/plugin update` ([`docs/development/release-checklist.md`](../docs/development/release-checklist.md)).

## Documentation language policy

Korean is canonical; English pages are an adoption path. Keep `*.en.md` English mirrors alongside the canonical Korean documents, and preserve domain terms in their original form.

## Code of conduct / security / support

See [`CODE_OF_CONDUCT.en.md`](CODE_OF_CONDUCT.en.md) · [`SECURITY.md`](../SECURITY.md) · [`SUPPORT.en.md`](SUPPORT.en.md).

---

These community files (under `.github/`) are **for this repository only** and are not copied into `/atp:init` consumer projects.
