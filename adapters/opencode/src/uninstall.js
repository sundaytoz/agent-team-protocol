import fs from 'fs';
import path from 'path';
import {
  resolveScopeRoot,
  resolveAgentsDir,
  resolveCommandsDir,
  resolveAtpDir,
  resolveManifestPath,
} from './paths.js';

/**
 * List `atp-*.md` filenames in `dir`. Dependency-free glob.
 * @param {string} dir
 * @returns {string[]} matching filenames (empty if dir does not exist)
 */
function listAtpFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((n) => n.startsWith('atp-') && n.endsWith('.md'));
}

/**
 * Manifest-driven exact uninstall with zero-residue verification.
 *
 * Does NOT call process.exit — returns an exit code for the CLI to apply
 * (kept side-effect-free for testability).
 *
 * @param {{ scope: 'global'|'project' }} opts
 *        scope is used only to resolve the manifest path; all other options
 *        were recorded in the manifest at install time.
 * @returns {{ exitCode: number, messages: string[], errors: string[] }}
 *        exitCode: 0 success / 1 I/O error / 4 residue detected (incomplete removal)
 */
export function runUninstall(opts) {
  const messages = [];
  const errors = [];

  // 1. resolve scope
  const root = resolveScopeRoot(opts.scope);

  // 2. read manifest
  const manifestPath = resolveManifestPath(root);

  if (!fs.existsSync(manifestPath)) {
    // F.2.2 — no install record, safe no-op
    return {
      exitCode: 0,
      messages: ['설치 기록 없음 — 제거할 항목이 없습니다 (no-op).'],
      errors: [],
    };
  }

  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  } catch (_e) {
    return {
      exitCode: 1,
      errors: ['매니페스트 파싱 실패: ' + manifestPath],
      messages: [],
    };
  }

  // 3. delete every file listed in files[] (best-effort)
  const files = Array.isArray(manifest.files) ? manifest.files : [];
  const deletedParents = new Set();
  let deletedCount = 0;

  for (const filePath of files) {
    try {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        deletedCount += 1;
      }
      deletedParents.add(path.dirname(filePath));
    } catch (e) {
      errors.push('파일 삭제 실패: ' + filePath + ' (' + e.message + ')');
    }
  }

  // 4. clean up emptied directories (leaf -> root, empty-only)
  const dirCandidates = new Set();

  // implied directories from the manifest
  for (const implied of [resolveAgentsDir(root), resolveCommandsDir(root), resolveAtpDir(root)]) {
    dirCandidates.add(implied);
  }

  // deleted file parents + all ancestors up to (but excluding) root
  for (const parent of deletedParents) {
    dirCandidates.add(parent);
  }

  // expand every candidate to its ancestor chain, keep only dirs strictly below root
  const rootWithSep = root.endsWith(path.sep) ? root : root + path.sep;
  const dirsToRemove = new Set();
  for (const candidate of dirCandidates) {
    let current = candidate;
    // walk up until we reach root (exclusive) or filesystem boundary
    while (current.startsWith(rootWithSep)) {
      dirsToRemove.add(current);
      const next = path.dirname(current);
      if (next === current) break;
      current = next;
    }
  }

  // deepest first so children are removed before parents
  const sortedDirs = Array.from(dirsToRemove).sort((a, b) => b.length - a.length);
  for (const dir of sortedDirs) {
    try {
      // rmdir only succeeds on empty dirs; non-empty (user files) -> EOTEMPTY, ignored
      fs.rmdirSync(dir);
    } catch (_e) {
      // not empty or already gone — skip (root itself is never in this set)
    }
  }

  // 5. delete the manifest itself
  try {
    fs.unlinkSync(manifestPath);
  } catch (e) {
    errors.push('매니페스트 삭제 실패: ' + manifestPath + ' (' + e.message + ')');
  }

  // 6. zero-residue verification (self-check, secondary safety net)
  const residue = [];

  for (const leftover of listAtpFiles(resolveAgentsDir(root))) {
    residue.push(path.join(resolveAgentsDir(root), leftover));
  }
  for (const leftover of listAtpFiles(resolveCommandsDir(root))) {
    residue.push(path.join(resolveCommandsDir(root), leftover));
  }
  const atpDir = resolveAtpDir(root);
  if (fs.existsSync(atpDir)) {
    residue.push(atpDir);
  }

  if (residue.length > 0) {
    return {
      exitCode: 4,
      errors: ['불완전 제거 — 잔여 파일/디렉토리:', ...residue],
      messages: [...messages],
    };
  }

  messages.push('제거 완료: ' + deletedCount + '개 파일 삭제, scope=' + opts.scope + ', root=' + root);

  return {
    exitCode: errors.length > 0 ? 1 : 0,
    messages,
    errors,
  };
}
