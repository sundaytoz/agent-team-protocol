#!/usr/bin/env node
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';

import { runInstall } from '../src/install.js';
import { runUninstall } from '../src/uninstall.js';
import { TIER_SLUG } from '../src/mappings.js';

const HELP_TEXT = `atp-opencode — ATP agents/commands generator for opencode

Usage:
  atp-opencode install   [--global|--project] [--provider <id>] [--with-graphify] [--force] [--require-opencode]
  atp-opencode uninstall [--global|--project]
  atp-opencode --help | --version

Options:
  --global            Install to ~/.config/opencode/
  --project           Install to .opencode/ (default)
  --provider <id>     Bake model slugs for provider (e.g. amazon-bedrock)
  --with-graphify     Include graphify add-on agents
  --force             Overwrite existing files
  --require-opencode  Fail if opencode binary not found

Exit codes: 0 ok / 1 I/O error / 2 bad args / 3 opencode missing (--require-opencode) / 4 incomplete uninstall`;

function printVersion() {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const pkg = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8')
  );
  console.log(pkg.version);
}

function emit(result) {
  for (const m of result.messages ?? []) console.log(m);
  for (const e of result.errors ?? []) console.error(e);
}

function main() {
  const argv = process.argv.slice(2);

  // --help / --version take precedence regardless of position.
  if (argv.includes('--help') || argv.includes('-h')) {
    console.log(HELP_TEXT);
    process.exit(0);
  }
  if (argv.includes('--version') || argv.includes('-v')) {
    printVersion();
    process.exit(0);
  }

  const command = argv[0];

  // Flag parsing.
  let wantGlobal = false;
  let wantProject = false;
  let withGraphify = false;
  let force = false;
  let requireOpencode = false;
  let provider = null;

  for (let i = 1; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case '--global':
        wantGlobal = true;
        break;
      case '--project':
        wantProject = true;
        break;
      case '--with-graphify':
        withGraphify = true;
        break;
      case '--force':
        force = true;
        break;
      case '--require-opencode':
        requireOpencode = true;
        break;
      case '--provider': {
        const next = argv[i + 1];
        if (next === undefined) {
          console.error('--provider 값이 필요합니다');
          process.exit(2);
        }
        provider = next;
        i++; // consume the value token
        break;
      }
      default:
        // Unknown flags are tolerated (lenient parsing).
        break;
    }
  }

  // scope resolution.
  if (wantGlobal && wantProject) {
    console.error('scope 충돌: --global 과 --project 중 하나만');
    process.exit(2);
  }
  const scope = wantGlobal ? 'global' : 'project';

  // Subcommand dispatch.
  if (command === 'install') {
    if (provider !== null && !TIER_SLUG[provider]) {
      console.error(
        `미지원 provider: ${provider} (지원: ${Object.keys(TIER_SLUG).join(', ')})`
      );
      process.exit(2);
    }
    const result = runInstall({
      scope,
      provider: provider ?? null,
      withGraphify,
      force,
      requireOpencode,
    });
    emit(result);
    process.exit(result.exitCode);
  }

  if (command === 'uninstall') {
    const result = runUninstall({ scope });
    emit(result);
    process.exit(result.exitCode);
  }

  // Unknown / missing subcommand.
  console.error(`알 수 없는 명령: ${command ?? '(none)'}`);
  console.error('Usage: atp-opencode <install|uninstall> [options] | --help | --version');
  process.exit(2);
}

try {
  main();
} catch (err) {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
}
