// adapters/opencode/test/install.test.js
// install / uninstall round-trip tests for the opencode adapter.
// design G.1 AC mapping (AC-01, AC-01b, AC-02, AC-12, AC-13, AC-14).
//
// Isolation: runInstall/runUninstall with scope='project' write to
// `process.cwd()/.opencode`. Each test creates a unique dir under os.tmpdir(),
// process.chdir()'s into it, runs, then restores cwd + rm -rf in a finally block.
// opencode binary is NOT required (requireOpencode:false), so these run anywhere.
//
// Run with: node --test  (DO NOT run here — verification is a separate stage)

import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { runInstall } from '../src/install.js';
import { runUninstall } from '../src/uninstall.js';

// ---------------------------------------------------------------------------
// Repo-source counts — computed dynamically (invariant; never hard-coded).
// __dirname = .../adapters/opencode/test ; repo root = three levels up.
// ---------------------------------------------------------------------------
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..');

function countMd(absDir) {
  return fs.readdirSync(absDir).filter((f) => f.endsWith('.md')).length;
}

const BASE_AGENTS = path.join(REPO_ROOT, 'plugins', 'atp', 'agents');
const GRAPHIFY_AGENTS = path.join(REPO_ROOT, 'plugins', 'atp-graphify', 'agents');

const N_BASE_AGENTS = countMd(BASE_AGENTS);
const N_GRAPHIFY_AGENTS = countMd(GRAPHIFY_AGENTS);

// ---------------------------------------------------------------------------
// Output-dir helpers (mirror paths.js layout for the project scope).
// ---------------------------------------------------------------------------
const OPENCODE = '.opencode';
const MANIFEST = '.atp-opencode-manifest.json';

function listAtpAgents(cwd) {
  const dir = path.join(cwd, OPENCODE, 'agents');
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((f) => f.startsWith('atp-') && f.endsWith('.md'));
}

function listAtpCommands(cwd) {
  const dir = path.join(cwd, OPENCODE, 'commands');
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((f) => f.startsWith('atp-') && f.endsWith('.md'));
}

function readManifest(cwd) {
  const p = path.join(cwd, OPENCODE, MANIFEST);
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

/**
 * Create a unique tmp working dir, chdir into it, run `fn(tmpDir)`, then always
 * restore the original cwd and remove the tmp dir.
 */
function withTmpCwd(fn) {
  const prevCwd = process.cwd();
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'atp-opencode-'));
  // realpath: macOS tmpdir is a /var → /private/var symlink; normalise so any
  // cwd-derived comparisons stay consistent.
  const realTmp = fs.realpathSync(tmpDir);
  try {
    process.chdir(realTmp);
    return fn(realTmp);
  } finally {
    process.chdir(prevCwd);
    fs.rmSync(realTmp, { recursive: true, force: true });
  }
}

const INSTALL_OPTS = {
  scope: 'project',
  provider: null,
  withGraphify: false,
  force: false,
  requireOpencode: false,
};

// ===========================================================================
// 1) install --project basic (AC-01, AC-02)
// ===========================================================================

test('install --project: exit 0, agent count == repo base agents, exactly 2 commands', () => {
  withTmpCwd((cwd) => {
    const res = runInstall({ ...INSTALL_OPTS });
    assert.equal(res.exitCode, 0, res.errors.join('\n'));

    // AC-01 invariant: emitted atp-*.md agents == canonical base agent count.
    assert.equal(listAtpAgents(cwd).length, N_BASE_AGENTS);

    // AC-02: exactly atp-task.md + atp-init.md.
    const cmds = listAtpCommands(cwd).sort();
    assert.deepEqual(cmds, ['atp-init.md', 'atp-task.md']);

    // manifest exists and is non-empty.
    const manifest = readManifest(cwd);
    assert.ok(manifest, 'manifest must exist after install');
    assert.ok(Array.isArray(manifest.files));
    assert.ok(manifest.files.length > 0);
  });
});

// ===========================================================================
// 2) AC-01b --with-graphify (base + graphify agents)
// ===========================================================================

test('install --with-graphify: agent count == base + graphify agents', () => {
  withTmpCwd((cwd) => {
    const res = runInstall({ ...INSTALL_OPTS, withGraphify: true });
    assert.equal(res.exitCode, 0, res.errors.join('\n'));
    assert.equal(
      listAtpAgents(cwd).length,
      N_BASE_AGENTS + N_GRAPHIFY_AGENTS,
    );
  });
});

// ===========================================================================
// 3) AC-13 idempotent re-install (manifest files[] stable)
// ===========================================================================

test('install twice: second manifest files[] == first (sorted deepEqual)', () => {
  withTmpCwd((cwd) => {
    const first = runInstall({ ...INSTALL_OPTS });
    assert.equal(first.exitCode, 0, first.errors.join('\n'));
    const m1 = readManifest(cwd).files.slice().sort();

    const second = runInstall({ ...INSTALL_OPTS });
    assert.equal(second.exitCode, 0, second.errors.join('\n'));
    const m2 = readManifest(cwd).files.slice().sort();

    assert.deepEqual(m2, m1);
  });
});

// ===========================================================================
// 4) AC-12 uninstall — zero residue
// ===========================================================================

test('uninstall after install: exit 0, no atp-* files, no atp/ dir, no manifest', () => {
  withTmpCwd((cwd) => {
    const ins = runInstall({ ...INSTALL_OPTS, withGraphify: true });
    assert.equal(ins.exitCode, 0, ins.errors.join('\n'));

    const un = runUninstall({ scope: 'project' });
    assert.equal(un.exitCode, 0, un.errors.join('\n'));

    // atp-*.md globs in agents/ and commands/ → 0.
    assert.equal(listAtpAgents(cwd).length, 0);
    assert.equal(listAtpCommands(cwd).length, 0);

    // .opencode/atp/ directory absent.
    assert.equal(fs.existsSync(path.join(cwd, OPENCODE, 'atp')), false);

    // manifest absent.
    assert.equal(fs.existsSync(path.join(cwd, OPENCODE, MANIFEST)), false);
  });
});

// ===========================================================================
// 5) uninstall no-op on a clean dir (no manifest)
// ===========================================================================

test('uninstall with no manifest: exit 0 (safe no-op)', () => {
  withTmpCwd(() => {
    const un = runUninstall({ scope: 'project' });
    assert.equal(un.exitCode, 0, un.errors.join('\n'));
  });
});

// ===========================================================================
// 6) AC-14 default bake 0 — no ^model: in any installed agent (provider null)
// ===========================================================================

test('install provider:null: zero ^model: lines across all installed agents', () => {
  withTmpCwd((cwd) => {
    const res = runInstall({ ...INSTALL_OPTS, withGraphify: true });
    assert.equal(res.exitCode, 0, res.errors.join('\n'));

    const agentsDir = path.join(cwd, OPENCODE, 'agents');
    const files = fs.readdirSync(agentsDir).filter((f) => f.endsWith('.md'));
    assert.ok(files.length > 0, 'expected installed agent files');

    for (const f of files) {
      const text = fs.readFileSync(path.join(agentsDir, f), 'utf8');
      assert.equal(
        /^model:/m.test(text),
        false,
        `agent ${f} unexpectedly contains a model: line`,
      );
    }
  });
});
