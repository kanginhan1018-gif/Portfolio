import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const read = (p) => readFileSync(new URL(`../src/content/${p}/cflp-network-design.md`, import.meta.url), 'utf8');
const split = (s) => {
  const m = s.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  const fm = {};
  let key = null;
  for (const line of m[1].split('\n')) {
    const top = line.match(/^(\w+):\s*(.*)$/);
    if (top) fm[(key = top[1])] = top[2];
    else if (key) fm[key] += `\n${line}`; // nested (data_source) lines belong to the last top-level key
  }
  return { fm, body: m[2] };
};
const en = split(read('projects'));
const ko = split(read('projects-ko'));

// integers, thousands separators, decimals, percentages, scientific notation, plus × and ≤
const NUM = /\d+(?:,\d{3})*(?:\.\d+)*(?:e-?\d+)?%?|×|≤/g;
const sorted = (a) => [...a].sort();
const all = (s, re) => s.match(re) ?? [];

test('numeric tokens are the same multiset', () => {
  assert.deepEqual(sorted(all(ko.body, NUM)), sorted(all(en.body, NUM)));
});

test('$$ display math blocks are byte-identical and in order', () => {
  const blocks = (s) => all(s, /\$\$[\s\S]*?\$\$/g);
  assert.ok(blocks(en.body).length > 0);
  assert.deepEqual(blocks(ko.body), blocks(en.body));
});

test('same set of URLs', () => {
  const urls = (s) => new Set(all(s, /https?:\/\/[^\s)"]+/g));
  assert.deepEqual(urls(ko.body), urls(en.body));
});

test('same number of ## headings, numbering kept', () => {
  const h = (s) => all(s, /^## (\d+)\./gm);
  assert.equal(all(ko.body, /^## /gm).length, all(en.body, /^## /gm).length);
  assert.deepEqual(h(ko.body), h(en.body));
});

test('shared frontmatter fields are not overridden by the ko entry', () => {
  // ko holds only translated fields; shared ones come from the English entry (single source of truth).
  for (const k of ['data_source', 'solver', 'repo', 'date', 'charts']) {
    assert.ok(k in en.fm, `en has ${k}`);
    if (k in ko.fm) assert.equal(ko.fm[k], en.fm[k], k);
  }
});

test('ko methods/tags line up 1:1 with en (filter chips map by position)', () => {
  const arr = (fm, k) => JSON.parse(fm[k]);
  for (const k of ['methods', 'tags']) assert.equal(arr(ko.fm, k).length, arr(en.fm, k).length, k);
  for (const k of ['title', 'domain']) assert.ok(ko.fm[k], k);
});
