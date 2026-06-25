# Graph Report - adapters/opencode  (2026-06-25)

## Corpus Check
- Corpus is ~7,648 words - fits in a single context window. You may not need a graph.

## Summary
- 162 nodes · 297 edges · 9 communities
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Install·Plan 실행 코어|Install·Plan 실행 코어]]
- [[_COMMUNITY_Agent 변환 개념·매핑|Agent 변환 개념·매핑]]
- [[_COMMUNITY_Vendor 번들·패키징|Vendor 번들·패키징]]
- [[_COMMUNITY_Install 테스트|Install 테스트]]
- [[_COMMUNITY_Transform 테스트|Transform 테스트]]
- [[_COMMUNITY_Tool·Tier 매핑 상수|Tool·Tier 매핑 상수]]
- [[_COMMUNITY_Frontmatter YAML 직렬화|Frontmatter YAML 직렬화]]
- [[_COMMUNITY_Canonical 번들 스크립트|Canonical 번들 스크립트]]
- [[_COMMUNITY_참조 경로·이름 재작성|참조 경로·이름 재작성]]

## God Nodes (most connected - your core abstractions)
1. `runInstall() - plan executor` - 12 edges
2. `transformAgent() - canonical agent to opencode format` - 12 edges
3. `runInstall()` - 11 edges
4. `buildPlan() - pure install plan builder` - 11 edges
5. `buildPlan()` - 10 edges
6. `runUninstall()` - 10 edges
7. `transformAgent()` - 9 edges
8. `runUninstall() - manifest-driven uninstall` - 9 edges
9. `transform.test.js - transform pipeline unit tests` - 9 edges
10. `transformCommand()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `README - opencode adapter documentation` --references--> `Model Bake - provider-specific slug injection`  [EXTRACTED]
  adapters/opencode/README.md → adapters/opencode/src/transform-agent.js
- `transform.test.js - transform pipeline unit tests` --references--> `sample-agent.md - test fixture canonical agent`  [EXTRACTED]
  adapters/opencode/test/transform.test.js → adapters/opencode/test/fixtures/sample-agent.md
- `sample-agent.md - test fixture canonical agent` --conceptually_related_to--> `mode: subagent - forced opencode agent mode`  [INFERRED]
  adapters/opencode/test/fixtures/sample-agent.md → adapters/opencode/src/mappings.js
- `main()` --calls--> `runInstall()`  [EXTRACTED]
  bin/cli.js → src/install.js
- `main()` --calls--> `runUninstall()`  [EXTRACTED]
  bin/cli.js → src/uninstall.js

## Hyperedges (group relationships)
- **Transform Pipeline (parse → rewrite → serialize)** — frontmatter_parseFrontmatter, rewrite_rewriteRefs, mappings_toPermission, frontmatter_serializeFrontmatter [EXTRACTED 0.95]
- **Install Flow (plan → prune → mkdir → write → manifest)** — plan_buildPlan, install_runInstall, paths_resolveManifestPath, concept_manifest [EXTRACTED 0.95]
- **Canonical Source Resolution (vendor bundle vs repo fallback)** — paths_resolveCanonicalPluginsRoot, concept_vendor_bundle, bundle_canonical [EXTRACTED 0.90]

## Communities (9 total, 0 thin omitted)

### Community 0 - "Install·Plan 실행 코어"
Cohesion: 0.14
Nodes (29): emit(), main(), printVersion(), __dirname, __filename, PLUGINS_ROOT, runInstall(), resolveAgentsDir() (+21 more)

### Community 1 - "Agent 변환 개념·매핑"
Cohesion: 0.13
Nodes (26): $ARGUMENTS injection - opencode user input substitution, atp- Namespace Prefix - opencode identifier convention, Model Bake - provider-specific slug injection, mode: subagent - forced opencode agent mode, task: deny - fan-out prevention for subagents, sample-agent.md - test fixture canonical agent, needsQuoting() - YAML quoting predicate, parseFrontmatter() - YAML frontmatter parser (+18 more)

### Community 2 - "Vendor 번들·패키징"
Cohesion: 0.13
Nodes (23): bundle-canonical.js - prepack vendor bundler, CLI emit(result), CLI main() entrypoint, Canonical Single Source (plugins/**) - ADR-0014 D3, CopyItem - canonical to install copy plan unit, EmitItem - generated agent/command md plan unit, Manifest (.atp-opencode-manifest.json) - install record, Install Scope (global vs project) (+15 more)

### Community 3 - "Install 테스트"
Cohesion: 0.08
Nodes (19): agentsDir, BASE_AGENTS, cmds, __dirname, files, first, GRAPHIFY_AGENTS, ins (+11 more)

### Community 4 - "Transform 테스트"
Cohesion: 0.12
Nodes (15): CANONICAL_CODE_WRITER, CANONICAL_TASK_SKILL, { data }, denies, __dirname, FIXTURE_AGENT, fmMatch, md (+7 more)

### Community 5 - "Tool·Tier 매핑 상수"
Cohesion: 0.27
Nodes (9): AGENT_TIER, ALWAYS, ALWAYS_DENY, CANONICAL_AGENT_NAMES, DROP_TOOLS, TIER_SLUG, TOOL_PERMISSION, toPermission() (+1 more)

### Community 6 - "Frontmatter YAML 직렬화"
Cohesion: 0.4
Nodes (8): needsQuoting(), parseFrontmatter(), parseScalar(), serializeFrontmatter(), serializeScalar(), splitFrontmatter(), prefixName(), transformCommand()

### Community 7 - "Canonical 번들 스크립트"
Cohesion: 0.22
Nodes (8): COPY_TARGETS, destAbs, __dirname, missing, PKG_ROOT, REPO_ROOT, srcAbs, VENDOR_DIR

### Community 8 - "참조 경로·이름 재작성"
Cohesion: 0.7
Nodes (4): escapeRegex(), rewriteAgentNames(), rewritePaths(), rewriteRefs()

## Knowledge Gaps
- **68 isolated node(s):** `__dirname`, `REPO_ROOT`, `FIXTURE_AGENT`, `CANONICAL_CODE_WRITER`, `CANONICAL_TASK_SKILL` (+63 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `transformCommand()` connect `Frontmatter YAML 직렬화` to `Install·Plan 실행 코어`, `참조 경로·이름 재작성`, `Transform 테스트`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `buildPlan() - pure install plan builder` connect `Vendor 번들·패키징` to `Agent 변환 개념·매핑`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `transformAgent() - canonical agent to opencode format` connect `Agent 변환 개념·매핑` to `Vendor 번들·패키징`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **What connects `__dirname`, `REPO_ROOT`, `FIXTURE_AGENT` to the rest of the system?**
  _68 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Install·Plan 실행 코어` be split into smaller, more focused modules?**
  _Cohesion score 0.14 - nodes in this community are weakly interconnected._
- **Should `Agent 변환 개념·매핑` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._
- **Should `Vendor 번들·패키징` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._