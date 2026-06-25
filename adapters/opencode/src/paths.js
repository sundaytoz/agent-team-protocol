import fs from 'fs';
import path from 'path';
import os from 'os';

/**
 * Resolve the installation root directory for the given scope.
 * @param {'global'|'project'} scope
 * @returns {string} absolute path
 */
export function resolveScopeRoot(scope) {
  if (scope === 'global') {
    return path.join(os.homedir(), '.config', 'opencode');
  }
  if (scope === 'project') {
    return path.join(process.cwd(), '.opencode');
  }
  throw new Error(`Unknown scope: "${scope}". Expected "global" or "project".`);
}

/**
 * @param {string} root
 * @returns {string}
 */
export function resolveAgentsDir(root) {
  return path.join(root, 'agents');
}

/**
 * @param {string} root
 * @returns {string}
 */
export function resolveCommandsDir(root) {
  return path.join(root, 'commands');
}

/**
 * @param {string} root
 * @returns {string}
 */
export function resolveAtpDocsDir(root) {
  return path.join(root, 'atp', 'docs');
}

/**
 * @param {string} root
 * @returns {string}
 */
export function resolveAtpTemplatesDir(root) {
  return path.join(root, 'atp', 'templates');
}

/**
 * @param {string} root
 * @returns {string}
 */
export function resolveManifestPath(root) {
  return path.join(root, '.atp-opencode-manifest.json');
}

/**
 * @param {string} root
 * @returns {string}
 */
export function resolveAtpDir(root) {
  return path.join(root, 'atp');
}

/**
 * Resolve the root of the canonical plugins/ tree.
 * Prefers the vendor bundle (npm-installed) over the repo-local path.
 *
 * @param {string} fromDir  absolute dir of the calling module (__dirname)
 * @returns {string}        absolute path to the plugins/ root
 */
export function resolveCanonicalPluginsRoot(fromDir) {
  // 번들 사본 우선 (npm 설치 후 node_modules/@atp/opencode/vendor/plugins)
  const bundled = path.resolve(fromDir, '..', 'vendor', 'plugins');
  if (fs.existsSync(path.join(bundled, 'atp', 'agents'))) {
    return bundled;
  }
  // 레포 로컬 폴백 (self-dogfooding: adapters/opencode/src → ../../.. = repo root)
  return path.resolve(fromDir, '..', '..', '..', 'plugins');
}
