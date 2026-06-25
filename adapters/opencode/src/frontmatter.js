/**
 * frontmatter.js
 *
 * Zero-dependency YAML frontmatter parser / serializer for canonical ATP agent files.
 * gray-matter / js-yaml are intentionally excluded.
 *
 * Supported schema (flat):
 *   name, description, version, mode, trigger, disable-model-invocation  — scalars
 *   tools       — comma-separated single line  →  string[]
 *   peer_agents — block sequence (`- item`)    →  string[]
 *   permission  — nested map (read/bash/task)  →  object  (serialize only)
 *   # comment lines — ignored on parse
 *   unknown keys — stored as raw string
 *
 * ESM module (package.json: "type": "module").
 */

// ─────────────────────────────────────────────
// Internal helpers
// ─────────────────────────────────────────────

/**
 * Extract the raw frontmatter block and the body that follows it.
 * Returns { raw: string|null, body: string }.
 *
 * Spec: first `---` line → second `---` line (exclusive).
 * The closing `---` may be followed immediately by the body.
 */
function splitFrontmatter(md) {
  // Normalise line endings so the regex works uniformly.
  const text = md.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

  // Must start with `---` on its own line (optional leading spaces ignored per YAML).
  const openRe = /^---[ \t]*\n/;
  const match = openRe.exec(text);
  if (!match) return { raw: null, body: text };

  const afterOpen = text.slice(match[0].length);
  // Find closing `---` line.
  const closeRe = /\n---[ \t]*(\n|$)/;
  const closeMatch = closeRe.exec(afterOpen);
  if (!closeMatch) return { raw: null, body: text };

  const raw = afterOpen.slice(0, closeMatch.index);
  const body = afterOpen.slice(closeMatch.index + closeMatch[0].length);
  return { raw, body };
}

/**
 * Parse one scalar value: strip optional surrounding quotes,
 * convert bare integers, leave everything else as string.
 */
function parseScalar(raw) {
  const v = raw.trim();
  // Quoted strings — single or double.
  if ((v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))) {
    return v.slice(1, -1);
  }
  // Integer.
  if (/^-?\d+$/.test(v)) return parseInt(v, 10);
  return v;
}

/**
 * Determine whether a YAML scalar value needs quoting in output.
 * We quote minimally: only when the value contains `:` followed by a space,
 * starts with a YAML indicator character, or contains `"`.
 */
function needsQuoting(str) {
  if (typeof str !== 'string') return false;
  // Contains double-quote → must quote (use single quotes).
  if (str.includes('"')) return true;
  // Contains `: ` sequence (would be parsed as a mapping).
  if (/: /.test(str)) return true;
  // Starts with a YAML flow indicator.
  if (/^[{[\|>&*!,%@`]/.test(str)) return true;
  return false;
}

/**
 * Serialize a scalar string safely for YAML output.
 */
function serializeScalar(val) {
  if (typeof val === 'number') return String(val);
  const s = String(val);
  if (!needsQuoting(s)) return s;
  // Prefer single-quote wrapping (escaping inner `'` as `''`).
  if (!s.includes("'")) return `'${s}'`;
  // Fall back to double-quote, escaping inner `"`.
  return `"${s.replace(/"/g, '\\"')}"`;
}

// ─────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────

/**
 * parseFrontmatter(md)
 *
 * md  — full markdown file string (frontmatter + body)
 * Returns { data: Object, body: string }
 *
 * data keys:
 *   tools       → string[]   (comma-split)
 *   peer_agents → string[]   (block-sequence items)
 *   others      → string | number
 */
export function parseFrontmatter(md) {
  const { raw, body } = splitFrontmatter(md);
  if (raw === null) return { data: {}, body: md };

  const data = {};
  const lines = raw.split('\n');

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    // Skip blank lines and comment lines.
    if (/^\s*$/.test(line) || /^\s*#/.test(line)) {
      i++;
      continue;
    }

    // Key: value  (mapping entry)
    const mapMatch = /^(\S[^:]*?)\s*:\s*(.*)$/.exec(line);
    if (!mapMatch) {
      i++;
      continue;
    }

    const key = mapMatch[1].trim();
    const rest = mapMatch[2].trim();

    // ── peer_agents: block sequence (value is empty, next lines are `- item`) ──
    if (key === 'peer_agents') {
      const items = [];
      i++;
      while (i < lines.length && /^\s*-\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*-\s+/, '').trim());
        i++;
      }
      data[key] = items;
      continue;
    }

    // ── tools: comma-separated single line ──
    if (key === 'tools') {
      data[key] = rest
        .split(',')
        .map(t => t.trim())
        .filter(t => t.length > 0);
      i++;
      continue;
    }

    // ── generic scalar ──
    data[key] = rest === '' ? '' : parseScalar(rest);
    i++;
  }

  return { data, body };
}

/**
 * serializeFrontmatter(data, body)
 *
 * data  — transformed frontmatter key-map
 * body  — substitution-complete markdown body
 * Returns reassembled markdown string with YAML frontmatter block.
 *
 * Key output order: name → description → mode → model → permission → others
 */
export function serializeFrontmatter(data, body) {
  // Canonical key ordering.
  const ORDER = ['name', 'description', 'mode', 'model', 'permission'];
  const orderedKeys = [
    ...ORDER.filter(k => Object.prototype.hasOwnProperty.call(data, k)),
    ...Object.keys(data).filter(k => !ORDER.includes(k)),
  ];

  const lines = [];

  for (const key of orderedKeys) {
    const val = data[key];

    // ── peer_agents → block sequence ──
    if (key === 'peer_agents') {
      if (Array.isArray(val) && val.length > 0) {
        lines.push('peer_agents:');
        for (const item of val) {
          lines.push(`  - ${item}`);
        }
      } else {
        lines.push('peer_agents:');
      }
      continue;
    }

    // ── tools → comma-separated single line ──
    if (key === 'tools') {
      const toolStr = Array.isArray(val) ? val.join(', ') : String(val);
      lines.push(`tools: ${toolStr}`);
      continue;
    }

    // ── permission → nested YAML map ──
    if (key === 'permission' && val !== null && typeof val === 'object' && !Array.isArray(val)) {
      lines.push('permission:');
      for (const [subKey, subVal] of Object.entries(val)) {
        lines.push(`  ${subKey}: ${serializeScalar(subVal)}`);
      }
      continue;
    }

    // ── generic scalar ──
    lines.push(`${key}: ${serializeScalar(val)}`);
  }

  const frontmatter = `---\n${lines.join('\n')}\n---\n`;
  return frontmatter + body;
}
