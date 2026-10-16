import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, renameSync, rmSync } from 'node:fs';

const root = new URL('..', import.meta.url).pathname;
const dir = `${root}src/content/projects/`;
const build = () => spawnSync('npx', ['astro', 'build'], { cwd: root, encoding: 'utf8' });

test('invalid frontmatter fails the build', () => {
  const bad = `${dir}zz-bad.md`;
  writeFileSync(bad, '---\ntitle: "x"\n---\nbody\n');
  try {
    const r = build();
    assert.notEqual(r.status, 0);
    assert.match(r.stdout + r.stderr, /domain|data_source|zz-bad/);
  } finally {
    rmSync(bad, { force: true });
  }
});

test('zero projects: empty states, no crash', () => {
  const real = `${dir}template-case-study.md`;
  const hidden = `${root}template-case-study.md.bak`;
  renameSync(real, hidden);
  try {
    const r = build();
    assert.equal(r.status, 0, r.stdout + r.stderr);
    assert.match(readFileSync(`${root}dist/projects/index.html`, 'utf8'), /No projects yet/);
    assert.match(readFileSync(`${root}dist/index.html`, 'utf8'), /Coming soon/);
  } finally {
    renameSync(hidden, real);
  }
});
