#!/usr/bin/env node
// scripts/bundle-canonical.js
// prepack 시 canonical plugins/ 소스를 vendor/ 로 복사한다.
// npm publish / npm pack 이 자동 호출. 직접 실행: node scripts/bundle-canonical.js
// vendor/ 는 .gitignore 대상 (빌드 산출물). canonical 단일 소스 = plugins/** (ADR-0014 D3).

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url)); // adapters/opencode/scripts
const PKG_ROOT = path.resolve(__dirname, '..'); //                adapters/opencode/
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..'); //   repo root
const VENDOR_DIR = path.join(PKG_ROOT, 'vendor'); //             번들 출력 루트

// src: 레포루트 기준, dest: vendor/ 기준. 디렉토리=재귀 복사, 파일=단일 복사.
// 이 목록은 plan.js / install.js 의 CANONICAL_* 상수 7개와 1:1 대응해야 한다.
const COPY_TARGETS = [
  { src: 'plugins/atp/agents', dest: 'plugins/atp/agents', recursive: true },
  { src: 'plugins/atp-graphify/agents', dest: 'plugins/atp-graphify/agents', recursive: true },
  { src: 'plugins/atp/skills', dest: 'plugins/atp/skills', recursive: true },
  { src: 'plugins/atp/docs', dest: 'plugins/atp/docs', recursive: true },
  { src: 'plugins/atp-graphify/docs/graphify-usage.md', dest: 'plugins/atp-graphify/docs/graphify-usage.md', recursive: false },
  { src: 'plugins/atp/templates', dest: 'plugins/atp/templates', recursive: true },
  { src: 'plugins/atp/.claude-plugin/plugin.json', dest: 'plugins/atp/.claude-plugin/plugin.json', recursive: false },
];

// vendor/ 초기화 (멱등 보장 — 재실행 시 stale 잔여 제거)
if (fs.existsSync(VENDOR_DIR)) {
  fs.rmSync(VENDOR_DIR, { recursive: true, force: true });
}

let copied = 0;
const missing = [];
for (const { src, dest, recursive } of COPY_TARGETS) {
  const srcAbs = path.join(REPO_ROOT, src);
  const destAbs = path.join(VENDOR_DIR, dest);
  if (!fs.existsSync(srcAbs)) {
    missing.push(src);
    continue;
  }
  fs.mkdirSync(path.dirname(destAbs), { recursive: true });
  if (recursive) {
    fs.cpSync(srcAbs, destAbs, { recursive: true });
  } else {
    fs.copyFileSync(srcAbs, destAbs);
  }
  copied++;
}

if (missing.length > 0) {
  // canonical 소스 누락은 publish 블로커 — 비정상 종료로 prepack 을 멈춘다.
  console.error(`[bundle-canonical] 오류: canonical 소스 ${missing.length}개 누락:`);
  for (const m of missing) console.error(`  - ${m}`);
  process.exit(1);
}

console.log(`[bundle-canonical] vendor/ 생성 완료 (${copied}/${COPY_TARGETS.length} 대상): ${VENDOR_DIR}`);
