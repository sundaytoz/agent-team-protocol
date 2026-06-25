// adapters/opencode/src/mappings.js
// Data-only module — no logic. tool→permission table + tier→slug table.
// as-of 2026-06-24

// canonical tool token → opencode permission key array (value: 'allow')
// Bash absence and task are handled by separate rules (see toPermission)
export const TOOL_PERMISSION = {
  Read:            ['read'],
  Write:           ['edit', 'write'],   // both keys (C2 concern)
  Edit:            ['edit'],
  Grep:            ['grep'],
  Glob:            ['glob'],
  Bash:            ['bash'],
  WebFetch:        ['webfetch'],
  WebSearch:       ['websearch'],
  AskUserQuestion: ['question'],
  // Agent → not emitted (replaced by task:deny rule)
  // LSP   → drop
};

// tools whose permission keys are never emitted
export const DROP_TOOLS = ['Agent', 'LSP'];

// mode injected for every agent config
export const ALWAYS = { mode: 'subagent' };

// permissions always denied for every subagent (A-flat rule)
export const ALWAYS_DENY = ['task'];

// when Bash is absent from a tool list, bash:deny is appended
export const BASH_DENY_WHEN_ABSENT = true;

// provider id → { tier: opencode model slug }  (staleness warning: snapshot 2026-06-24)
export const TIER_SLUG = {
  'amazon-bedrock': {
    small:  'amazon-bedrock/anthropic.claude-haiku-4-5-20251001-v1:0',
    medium: 'amazon-bedrock/anthropic.claude-sonnet-4-6',
    // large: inherit default — not baked in
  },
};

// agent canonical name → tier ('small' | 'medium') — used for model bake when --provider is set
export const AGENT_TIER = {
  'code-writer':             'small',
  'migration-writer':        'small',
  'parallel-explorer':       'small',
  'graph-refresh-checker':   'small',
  'graphify-lookup-advisor': 'small',
  'verification-advisor':    'small',
  'requirements-advisor':    'medium',
  'design-advisor':          'medium',
  'documentation-advisor':   'medium',
  'research-advisor':        'medium',
  'implementation-advisor':  'medium',
  'graphify-update-advisor': 'medium',
  'retrospective-advisor':   'medium',
};

// 13 agent canonical names (longest-match sort is done inside rewrite-refs.js)
export const CANONICAL_AGENT_NAMES = [
  'graphify-lookup-advisor',
  'graphify-update-advisor',
  'graph-refresh-checker',
  'implementation-advisor',
  'requirements-advisor',
  'retrospective-advisor',
  'documentation-advisor',
  'verification-advisor',
  'parallel-explorer',
  'research-advisor',
  'design-advisor',
  'migration-writer',
  'code-writer',
];

/**
 * canonical tools list → opencode permission object
 * @param {string[]} tools - array of canonical tool tokens e.g. ["Read","Write","Bash"]
 * @returns {Record<string, 'allow'|'deny'>}
 *   e.g. { read:'allow', edit:'allow', write:'allow', bash:'allow', task:'deny' }
 */
export function toPermission(tools) {
  const keys = new Set();
  let hasBash = false;

  for (const tool of tools) {
    if (DROP_TOOLS.includes(tool)) continue;
    if (tool === 'Bash') hasBash = true;
    const mapped = TOOL_PERMISSION[tool];
    if (mapped) {
      for (const k of mapped) keys.add(k);
    }
  }

  const result = {};

  // emit allow entries
  for (const k of keys) {
    result[k] = 'allow';
  }

  // bash:deny when Bash was absent from tool list
  if (BASH_DENY_WHEN_ABSENT && !hasBash) {
    result['bash'] = 'deny';
  }

  // task:deny always (ALWAYS_DENY)
  for (const k of ALWAYS_DENY) {
    result[k] = 'deny';
  }

  return result;
}

/**
 * canonical agent name → opencode identifier (idempotent)
 * @param {string} name
 * @returns {string}
 */
export function prefixName(name) {
  return name.startsWith('atp-') ? name : 'atp-' + name;
}
