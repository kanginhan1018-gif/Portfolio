import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

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
  assert.match(page('index.html'), /Template: Case Study Title/);
});

test('about page renders and hides empty contact links', () => {
  const html = page('about/index.html');
  assert.match(html, /<h1>About<\/h1>/);
  assert.doesNotMatch(html, /href="mailto:"/);
});
