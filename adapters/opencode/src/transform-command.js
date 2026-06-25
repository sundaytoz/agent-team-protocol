// adapters/opencode/src/transform-command.js
// canonical SKILL.md → opencode command md.
// design.md B.1 (command transform) + G7 (primary/fan-out) + E.4 (path rewrite in heredocs)
// + research "Command frontmatter". as-of 2026-06-24

import { parseFrontmatter, serializeFrontmatter } from './frontmatter.js';
import { prefixName } from './mappings.js';
import { rewriteRefs } from './rewrite-refs.js';

/**
 * transformCommand(md, opts)
 *
 * Convert a canonical Claude Code SKILL.md into an opencode command markdown.
 *
 * opencode command frontmatter schema (research-verified):
 *   - description : preserved verbatim from the skill (required)
 *   - agent       : UNSET — runs as primary (atp-task / atp-init)
 *   - subtask     : UNSET — atp-task MUST stay primary so the orchestrator can
 *                   fan out to subagents; setting subtask would force the command
 *                   to run as a subagent and disable fan-out (research/G7).
 *   - model       : UNSET — inherit
 * canonical-only keys (trigger, disable-model-invocation) are dropped — they are
 * not part of the opencode command schema.
 *
 * Body transforms:
 *   - rewriteRefs : ${CLAUDE_PLUGIN_ROOT}/${CLAUDE_PROJECT_DIR} path rewrite,
 *                   then canonical agent-name → atp-<name> rewrite (E.3/E.4).
 *   - $ARGUMENTS  : opencode substitutes user input at this token. Canonical
 *                   skill bodies do not contain it, so prepend one line. If the
 *                   body already contains $ARGUMENTS, leave it untouched (no dup).
 *
 * @param {string} md                full canonical SKILL.md file string
 * @param {{ scopeRoot: string }} opts
 *   scopeRoot — display root for body path rewrite
 *               ("~/.config/opencode" | ".opencode")
 * @returns {{ name: string, content: string }}
 *   name    — 'atp-<skillname>' (file identifier, e.g. "atp-task")
 *   content — opencode command markdown string
 */
export function transformCommand(md, opts) {
  const { scopeRoot } = opts;

  // 1) parse
  const { data, body } = parseFrontmatter(md);

  // 2) identity — skill name → prefixed command identifier
  const skillName = data.name;

  // 3) body: path + agent-name rewrite
  const newBody = rewriteRefs(body, scopeRoot);

  // 4) $ARGUMENTS injection (skip if already present)
  const finalBody = newBody.includes('$ARGUMENTS')
    ? newBody
    : '$ARGUMENTS\n\n' + newBody;

  // 5) opencode command frontmatter — description only.
  //    agent / subtask / model intentionally unset (primary + fan-out capable).
  const outData = {
    description: data.description,
  };

  // 6) serialize
  const content = serializeFrontmatter(outData, finalBody);

  // 7) emit
  return { name: prefixName(skillName), content };
}
