#!/usr/bin/env node
// docs-check: fails when a repo's agent map lies. Canon copy lives in
// sampu-codex/standards/agents-md/; each repo carries it at .github/docs-check.mjs (CI: docs-check.yml).
// Checks, from the repo root:
//   1. AGENTS.md exists and CLAUDE.md is the @AGENTS.md shim (Claude Code skips AGENTS.md otherwise).
//   2. The sampu-canon block is present (its text is checked against canon by sync-canon-block.mjs --check),
//      and the SAMPU_DNA.md it points at is tracked.
//   3. Every path named in backticks in AGENTS.md matches a tracked file or directory.
//   4. Every `npm run <script>` named in AGENTS.md exists in some package.json at depth <= 2.
//   5. No CONTEXT.md / CONTEXT-MAP.md pointer (Pocock 1.3.0 renamed them GLOSSARY.md / GLOSSARY-MAP.md).
// Warns (never fails) when AGENTS.md passes 200 lines.
// usage: node docs-check.mjs [repoRoot]
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { execSync } from 'node:child_process';

const root = process.argv[2] || process.cwd();
const errors = [];
const warnings = [];
const read = f => readFileSync(join(root, f), 'utf8').replace(/\r\n/g, '\n');

if (!existsSync(join(root, 'AGENTS.md'))) {
  console.log('docs-check: FAIL\n  AGENTS.md missing (template: sampu-codex standards/templates/repo-agents-md.md)');
  process.exit(1);
}
const agents = read('AGENTS.md');
const lines = agents.split('\n');

if (!existsSync(join(root, 'CLAUDE.md')) || read('CLAUDE.md').split('\n')[0].trim() !== '@AGENTS.md')
  errors.push('CLAUDE.md must start with the line @AGENTS.md (Claude Code does not read AGENTS.md on its own here)');

if (!agents.includes('<!-- BEGIN:sampu-canon') || !agents.includes('<!-- END:sampu-canon -->'))
  errors.push('sampu-canon block missing (run sampu-codex standards/agents-md/sync-canon-block.mjs AGENTS.md)');

// The canon block promises the full DNA at the repo root; a local-only copy reaches no clone.
if (agents.includes('<!-- BEGIN:sampu-canon') && !execSync('git ls-files SAMPU_DNA.md', { cwd: root, encoding: 'utf8' }).trim())
  errors.push('SAMPU_DNA.md is not tracked; commit the canon copy (cp from sampu-codex) so clones and other agents get it');

// Paths: backticked tokens that look like a file or directory, resolved against the TRACKED tree
// (what CI and a fresh clone see): a token matches when some tracked path equals it or ends with it.
// Skipped: generated marker blocks (BEGIN:/END:), cross-repo and machine lines, ../ and /url paths,
// bare extensions, and tokens listed one per line in .github/docs-check-ignore.
const tracked = execSync('git ls-files', { cwd: root, encoding: 'utf8', maxBuffer: 64 << 20 }).split('\n').filter(Boolean);
const dirs = new Set(tracked.flatMap(f => f.split('/').slice(0, -1).map((_, i, a) => a.slice(0, i + 1).join('/') + '/')));
const exists = tok => {
  const t = tok.replace(/^\.\//, '');
  if (t.endsWith('/')) return [...dirs].some(d => d === t || d.endsWith('/' + t));
  return tracked.some(f => f === t || f.endsWith('/' + t));
};
const ignorePath = join(root, '.github', 'docs-check-ignore');
const ignored = new Set(existsSync(ignorePath) ? readFileSync(ignorePath, 'utf8').split(/\r?\n/).map(s => s.trim()).filter(s => s && !s.startsWith('#')) : []);
const PATHLIKE = /^(\.\/)?[\w@-][\w.@-]*(\/[\w.@-]+)*\/?$/;
const EXT = /\.(md|mdx|ts|tsx|js|mjs|cjs|json|jsonc|sql|ya?ml|toml|ps1|sh|py|java|kt|css|html)$/;
let inBlock = false;
lines.forEach((line, i) => {
  if (/<!-- BEGIN:/.test(line)) inBlock = true;
  if (/<!-- END:/.test(line)) { inBlock = false; return; }
  if (inBlock || /sampu-codex|~\/|https?:\/\//.test(line)) return;
  for (const [, tok] of line.matchAll(/`([^`\s]+)`/g)) {
    if (!PATHLIKE.test(tok) || !(EXT.test(tok) || (tok.endsWith('/') && tok.length > 2))) continue;
    if (/^(node_modules|dist|build|\.next|coverage)\//.test(tok) || ignored.has(tok)) continue;
    if (!exists(tok)) errors.push(`AGENTS.md:${i + 1} names \`${tok}\`, which no tracked file matches`);
  }
});

// npm scripts named in AGENTS.md.
const scripts = new Set();
const walk = (dir, depth) => {
  for (const e of readdirSync(dir)) {
    if (e === 'node_modules' || e.startsWith('.')) continue;
    const p = join(dir, e);
    if (e === 'package.json') { try { Object.keys(JSON.parse(readFileSync(p, 'utf8')).scripts || {}).forEach(s => scripts.add(s)); } catch {} }
    else if (depth < 2 && statSync(p).isDirectory()) walk(p, depth + 1);
  }
};
walk(root, 0);
lines.forEach((line, i) => {
  for (const [, s] of line.matchAll(/npm run ([\w:.-]+)/g))
    if (!scripts.has(s)) errors.push(`AGENTS.md:${i + 1} names \`npm run ${s}\`, but no package.json defines "${s}"`);
});

lines.forEach((line, i) => {
  if (/(?<![A-Za-z_-])CONTEXT(-MAP)?\.md/.test(line) && !/GLOSSARY/.test(line))
    errors.push(`AGENTS.md:${i + 1} points at CONTEXT.md; the convention is GLOSSARY.md since Pocock skills 1.3.0`);
});

if (lines.length > 200) warnings.push(`AGENTS.md is ${lines.length} lines; aim under 200 and push depth into docs/ behind pointers`);

for (const w of warnings) console.log(`  warn: ${w}`);
if (errors.length) { console.log(`docs-check: FAIL (${errors.length})`); for (const e of errors) console.log(`  ${e}`); process.exit(1); }
console.log('docs-check: ok');
