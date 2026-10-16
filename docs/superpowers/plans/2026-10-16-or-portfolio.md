# OR Portfolio Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an English-language static portfolio site (Home, Projects list + filter, project case-study page, About) with one template case study, ready to deploy on GitHub Pages.

**Architecture:** Astro static site. One content collection `projects` (Markdown files + Zod-validated frontmatter) drives the list, filter and detail pages. Math via remark-math + rehype-katex. Tests are stdlib `node:test` files that read the built `dist/` HTML.

**Tech Stack:** Astro ^6.3.1 (pinned to v6: Astro 7 swaps the default Markdown pipeline and would need `unified()` for the remark/rehype plugins), remark-math, rehype-katex, katex, Node 20+.

**Spec:** `docs/superpowers/specs/2026-10-16-or-portfolio-design.md`

## Global Constraints

- English-only copy.
- Static output only: no backend, auth, blog, comments, i18n, interactive demos.
- Content is `.md` only (no MDX; add `@astrojs/mdx` when a project needs components).
- Project frontmatter keys exactly: `title`, `domain`, `data_source`, `methods`, `solver`, `tags`, `repo`, `date`.
- Dark mode via `prefers-color-scheme`; layout works at 375px width without horizontal page scroll.
- Every internal link goes through `url()` so the site works under a GitHub Pages sub-path (`BASE_PATH`).
- Repo lives at `~/Developer/or-portfolio`, separate from the Instagram project.

## Review Focus

- Served under a sub-path (`BASE_PATH=/demo`): every internal link must start with `/demo/`. (Task 4 `tests/base.test.mjs`)
- A project with missing/invalid frontmatter: build must fail loudly, not publish a broken page. (Task 4 `tests/edge.test.mjs`)
- Zero projects: Projects page shows an empty state and Home does not crash. (Task 4 `tests/edge.test.mjs`)
- Long display equations on a phone: scroll inside the equation, not the page. (`.katex-display` CSS in Task 1, browser check in Task 4)
- Tags/domains containing spaces or capitals ("Supply Chain"): filter buttons still work. (Task 2 test checks `data-tags` uses `|` separator)

---

### Task 1: Scaffold, layout, home page

**Files:**
- Create: `package.json`, `astro.config.mjs`, `tsconfig.json`, `.gitignore`
- Create: `src/site.ts`, `src/lib/url.ts`, `src/layouts/Base.astro`, `src/styles/global.css`
- Create: `src/components/TShape.astro`, `src/pages/index.astro`
- Test: `tests/site.test.mjs`

**Interfaces:**
- Produces: `url(path: string): string` in `src/lib/url.ts` (prefixes `BASE_URL`); `SITE` in `src/site.ts` (`{ name, tagline, email, github }`); `Base.astro` props `{ title: string; description?: string }`.

- [ ] **Step 1: Create the project files**

`package.json`:
```json
{
  "name": "or-portfolio",
  "type": "module",
  "private": true,
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "test": "astro build && node --test tests/site.test.mjs",
    "test:base": "BASE_PATH=/demo astro build && BASE_PATH=/demo node --test tests/base.test.mjs",
    "test:edge": "node --test tests/edge.test.mjs"
  },
  "dependencies": {
    "astro": "^6.3.1",
    "katex": "^0.16.11",
    "rehype-katex": "^7.0.1",
    "remark-math": "^6.0.0"
  }
}
```

`astro.config.mjs`:
```js
import { defineConfig } from 'astro/config';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

export default defineConfig({
  site: process.env.SITE_URL,
  base: process.env.BASE_PATH ?? '/',
  markdown: { remarkPlugins: [remarkMath], rehypePlugins: [rehypeKatex] },
});
```

`tsconfig.json`:
```json
{ "extends": "astro/tsconfigs/strict", "include": [".astro/types.d.ts", "**/*"], "exclude": ["dist"] }
```

`.gitignore`:
```
node_modules
dist
.astro
```

Run: `cd ~/Developer/or-portfolio && npm install`
Expected: installs without errors; `package-lock.json` created.

- [ ] **Step 2: Write the failing test**

`tests/site.test.mjs`:
```js
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `npm test`
Expected: FAIL (build error: no pages / `dist/index.html` missing).

- [ ] **Step 4: Implement**

`src/site.ts`:
```ts
// Edit these; they feed the header, home page and About page.
export const SITE = {
  name: 'Inhan',
  tagline: 'Operations research, grounded in real data.',
  email: '',
  github: '',
};
```

`src/lib/url.ts`:
```ts
export const url = (p: string) => import.meta.env.BASE_URL.replace(/\/$/, '') + p;
```

`src/layouts/Base.astro`:
```astro
---
import 'katex/dist/katex.min.css';
import '../styles/global.css';
import { SITE } from '../site';
import { url } from '../lib/url';
const { title, description = SITE.tagline } = Astro.props;
---
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content={description} />
    <title>{title} · {SITE.name}</title>
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href={url('/')}>{SITE.name}</a>
      <nav>
        <a href={url('/projects/')}>Projects</a>
        <a href={url('/about/')}>About</a>
      </nav>
    </header>
    <main><slot /></main>
    <footer class="site-footer">© {new Date().getFullYear()} {SITE.name}</footer>
  </body>
</html>
```

`src/styles/global.css`:
```css
:root {
  --bg: #fafaf9; --fg: #1c1917; --muted: #57534e; --line: #e7e5e4; --accent: #1d4ed8; --card: #ffffff;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #0c0a09; --fg: #f5f5f4; --muted: #a8a29e; --line: #292524; --accent: #93c5fd; --card: #1c1917; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 17px/1.65 system-ui, -apple-system, 'Segoe UI', sans-serif; }
main, .site-header, .site-footer { max-width: 760px; margin: 0 auto; padding: 0 16px; }
main { padding-top: 32px; padding-bottom: 64px; }
.site-header { display: flex; justify-content: space-between; align-items: center; padding-top: 20px; padding-bottom: 20px; border-bottom: 1px solid var(--line); }
.site-header nav { display: flex; gap: 20px; }
.brand { font-weight: 700; color: var(--fg); text-decoration: none; }
a { color: var(--accent); }
h1, h2, h3 { line-height: 1.25; }
.site-footer { color: var(--muted); font-size: 14px; padding-top: 24px; padding-bottom: 32px; border-top: 1px solid var(--line); }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 16px; }
.muted { color: var(--muted); }
.chip { display: inline-block; font-size: 13px; padding: 2px 10px; border: 1px solid var(--line); border-radius: 999px; margin: 0 6px 6px 0; background: transparent; color: var(--fg); }
button.chip { cursor: pointer; font-family: inherit; }
button.chip[aria-pressed='true'] { background: var(--accent); color: var(--bg); border-color: var(--accent); }
.katex-display { overflow-x: auto; overflow-y: hidden; padding: 4px 0; }
pre { overflow-x: auto; padding: 12px; border-radius: 8px; }
table { border-collapse: collapse; width: 100%; }
td, th { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
ul.plain { list-style: none; padding: 0; display: grid; gap: 12px; }
```

`src/components/TShape.astro`:
```astro
---
const breadth = ['Data analysis', 'Machine learning', 'Engineering', 'Communication'];
---
<figure class="tshape">
  <svg viewBox="0 0 320 220" role="img" aria-label="T-shaped skill model: broad bar on top, deep stem below">
    <rect x="10" y="10" width="300" height="50" rx="8" fill="none" stroke="currentColor" opacity="0.5" />
    <rect x="120" y="60" width="80" height="150" rx="8" fill="currentColor" opacity="0.85" />
    <text x="160" y="40" text-anchor="middle" font-size="14" fill="currentColor">Breadth</text>
    <text x="160" y="140" text-anchor="middle" font-size="13" fill="var(--bg)">Depth</text>
  </svg>
  <figcaption>
    <p><strong>Depth:</strong> Mathematical optimization (LP, MIP, stochastic, decomposition).</p>
    <p><strong>Breadth:</strong> {breadth.join(' · ')}.</p>
  </figcaption>
</figure>
<style>
  .tshape svg { width: 100%; max-width: 320px; display: block; margin: 0 auto; color: var(--fg); }
  .tshape figcaption { margin-top: 12px; }
  .tshape p { margin: 4px 0; }
</style>
```

`src/pages/index.astro`:
```astro
---
import Base from '../layouts/Base.astro';
import TShape from '../components/TShape.astro';
import { SITE } from '../site';
import { url } from '../lib/url';
---
<Base title="Home">
  <h1>{SITE.tagline}</h1>
  <p>
    I am building a T-shaped profile: deep in mathematical optimization, broad across data analysis,
    machine learning and engineering. Each project below starts from a real public dataset and ends
    with a model that makes a decision.
  </p>
  <TShape />
  <p><a href={url('/projects/')}>See the projects →</a></p>
</Base>
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npm test`
Expected: PASS (the build only needs `index.astro` for now; `/about/` link is just an href).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: scaffold Astro site with layout, theme and home page" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Projects collection, list with filter, detail page, template case study

**Files:**
- Create: `src/content.config.ts`, `src/content/projects/template-case-study.md`
- Create: `src/pages/projects/index.astro`, `src/pages/projects/[id].astro`
- Modify: `src/pages/index.astro` (latest projects section)
- Modify: `tests/site.test.mjs` (append tests)

**Interfaces:**
- Consumes: `Base.astro`, `url()` from Task 1.
- Produces: collection `projects` with data `{ title: string; domain: string; data_source: { name: string; url: string; license: string }; methods: string[]; solver: string; tags: string[]; repo: string (url); date: Date }`; routes `/projects/` and `/projects/<id>/`.

- [ ] **Step 1: Append the failing tests**

Append to `tests/site.test.mjs`:
```js
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL (`dist/projects/index.html` missing).

- [ ] **Step 3: Implement**

`src/content.config.ts`:
```ts
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const projects = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/projects' }),
  schema: z.object({
    title: z.string(),
    domain: z.string(),
    data_source: z.object({ name: z.string(), url: z.string().url(), license: z.string() }),
    methods: z.array(z.string()).min(1),
    solver: z.string(),
    tags: z.array(z.string()),
    repo: z.string().url(),
    date: z.coerce.date(),
  }),
});

export const collections = { projects };
```

`src/content/projects/template-case-study.md`:
```md
---
title: "Template: Case Study Title"
domain: "Supply chain"
data_source:
  name: "Kaggle: dataset name"
  url: "https://www.kaggle.com/datasets"
  license: "CC0 / check the dataset page"
methods: ["MIP", "Forecasting"]
solver: "HiGHS via Pyomo"
tags: ["template", "inventory"]
repo: "https://github.com/"
date: 2026-10-16
---

Copy this file, rename it, and replace every section. Delete this line.

## 1. Business problem

Who decides what, how often, and what does a bad decision cost? One paragraph, in the decision-maker's words.

## 2. Data

Source, link, license, row counts, and what you had to clean. State which columns become parameters of the model.

## 3. EDA

Three to five plots that change a modeling choice (not decoration). Say what each one changed.

## 4. Prediction / forecasting

Only if the optimization needs a forecast. Report the error metric and how forecast error flows into the model.

## 5. Optimization model

Decision variables, objective, constraints. For example:

$$
\min_{x,\,y}\ \sum_{t=1}^{T}\left(c\,x_t + h\,I_t\right)
\quad\text{s.t.}\quad I_t = I_{t-1} + x_t - d_t,\ \ x_t \le M\,y_t,\ \ x_t, I_t \ge 0,\ y_t \in \{0,1\}.
$$

Inline math works too: $I_t$ is end-of-period inventory. Name the solver, the model size and the solve time.

## 6. Results & sensitivity

Compare against a baseline policy. Show how the answer moves when the key parameter changes by ±20%.

## 7. Limitations

What the model ignores, where the data is thin, and what would change your recommendation.

## 8. Reproduce

Link the repository, the environment file, and the single command that regenerates the results.
```

`src/pages/projects/index.astro`:
```astro
---
import { getCollection } from 'astro:content';
import Base from '../../layouts/Base.astro';
import { url } from '../../lib/url';

const projects = (await getCollection('projects')).sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
const labels = (p: (typeof projects)[number]) => [p.data.domain, ...p.data.methods, ...p.data.tags];
const allTags = [...new Set(projects.flatMap(labels))].sort((a, b) => a.localeCompare(b));
---
<Base title="Projects">
  <h1>Projects</h1>
  {projects.length === 0 ? (
    <p class="muted">No projects yet.</p>
  ) : (
    <>
      <div class="filters" aria-label="Filter by tag">
        {allTags.map((t) => <button type="button" class="chip" data-tag={t} aria-pressed="false">{t}</button>)}
      </div>
      <ul class="plain">
        {projects.map((p) => (
          <li class="card" data-tags={labels(p).join('|')}>
            <h2 style="margin:0 0 4px"><a href={url(`/projects/${p.id}/`)}>{p.data.title}</a></h2>
            <p class="muted" style="margin:0 0 8px">{p.data.domain} · {p.data.methods.join(', ')} · {p.data.date.getFullYear()}</p>
            {labels(p).map((t) => <span class="chip">{t}</span>)}
          </li>
        ))}
      </ul>
    </>
  )}
</Base>

<script>
  const buttons = document.querySelectorAll<HTMLButtonElement>('button[data-tag]');
  const items = document.querySelectorAll<HTMLElement>('li[data-tags]');
  let active: string | null = null;
  buttons.forEach((b) =>
    b.addEventListener('click', () => {
      active = active === b.dataset.tag ? null : (b.dataset.tag ?? null);
      buttons.forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.tag === active)));
      items.forEach((li) => {
        li.hidden = active !== null && !li.dataset.tags!.split('|').includes(active);
      });
    }),
  );
</script>
```

`src/pages/projects/[id].astro`:
```astro
---
import { getCollection, render } from 'astro:content';
import Base from '../../layouts/Base.astro';
import { url } from '../../lib/url';

export async function getStaticPaths() {
  const projects = await getCollection('projects');
  return projects.map((p) => ({ params: { id: p.id }, props: { p } }));
}
const { p } = Astro.props;
const { Content } = await render(p);
const d = p.data;
---
<Base title={d.title} description={`${d.domain}: ${d.methods.join(', ')}`}>
  <p><a href={url('/projects/')}>← All projects</a></p>
  <h1>{d.title}</h1>
  <table>
    <tbody>
      <tr><th>Domain</th><td>{d.domain}</td></tr>
      <tr><th>Data</th><td><a href={d.data_source.url}>{d.data_source.name}</a> ({d.data_source.license})</td></tr>
      <tr><th>Methods</th><td>{d.methods.join(', ')}</td></tr>
      <tr><th>Solver</th><td>{d.solver}</td></tr>
      <tr><th>Code</th><td><a href={d.repo}>{d.repo}</a></td></tr>
      <tr><th>Date</th><td>{d.date.toISOString().slice(0, 10)}</td></tr>
    </tbody>
  </table>
  <article><Content /></article>
</Base>
```

Modify `src/pages/index.astro`: replace the frontmatter and add a section before the closing `</Base>`.

Frontmatter becomes:
```astro
---
import { getCollection } from 'astro:content';
import Base from '../layouts/Base.astro';
import TShape from '../components/TShape.astro';
import { SITE } from '../site';
import { url } from '../lib/url';
const latest = (await getCollection('projects')).sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf()).slice(0, 3);
---
```
Replace `<p><a href={url('/projects/')}>See the projects →</a></p>` with:
```astro
  <h2>Latest projects</h2>
  {latest.length === 0 ? <p class="muted">Coming soon.</p> : (
    <ul class="plain">
      {latest.map((p) => (
        <li class="card"><a href={url(`/projects/${p.id}/`)}>{p.data.title}</a>
          <span class="muted"> · {p.data.domain}</span></li>
      ))}
    </ul>
  )}
  <p><a href={url('/projects/')}>All projects →</a></p>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS, all four tests.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: projects collection, list with tag filter, case-study page and template" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: About page

**Files:**
- Create: `src/pages/about.astro`
- Modify: `tests/site.test.mjs` (append test)

**Interfaces:**
- Consumes: `SITE` (`email`, `github` render only when non-empty), `Base.astro`.

- [ ] **Step 1: Append the failing test**

```js
test('about page renders and hides empty contact links', () => {
  const html = page('about/index.html');
  assert.match(html, /<h1>About<\/h1>/);
  assert.doesNotMatch(html, /href="mailto:"/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL (`dist/about/index.html` missing).

- [ ] **Step 3: Implement**

`src/pages/about.astro`:
```astro
---
import Base from '../layouts/Base.astro';
import { SITE } from '../site';
---
<Base title="About">
  <h1>About</h1>
  <p>
    I study operations research and use public datasets to practice the full loop:
    frame the decision, analyze the data, build the model, and test how robust the answer is.
  </p>
  <h2>Skills</h2>
  <ul>
    <li><strong>Depth:</strong> linear / mixed-integer / stochastic optimization, decomposition, solver modeling.</li>
    <li><strong>Breadth:</strong> data analysis, forecasting and ML, Python tooling, clear technical writing.</li>
  </ul>
  <h2>Contact</h2>
  <p>
    {SITE.email && <a href={`mailto:${SITE.email}`}>{SITE.email}</a>}
    {SITE.github && <> · <a href={SITE.github}>GitHub</a></>}
    {!SITE.email && !SITE.github && <span class="muted">Add your contact links in <code>src/site.ts</code>.</span>}
  </p>
</Base>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS, five tests.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: about page" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Base-path and edge-case tests, deploy workflow, README, browser check

**Files:**
- Create: `tests/base.test.mjs`, `tests/edge.test.mjs`
- Create: `.github/workflows/deploy.yml`, `README.md`

**Interfaces:**
- Consumes: everything above; env vars `SITE_URL`, `BASE_PATH` read by `astro.config.mjs`.

- [ ] **Step 1: Write the base-path test**

`tests/base.test.mjs`:
```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const page = (p) => readFileSync(new URL(`../dist/${p}`, import.meta.url), 'utf8');

test('internal links respect BASE_PATH=/demo', () => {
  for (const p of ['index.html', 'projects/index.html', 'projects/template-case-study/index.html', 'about/index.html']) {
    const hrefs = [...page(p).matchAll(/href="(\/[^"]*)"/g)].map((m) => m[1]);
    assert.ok(hrefs.length > 0, p);
    for (const h of hrefs) assert.ok(h.startsWith('/demo/'), `${p}: ${h}`);
  }
});
```

- [ ] **Step 2: Run it**

Run: `npm run test:base`
Expected: PASS. If it fails, a link bypasses `url()` (Astro's own asset links already include the base); fix that link.

- [ ] **Step 3: Write the edge-case test**

`tests/edge.test.mjs`:
```js
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
```

- [ ] **Step 4: Run it**

Run: `npm run test:edge && npm test`
Expected: PASS for both; afterwards `ls src/content/projects` shows only `template-case-study.md` (the final `npm test` rebuilds with it).

- [ ] **Step 5: Deploy workflow and README**

`.github/workflows/deploy.yml`:
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: withastro/action@v6
        env:
          SITE_URL: https://${{ github.repository_owner }}.github.io
          BASE_PATH: /${{ github.event.repository.name }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v5
```

`README.md`:
```md
# OR Portfolio

Static portfolio for operations-research case studies (Astro).

- Develop: `npm install && npm run dev`
- Test: `npm test` (build + page checks), `npm run test:base`, `npm run test:edge`
- Add a project: copy `src/content/projects/template-case-study.md`, change the filename and frontmatter, rewrite the 8 sections.
- Edit name/contact: `src/site.ts`.
- Deploy: push to `main` on GitHub, then Settings → Pages → Source: GitHub Actions. If the repo is named `<user>.github.io`, delete the `BASE_PATH` line in the workflow.
```

- [ ] **Step 6: Browser check (manual, headless via chrome-devtools)**

Run: `npm run build && npx astro preview --port 4321` (background). Open `http://localhost:4321/projects/template-case-study/` at 375px width in light and dark emulation.
Expected: no console errors; `document.documentElement.scrollWidth <= window.innerWidth`; the display equation scrolls inside its own box; clicking a tag button on `/projects/` toggles `aria-pressed` and hides non-matching cards. Stop the preview server afterwards.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "test+ci: base-path and edge-case tests, Pages workflow, README" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```
