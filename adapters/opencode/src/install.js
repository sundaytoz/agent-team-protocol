// adapters/opencode/src/install.js
// Plan executor for the opencode host adapter.
// Consumes buildPlan() output and materializes it on disk: prune stale →
// mkdir → emit write → docs/templates copy → manifest record. Pure I/O side of
// the generator; planning (canonical reads/transforms) lives in plan.js.
//
// design.md F.1 (runInstall logic, fixed order), F.3 (manifest schema),
// E.1 (display vs install root). Idempotent re-install: ATP outputs are always
// overwritten (re-install = refresh), and files dropped from the new plan are
// pruned via the previous manifest (AC-13 → orphan 0).
// as-of 2026-06-24

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawnSync } from 'child_process';

import { buildPlan } from './plan.js';
import {
  resolveScopeRoot,
  resolveAgentsDir,
  resolveCommandsDir,
  resolveAtpDocsDir,
  resolveAtpTemplatesDir,
  resolveManifestPath,
} from './paths.js';

// ---------------------------------------------------------------------------
// Repo-root resolution for source_version (design F.3).
// This file lives at <repo>/adapters/opencode/src/install.js, so the repo root
// is three levels up; the canonical plugin.json carries the source version.
// ---------------------------------------------------------------------------
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename); // .../adapters/opencode/src

/**
 * Execute an install plan and record a manifest.
 *
 * Order is fixed (design F.1): scope → opencode probe → plan → prune stale →
 * mkdir → emit write → docs/templates copy → manifest write → summary.
 *
 * Never calls process.exit — returns an exitCode for the CLI to act on.
 *
 * @param {{
 *   scope: 'global'|'project',
 *   provider: ?string,        // null | 'amazon-bedrock' (used verbatim)
 *   withGraphify: boolean,
 *   force: boolean,           // extra-cleanup intent (ATP outputs overwrite regardless)
 *   requireOpencode: boolean, // fail (exit 3) when opencode binary is absent
 * }} opts
 * @returns {{ exitCode: number, messages: string[], errors: string[] }}
 *   exitCode: 0 success / 1 I/O error / 3 requireOpencode but opencode absent
 */
export function runInstall(opts) {
  const messages = [];

  // 1) scope resolution + display root (design E.1)
  const root = resolveScopeRoot(opts.scope);
  const displayRoot =
    opts.scope === 'global' ? '~/.config/opencode' : '.opencode';

  // 2) opencode presence probe (soft, design F.1.2)
  const probe = spawnSync('opencode', ['--version'], { stdio: 'ignore' });
  const opencodePresent = !probe.error && probe.status === 0;
  if (!opencodePresent) {
    if (opts.requireOpencode) {
      return {
        exitCode: 3,
        errors: ['opencode 바이너리를 PATH 에서 못 찾음 (--require-opencode).'],
        messages: [],
      };
    }
    messages.push(
      '경고: opencode 바이너리를 PATH 에서 못 찾음 — 파일은 설치하되, opencode 설치 후 `opencode agent list` 로 확인 권장.',
    );
  }

  try {
    // 3) plan
    const plan = buildPlan({
      installRoot: root,
      displayRoot,
      provider: opts.provider,
      withGraphify: opts.withGraphify,
    });

    const manifestPath = resolveManifestPath(root);

    // 4) re-install stale prune (design F.1 — prune before write).
    //    Previous-manifest files absent from the new plan are stale → unlink.
    //    Direct prune (no uninstall import) to avoid a circular dependency.
    const newDests = new Set([
      ...plan.emits.map((e) => e.destAbs),
      ...plan.copies.map((c) => c.destAbs),
    ]);
    if (fs.existsSync(manifestPath)) {
      try {
        const prev = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
        for (const f of prev.files || []) {
          if (!newDests.has(f) && fs.existsSync(f)) fs.unlinkSync(f);
        }
      } catch {
        // unreadable/corrupt previous manifest — skip prune, proceed with install.
      }
    }

    // 5) mkdir base dirs (design F.1.4)
    for (const dir of [
      resolveAgentsDir(root),
      resolveCommandsDir(root),
      resolveAtpDocsDir(root),
      resolveAtpTemplatesDir(root),
    ]) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // 6) emit write + manifest collect (design F.1.5 + F.1.7 — same loop, C3).
    //    ATP outputs are ALWAYS overwritten (force-independent: re-install = refresh).
    const writtenFiles = [];
    for (const { destAbs, content } of plan.emits) {
      fs.mkdirSync(path.dirname(destAbs), { recursive: true });
      fs.writeFileSync(destAbs, content, 'utf8');
      writtenFiles.push(destAbs);
    }

    // 7) docs/templates copy + manifest collect (design F.1.6 + F.1.7 — same loop).
    for (const { srcAbs, destAbs } of plan.copies) {
      fs.mkdirSync(path.dirname(destAbs), { recursive: true });
      fs.copyFileSync(srcAbs, destAbs);
      writtenFiles.push(destAbs);
    }

    // 8) manifest record (design F.1.7, F.3).
    //    source_version from the canonical plugin.json (3 levels up = repo root).
    let sourceVersion = null;
    try {
      const pj = JSON.parse(
        fs.readFileSync(
          path.resolve(
            __dirname,
            '..',
            '..',
            '..',
            'plugins/atp/.claude-plugin/plugin.json',
          ),
          'utf8',
        ),
      );
      sourceVersion = pj.version ?? null;
    } catch {
      // version unavailable — record null (non-fatal).
    }

    const manifest = {
      tool: 'atp-opencode',
      schema: 1,
      installed_at: new Date().toISOString(),
      scope: opts.scope,
      root,
      options: {
        withGraphify: !!opts.withGraphify,
        provider: opts.provider ?? null,
      },
      source_version: sourceVersion,
      // sorted for AC-13 idempotent manifest comparison stability.
      // manifestPath itself is intentionally NOT in files[] (design F.3) —
      // writtenFiles only holds emit+copy dests, so this holds automatically.
      files: writtenFiles.slice().sort(),
    };
    fs.writeFileSync(
      manifestPath,
      JSON.stringify(manifest, null, 2) + '\n',
      'utf8',
    );

    // 9) summary (design F.1.8).
    const agentsDir = resolveAgentsDir(root);
    const commandsDir = resolveCommandsDir(root);
    const n = plan.emits.filter(
      (e) => path.dirname(e.destAbs) === agentsDir,
    ).length;
    const m = plan.emits.filter(
      (e) => path.dirname(e.destAbs) === commandsDir,
    ).length;
    const k = plan.copies.length;
    messages.push(
      `설치 완료: agent ${n}개, command ${m}개, docs/templates ${k}개 복사.`,
    );
    messages.push('scope=' + opts.scope + ', root=' + root);
    messages.push('스모크: opencode run --command atp-task "..."');

    // 10) return
    return { exitCode: 0, messages, errors: [] };
  } catch (err) {
    return { exitCode: 1, errors: [String(err)], messages };
  }
}
