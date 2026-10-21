import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, existsSync } from 'node:fs';

const page = (p) => readFileSync(new URL(`../dist/${p}`, import.meta.url), 'utf8');

test('home has T-shape graphic and nav', () => {
  const html = page('index.html');
  assert.match(html, /T-shaped/);
  assert.match(html, /Mathematical optimization/);
  for (const href of ['/projects/', '/about/']) assert.ok(html.includes(`href="${href}"`), href);
});

test('projects list renders with pipe-separated filter data', () => {
  const html = page('projects/index.html');
  assert.match(html, /data-tags="[^"]*\|[^"]*"/);
  assert.match(html, /data-tag="Facility location"/);
});

test('project page has all 8 sections, metadata and rendered math', () => {
  const html = page('projects/cflp-network-design/index.html');
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
    .filter((f) => !/^draft:\s*true\s*$/m.test(readFileSync(new URL(f, dir), 'utf8')))
    .map((f) => ({ title: fm(f, 'title'), date: fm(f, 'date') }))
    .sort((a, b) => b.date.localeCompare(a.date))[0];
  assert.ok(page('index.html').includes(latest.title), latest.title);
});

test('draft template is hidden everywhere', () => {
  for (const p of ['index.html', 'projects/index.html']) assert.ok(!page(p).includes('Template: Case Study Title'), p);
  assert.ok(!existsSync(new URL('../dist/projects/template-case-study', import.meta.url)));
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

test('home T is a single svg with unique ids and a settled no-JS state', () => {
  const html = page('index.html');
  const section = html.match(/<section[^>]*data-tscroll[\s\S]*?<\/section>/)[0];
  assert.equal((section.match(/<svg/g) ?? []).length, 1);
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]);
  assert.equal(new Set(ids).size, ids.length, `duplicate ids: ${ids}`);
  assert.match(section, /data-liquid d="M0 0 H360 V350 H0 Z"/);
});

test('project page ships en + ko articles, a toggle and no duplicated charts', () => {
  const html = page('projects/cflp-network-design/index.html');
  assert.match(html, /<article lang="en"/);
  assert.match(html, /<article lang="ko"/);
  for (const l of ['ko', 'en']) assert.match(html, new RegExp(`<button[^>]*data-set-lang="${l}"[^>]*aria-pressed="(true|false)"`));
  assert.match(html, /localStorage\.getItem\('lang'\)/); // pre-paint script in head
  assert.ok(html.indexOf("getItem('lang')") < html.indexOf('</head>'));
  const charts = (html.match(/<svg[^>]*class="chart"/g) ?? []).length;
  assert.equal(charts, 3);
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]);
  assert.equal(new Set(ids).size, ids.length, `duplicate ids: ${ids}`);
  // both bodies render KaTeX (formulas are shared byte-for-byte)
  const ko = html.slice(html.indexOf('<article lang="ko"'));
  assert.match(ko, /class="katex/);
});

test('projects list has a toggle and ko labels keyed by the English tag', () => {
  const html = page('projects/index.html');
  assert.match(html, /data-set-lang="ko"/);
  assert.match(html, /data-tag="Facility location"[^>]*>.*?<span data-l="ko" lang="ko">시설 입지<\/span>/);
});

test('pages without a translation get no toggle or pre-paint script', () => {
  for (const p of ['index.html', 'about/index.html']) {
    const html = page(p);
    assert.doesNotMatch(html, /data-set-lang|getItem\('lang'\)/, p);
  }
});
