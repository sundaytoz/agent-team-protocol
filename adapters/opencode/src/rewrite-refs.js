// adapters/opencode/src/rewrite-refs.js
// Body-string transforms shared by transform-* — path substitution + agent-name rewrite.
// design.md E (path rewrite) + B.2 (agent-name rewrite). as-of 2026-06-24

import { CANONICAL_AGENT_NAMES, prefixName } from './mappings.js';

/**
 * Escape regex metacharacters in a string so it can be embedded as a literal
 * inside a dynamically-built RegExp. Agent names contain only [a-z-] in
 * practice, but this is defensive (design B.2 rule 2).
 * @param {string} s
 * @returns {string}
 */
function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Rewrite ${CLAUDE_PLUGIN_ROOT} / ${CLAUDE_PROJECT_DIR} references in body text
 * to scope-relative paths (design E.1–E.4).
 *
 * Order is fixed for determinism: PLUGIN_ROOT first, then PROJECT_DIR (E.3).
 *
 *  - ${CLAUDE_PLUGIN_ROOT}        → @<scopeRoot>/atp   (read-only bundled ref → @-ref; E.2/E.4)
 *  - ${CLAUDE_PROJECT_DIR}/       → ''                 (relative path; leading slash dropped)
 *  - ${CLAUDE_PROJECT_DIR}        → '.'                (bare, no trailing slash → cwd)
 *
 * Trailing path segments are preserved automatically because the regexes only
 * match the variable token (design E, rule 6).
 *
 * @param {string} text       body text being transformed
 * @param {string} scopeRoot  install root ("~/.config/opencode" | ".opencode")
 * @returns {string}
 */
export function rewritePaths(text, scopeRoot) {
  return text
    // 1) PLUGIN_ROOT first — literal token only → @<scopeRoot>/atp
    .replace(/\$\{CLAUDE_PLUGIN_ROOT\}/g, '@' + scopeRoot + '/atp')
    // 2) PROJECT_DIR with trailing slash → relative (strip leading slash)
    .replace(/\$\{CLAUDE_PROJECT_DIR\}\//g, '')
    // 3) remaining bare PROJECT_DIR (no trailing slash) → current dir
    .replace(/\$\{CLAUDE_PROJECT_DIR\}/g, '.');
}

/**
 * Rewrite every canonical agent name in body text to its prefixed identifier
 * (design B.2).
 *
 *  - Longest-match first: names sorted by length desc before sequential
 *    replacement, so e.g. `graphify-lookup-advisor` is rewritten before any
 *    shorter substring could interfere (rule 1).
 *  - Word-boundary match: `(?<![\w-])NAME(?![\w-])` — matches only when neither
 *    neighbour is a word char or hyphen (rule 2).
 *  - Idempotent: the trailing `-` of an already-prefixed `atp-<name>` trips the
 *    `(?<![\w-])` lookbehind, so a second pass rewrites nothing (rule 3).
 *
 * @param {string}   text   body text being transformed
 * @param {string[]} names  canonical agent names (defaults to CANONICAL_AGENT_NAMES)
 * @returns {string}
 */
export function rewriteAgentNames(text, names = CANONICAL_AGENT_NAMES) {
  const sorted = [...names].sort((a, b) => b.length - a.length);
  let result = text;
  for (const name of sorted) {
    const re = new RegExp('(?<![\\w-])' + escapeRegex(name) + '(?![\\w-])', 'g');
    result = result.replace(re, prefixName(name));
  }
  return result;
}

/**
 * Convenience composition: apply path rewrite then agent-name rewrite, in the
 * fixed order paths → names (design E.3). Called by transform-* modules.
 *
 * @param {string}   text       body text being transformed
 * @param {string}   scopeRoot  install root ("~/.config/opencode" | ".opencode")
 * @param {string[]} names      canonical agent names (defaults to CANONICAL_AGENT_NAMES)
 * @returns {string}
 */
export function rewriteRefs(text, scopeRoot, names = CANONICAL_AGENT_NAMES) {
  return rewriteAgentNames(rewritePaths(text, scopeRoot), names);
}
