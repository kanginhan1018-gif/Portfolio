import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const page = (p) => readFileSync(new URL(`../dist/${p}`, import.meta.url), 'utf8');

test('internal links respect BASE_PATH=/demo', () => {
  for (const p of ['index.html', 'activities/index.html', 'activities/cflp-network-design/index.html', 'activities/oibc-solar-portfolio/index.html', 'projects/index.html', 'projects/cflp-network-design/index.html', 'about/index.html']) {
    const hrefs = [...page(p).matchAll(/href="(\/[^"]*)"/g)].map((m) => m[1]);
    assert.ok(hrefs.length > 0, p);
    for (const h of hrefs) assert.ok(h.startsWith('/demo/'), `${p}: ${h}`);
  }
});
