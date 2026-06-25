// adapters/opencode/test/transform.test.js
// Unit tests for the opencode adapter transform pipeline.
// design G.1 AC mapping (AC-02/03/04/05/06/07/14/15).
// Pure unit tests — no filesystem writes, no opencode binary required.
// Run with: node --test  (DO NOT run here — verification is a separate stage)

import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { parseFrontmatter, serializeFrontmatter } from '../src/frontmatter.js';
import { toPermission, prefixName } from '../src/mappings.js';
import {
  rewritePaths,
  rewriteAgentNames,
} from '../src/rewrite-refs.js';
import { transformAgent } from '../src/transform-agent.js';
import { transformCommand } from '../src/transform-command.js';

// ---------------------------------------------------------------------------
// Path helpers — resolve fixtures + canonical repo sources by absolute path.
// __dirname = .../adapters/opencode/test ; repo root = three levels up.
// ---------------------------------------------------------------------------
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..');
const FIXTURE_AGENT = path.join(__dirname, 'fixtures', 'sample-agent.md');
const CANONICAL_CODE_WRITER = path.join(
  REPO_ROOT,
  'plugins',
  'atp',
  'agents',
  'code-writer.md',
);
const CANONICAL_TASK_SKILL = path.join(
  REPO_ROOT,
  'plugins',
  'atp',
  'skills',
  'task',
  'SKILL.md',
);

function readFixtureAgent() {
  return fs.readFileSync(FIXTURE_AGENT, 'utf8');
}

// ===========================================================================
// frontmatter parser / serializer
// ===========================================================================

test('parseFrontmatter: parses fixture name/tools/peer_agents', () => {
  const { data } = parseFrontmatter(readFixtureAgent());
  assert.equal(data.name, 'sample-advisor');
  assert.deepEqual(data.tools, ['Read', 'Write', 'Edit', 'Grep', 'Glob', 'LSP']);
  assert.deepEqual(data.peer_agents, ['design-advisor', 'code-writer']);
});

test('serializeFrontmatter: round-trips mode/permission/description-colon/body', () => {
  const out = serializeFrontmatter(
    {
      name: 'x',
      description: 'a: b',
      mode: 'subagent',
      permission: { read: 'allow', task: 'deny' },
    },
    'BODY',
  );

  // mode line present
  assert.match(out, /^mode: subagent$/m);
  // permission nested map with task: deny present
  assert.match(out, /^permission:$/m);
  assert.match(out, /^ {2}task: deny$/m);
  // body preserved
  assert.match(out, /BODY/);

  // description colon survives a parse round-trip ('a: b' restored exactly)
  const { data } = parseFrontmatter(out);
  assert.equal(data.description, 'a: b');
  assert.equal(data.mode, 'subagent');
});

// ===========================================================================
// toPermission (AC-05 — output contract)
// ===========================================================================

test('toPermission: Read/Write/Edit/Grep/Glob/LSP → no-bash, task:deny, LSP dropped', () => {
  const perm = toPermission(['Read', 'Write', 'Edit', 'Grep', 'Glob', 'LSP']);
  assert.deepEqual(perm, {
    read: 'allow',
    edit: 'allow',
    write: 'allow',
    grep: 'allow',
    glob: 'allow',
    bash: 'deny',
    task: 'deny',
  });
});

test('toPermission: Bash present → bash:allow, Agent/LSP dropped, only task:deny', () => {
  const perm = toPermission(['Read', 'Grep', 'Glob', 'Bash', 'Agent', 'LSP']);
  assert.equal(perm.bash, 'allow');
  assert.equal(perm.task, 'deny');
  // LSP dropped → no lsp key
  assert.ok(!('lsp' in perm));
  // Agent dropped → no task:allow leak; task is the only deny entry
  const denies = Object.entries(perm).filter(([, v]) => v === 'deny');
  assert.deepEqual(denies, [['task', 'deny']]);
});

test('toPermission: AskUserQuestion → question:allow', () => {
  const perm = toPermission(['Read', 'Grep', 'Glob', 'Bash', 'AskUserQuestion']);
  assert.equal(perm.question, 'allow');
});

test('toPermission: WebFetch/WebSearch → webfetch:allow + websearch:allow', () => {
  const perm = toPermission(['Read', 'Grep', 'Glob', 'Bash', 'WebFetch', 'WebSearch']);
  assert.equal(perm.webfetch, 'allow');
  assert.equal(perm.websearch, 'allow');
});

// ===========================================================================
// prefixName (idempotent)
// ===========================================================================

test('prefixName: adds atp- prefix and is idempotent', () => {
  assert.equal(prefixName('design-advisor'), 'atp-design-advisor');
  assert.equal(prefixName('atp-design-advisor'), 'atp-design-advisor');
});

// ===========================================================================
// rewritePaths (AC-06)
// ===========================================================================

test('rewritePaths: PLUGIN_ROOT → @<scopeRoot>/atp (project scope)', () => {
  assert.equal(
    rewritePaths('${CLAUDE_PLUGIN_ROOT}/docs/x.md', '.opencode'),
    '@.opencode/atp/docs/x.md',
  );
});

test('rewritePaths: PROJECT_DIR/ → relative (leading slash dropped)', () => {
  assert.equal(
    rewritePaths('${CLAUDE_PROJECT_DIR}/docs/y.md', '.opencode'),
    'docs/y.md',
  );
});

test('rewritePaths: PLUGIN_ROOT → @<scopeRoot>/atp (global scope)', () => {
  assert.equal(
    rewritePaths('${CLAUDE_PLUGIN_ROOT}/docs/x.md', '~/.config/opencode'),
    '@~/.config/opencode/atp/docs/x.md',
  );
});

test('rewritePaths: AC-06 — no CLAUDE_PLUGIN_ROOT / CLAUDE_PROJECT_DIR residue', () => {
  const input =
    '${CLAUDE_PLUGIN_ROOT}/a ${CLAUDE_PROJECT_DIR}/b ${CLAUDE_PROJECT_DIR}';
  const out = rewritePaths(input, '.opencode');
  assert.ok(!out.includes('CLAUDE_PLUGIN_ROOT'));
  assert.ok(!out.includes('CLAUDE_PROJECT_DIR'));
  // bare PROJECT_DIR (no trailing slash) → '.'
  assert.match(out, /\.$/);
});

// ===========================================================================
// rewriteAgentNames (AC-07, design B.2)
// ===========================================================================

test('rewriteAgentNames: canonical names → atp- prefixed', () => {
  assert.equal(
    rewriteAgentNames('design-advisor 와 code-writer'),
    'atp-design-advisor 와 atp-code-writer',
  );
});

test('rewriteAgentNames: idempotent (double pass == single pass)', () => {
  const x = 'design-advisor 와 code-writer 에게 위임';
  const once = rewriteAgentNames(x);
  const twice = rewriteAgentNames(once);
  assert.equal(twice, once);
});

test('rewriteAgentNames: word-boundary — already-prefixed name untouched', () => {
  assert.equal(rewriteAgentNames('atp-design-advisor'), 'atp-design-advisor');
});

test('rewriteAgentNames: longest-match — graphify-lookup-advisor whole token', () => {
  const names = [
    'graphify-lookup-advisor',
    'graph-refresh-checker',
    'design-advisor',
    'code-writer',
  ];
  assert.equal(
    rewriteAgentNames('graphify-lookup-advisor', names),
    'atp-graphify-lookup-advisor',
  );
  // no partial double-prefix leakage
  assert.ok(!rewriteAgentNames('graphify-lookup-advisor', names).includes('atp-atp-'));
});

// ===========================================================================
// transformAgent (AC-03 / 04 / 06 / 14 / 15)
// ===========================================================================

test('transformAgent: fixture → name/mode/permission/no-model/canonical-keys-dropped', () => {
  const md = readFixtureAgent();
  const { name, content } = transformAgent(md, {
    scopeRoot: '.opencode',
    provider: null,
  });

  // name prefixed (AC-15)
  assert.equal(name, 'atp-sample-advisor');

  // mode: subagent (AC-03)
  assert.match(content, /^mode: subagent$/m);
  // task: deny (AC-04) + bash: deny (Bash absent from tools)
  assert.match(content, /^ {2}task: deny$/m);
  assert.match(content, /^ {2}bash: deny$/m);

  // no model line at all (AC-14, provider null)
  assert.equal(/^model:/m.test(content), false);

  // canonical-only frontmatter keys removed.
  // Split off the frontmatter block to assert these keys are gone from it.
  const fmMatch = /^---\n([\s\S]*?)\n---\n/.exec(content);
  assert.ok(fmMatch, 'serialized output must contain a frontmatter block');
  const fm = fmMatch[1];
  assert.equal(/^tools:/m.test(fm), false);
  assert.equal(/^version:/m.test(fm), false);
  assert.equal(/^peer_agents:/m.test(fm), false);

  // body: agent-name rewrite applied (design-advisor → atp-design-advisor)
  assert.match(content, /atp-design-advisor/);
  assert.match(content, /atp-code-writer/);

  // body: PLUGIN_ROOT rewritten + zero CLAUDE_ residue (AC-06)
  assert.match(
    content,
    /@\.opencode\/atp\/docs\/development\/agent-team-protocol\.md/,
  );
  assert.ok(!content.includes('${CLAUDE_'));
});

test('transformAgent: provider amazon-bedrock bakes small-tier model for code-writer', () => {
  // code-writer is tier "small" in AGENT_TIER → bedrock haiku slug baked (design D.2).
  const md = fs.readFileSync(CANONICAL_CODE_WRITER, 'utf8');
  const { name, content } = transformAgent(md, {
    scopeRoot: '.opencode',
    provider: 'amazon-bedrock',
  });
  assert.equal(name, 'atp-code-writer');
  // model line present and points at the bedrock haiku (small) slug.
  assert.match(content, /^model: amazon-bedrock\/anthropic\.claude-haiku/m);
});

// ===========================================================================
// transformCommand (AC-02)
// ===========================================================================

test('transformCommand: task SKILL → atp-task primary command', () => {
  const md = fs.readFileSync(CANONICAL_TASK_SKILL, 'utf8');
  const { name, content } = transformCommand(md, { scopeRoot: '.opencode' });

  // name prefixed
  assert.equal(name, 'atp-task');

  // $ARGUMENTS injected (skill body has none → prepended at top)
  assert.match(content, /\$ARGUMENTS/);

  // frontmatter: description kept, agent/subtask unset (stays primary, fan-out capable)
  const fmMatch = /^---\n([\s\S]*?)\n---\n/.exec(content);
  assert.ok(fmMatch, 'command output must contain a frontmatter block');
  const fm = fmMatch[1];
  assert.equal(/^description:/m.test(fm), true);
  assert.equal(/^subtask:/m.test(fm), false);
  assert.equal(/^agent:/m.test(fm), false);

  // path rewrite applied → no CLAUDE_ residue
  assert.ok(!content.includes('${CLAUDE_'));
});
