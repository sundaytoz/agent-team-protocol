// adapters/opencode/src/transform-agent.js
// canonical ATP agent md → opencode agent md transform.
// design.md B.1 (name/description/permission/mode), B.2 (body name rewrite),
// C (output schema), D (conditional model bake). as-of 2026-06-24

import { parseFrontmatter, serializeFrontmatter } from './frontmatter.js';
import { toPermission, prefixName, AGENT_TIER, TIER_SLUG, ALWAYS } from './mappings.js';
import { rewriteRefs } from './rewrite-refs.js';

/**
 * Transform a canonical ATP agent markdown string into its opencode equivalent.
 *
 * @param {string} md   full canonical agent file string (frontmatter + body)
 * @param {{ scopeRoot: string, provider: ?string }} opts
 *   - scopeRoot: display root for body path rewrite ("~/.config/opencode" | ".opencode")
 *   - provider:  null → no model bake (default inherit, D.1);
 *                'amazon-bedrock' → bake tier slug when small/medium (D.2);
 *                anything else → ignored (model omitted; validation is CLI/plan's job).
 * @returns {{ name: string, content: string }}
 *   name: prefixed identifier ('atp-<canonical>'); content: serialized opencode md.
 */
export function transformAgent(md, opts) {
  const { scopeRoot, provider } = opts;

  // 1) parse canonical frontmatter + body
  const { data, body } = parseFrontmatter(md);

  // 2) name → prefixed
  const canonicalName = data.name;

  // 4) permission from tools (Write→edit+write, Bash absent→bash:deny, Agent/LSP drop, task:deny — all in mappings)
  const permission = toPermission(data.tools || []);

  // 6) conditional model bake (design D)
  //   provider null → omit model entirely (default inherit, AC-14 expects grep '^model:' == 0)
  //   provider 'amazon-bedrock' → bake slug for small/medium; omit for large/unassigned (inherit, D.2)
  //   any other provider (or missing TIER_SLUG entry) → omit (defensive)
  let modelSlug;
  if (provider === 'amazon-bedrock') {
    const tier = AGENT_TIER[canonicalName];
    const slug = TIER_SLUG[provider]?.[tier];
    if (slug) modelSlug = slug;
  }

  // 7) body transform: path rewrite → agent-name rewrite (design E.3)
  const newBody = rewriteRefs(body, scopeRoot);

  // 8) assemble opencode frontmatter — drop canonical-only keys (tools/version/peer_agents/comments).
  //    serializeFrontmatter orders: name → description → mode → model → permission.
  const outData = {
    name: prefixName(canonicalName),
    description: data.description, // 3) original preserved (G3); serializer quotes safely
    ...ALWAYS,                     // 5) mode: subagent — SSoT from mappings (design C.4)
    ...(modelSlug ? { model: modelSlug } : {}), // 6) conditional bake (D.2); omitted → inherit (D.1)
    permission,                    // serializer enforces final key order regardless of literal order
  };

  // 9) serialize
  const content = serializeFrontmatter(outData, newBody);

  // 10) return
  return { name: prefixName(canonicalName), content };
}
