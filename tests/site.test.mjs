import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';

const page = (p) => readFileSync(new URL(`../dist/${p}`, import.meta.url), 'utf8');

test('home has T-shape graphic and nav', () => {
  const html = page('index.html');
  assert.match(html, /T-shaped/);
  assert.match(html, /Mathematical optimization/);
  for (const href of ['/projects/', '/about/']) assert.ok(html.includes(`href="${href}"`), href);
});

test('projects list renders template with pipe-separated filter data', () => {
  const html = page('projects/index.html');
  assert.match(html, /Template: Case Study Title/);
  assert.match(html, /data-tags="[^"]*\|[^"]*"/);
  assert.match(html, /data-tag="Supply chain"/);
});

test('project page has all 8 sections, metadata and rendered math', () => {
  const html = page('projects/template-case-study/index.html');
  for (const h of ['Business problem', 'Data', 'EDA', 'Prediction', 'Optimization model', 'Results', 'Limitations', 'Reproduce'])
    assert.ok(html.includes(h), h);
  assert.match(html, /class="katex/);
  assert.match(html, /Solver/);
});

test('home lists latest project', () => {
  // derive the newest project from the content files (same rule as the home page: sort by date)
  const dir = new URL('../src/content/projects/', import.meta.url);
  const fm = (f, k) => readFileSync(new URL(f, dir), 'utf8').match(new RegExp(`^${k}:\\s*"?(.*?)"?\\s*$`, 'm'))[1];
  const latest = readdirSync(dir).filter((f) => f.endsWith('.md'))
    .map((f) => ({ title: fm(f, 'title'), date: fm(f, 'date') }))
    .sort((a, b) => b.date.localeCompare(a.date))[0];
  assert.ok(page('index.html').includes(latest.title), latest.title);
});

test('about page renders and hides empty contact links', () => {
  const html = page('about/index.html');
  assert.match(html, /<h1>About<\/h1>/);
  assert.doesNotMatch(html, /href="mailto:"/);
});

test('home T section is scroll-driven and shows final state without JS', () => {
  const html = page('index.html');
  assert.match(html, /data-tscroll/);
  assert.doesNotMatch(html, /<section[^>]*data-live/);
});
