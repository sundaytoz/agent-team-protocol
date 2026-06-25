// adapters/opencode/src/plan.js
// Pure planning module for the opencode host adapter (generator core).
// Resolves the canonical ATP source tree (repo-root plugins/**), transforms
// agents/commands, and enumerates docs/templates copy targets — WITHOUT touching
// the filesystem for writes. Only canonical reads are performed here; install.js
// executes the resulting plan.
//
// design.md A.1 (plan.js), B.3 (agent collect+transform), B.4 (docs copy),
// E.4 (templates copy), F.1.3 (display vs install root), G7 (command transform).
// as-of 2026-06-24

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

import { transformAgent } from './transform-agent.js';
import { transformCommand } from './transform-command.js';
import {
  resolveAgentsDir,
  resolveCommandsDir,
  resolveAtpDocsDir,
  resolveAtpTemplatesDir,
  resolveCanonicalPluginsRoot,
} from './paths.js';

// ---------------------------------------------------------------------------
// Canonical plugins/ root resolution.
// Prefers the vendor bundle (npm-installed) over the repo-local path so that
// `npx @atp-opencode/opencode install` works after publish AND repo-local self-dogfooding
// keeps working. See paths.js#resolveCanonicalPluginsRoot.
// ---------------------------------------------------------------------------
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename); // .../adapters/opencode/src

const PLUGINS_ROOT = resolveCanonicalPluginsRoot(__dirname);

const CANONICAL_AGENTS_BASE = path.join(PLUGINS_ROOT, 'atp', 'agents');
const CANONICAL_AGENTS_GRAPHIFY = path.join(PLUGINS_ROOT, 'atp-graphify', 'agents');
const CANONICAL_SKILLS_DIR = path.join(PLUGINS_ROOT, 'atp', 'skills');
const CANONICAL_DOCS_BASE = path.join(PLUGINS_ROOT, 'atp', 'docs');
const CANONICAL_GRAPHIFY_USAGE = path.join(
  PLUGINS_ROOT,
  'atp-graphify',
  'docs',
  'graphify-usage.md',
);
const CANONICAL_TEMPLATES_BASE = path.join(PLUGINS_ROOT, 'atp', 'templates');

/**
 * Recursively collect the absolute paths of every file under `dir`
 * (directories themselves are excluded; nested structure is flattened to paths).
 *
 * @param {string} dir absolute directory path
 * @returns {string[]} absolute file paths
 */
function walkDir(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walkDir(full));
    else out.push(full);
  }
  return out;
}

/**
 * Collect canonical agent `.md` files from `agentsDir`, transform each, and push
 * the resulting EmitItems into `emits`.
 *
 * @param {string} agentsDir   canonical agents directory (absolute)
 * @param {string} agentsDest  install agents directory (absolute)
 * @param {string} displayRoot body path-rewrite display root
 * @param {?string} provider   model-bake provider (passed verbatim to transform)
 * @param {Array} emits        accumulator
 */
function collectAgents(agentsDir, agentsDest, displayRoot, provider, emits) {
  const files = fs
    .readdirSync(agentsDir)
    .filter((f) => f.endsWith('.md'));
  for (const file of files) {
    const md = fs.readFileSync(path.join(agentsDir, file), 'utf8');
    const { name, content } = transformAgent(md, { scopeRoot: displayRoot, provider });
    emits.push({ destAbs: path.join(agentsDest, name + '.md'), content });
  }
}

/**
 * Build the install plan (pure function — canonical reads only, zero writes).
 *
 * @param {{
 *   installRoot: string,   // absolute fs root for writes (resolveScopeRoot result)
 *   displayRoot: string,   // display string for body path rewrite
 *                          //   ("~/.config/opencode" | ".opencode")
 *   provider: ?string,     // null | 'amazon-bedrock' (passed verbatim to transform)
 *   withGraphify: boolean, // include atp-graphify agents + graphify-usage doc
 * }} opts
 * @returns {{ emits: EmitItem[], copies: CopyItem[] }}
 *   EmitItem = { destAbs: string, content: string }  // generated agent/command md
 *   CopyItem = { srcAbs: string, destAbs: string }   // canonical → install copy
 */
export function buildPlan(opts) {
  const { installRoot, displayRoot, provider, withGraphify } = opts;

  const emits = [];
  const copies = [];

  // -------------------------------------------------------------------------
  // 2) agents → transform → EmitItem (design B.3)
  // -------------------------------------------------------------------------
  const agentsDest = resolveAgentsDir(installRoot);
  collectAgents(CANONICAL_AGENTS_BASE, agentsDest, displayRoot, provider, emits);
  if (withGraphify) {
    collectAgents(CANONICAL_AGENTS_GRAPHIFY, agentsDest, displayRoot, provider, emits);
  }

  // -------------------------------------------------------------------------
  // 3) skills → command transform → EmitItem (design G7)
  //    each skills/<dir>/SKILL.md becomes one opencode command.
  // -------------------------------------------------------------------------
  const commandsDest = resolveCommandsDir(installRoot);
  for (const entry of fs.readdirSync(CANONICAL_SKILLS_DIR, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const skillMd = path.join(CANONICAL_SKILLS_DIR, entry.name, 'SKILL.md');
    if (!fs.existsSync(skillMd)) continue;
    const md = fs.readFileSync(skillMd, 'utf8');
    const { name, content } = transformCommand(md, { scopeRoot: displayRoot });
    emits.push({ destAbs: path.join(commandsDest, name + '.md'), content });
  }

  // -------------------------------------------------------------------------
  // 4) docs copy list (design B.4 — always copy everything, structure preserved)
  // -------------------------------------------------------------------------
  const docsDest = resolveAtpDocsDir(installRoot);
  for (const srcAbs of walkDir(CANONICAL_DOCS_BASE)) {
    const rel = path.relative(CANONICAL_DOCS_BASE, srcAbs);
    copies.push({ srcAbs, destAbs: path.join(docsDest, rel) });
  }
  if (withGraphify) {
    // graphify-usage lands under development/ (design B.4)
    copies.push({
      srcAbs: CANONICAL_GRAPHIFY_USAGE,
      destAbs: path.join(docsDest, 'development', 'graphify-usage.md'),
    });
  }

  // -------------------------------------------------------------------------
  // 5) templates copy list (design E.4 — always copy everything, structure preserved)
  // -------------------------------------------------------------------------
  const templatesDest = resolveAtpTemplatesDir(installRoot);
  for (const srcAbs of walkDir(CANONICAL_TEMPLATES_BASE)) {
    const rel = path.relative(CANONICAL_TEMPLATES_BASE, srcAbs);
    copies.push({ srcAbs, destAbs: path.join(templatesDest, rel) });
  }

  // -------------------------------------------------------------------------
  // 6) return the plan
  // -------------------------------------------------------------------------
  return { emits, copies };
}
