import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { niceTicks, logTicks, gapChart, timeChart, tradeoffChart } from '../src/lib/chart.ts';

test('niceTicks rounds to a 1/2/5 step', () => {
  assert.deepEqual(niceTicks(0, 97, 5), [0, 20, 40, 60, 80, 100]);
  assert.deepEqual(niceTicks(0, 0.5, 5), [0, 0.1, 0.2, 0.3, 0.4, 0.5]);
  assert.deepEqual(niceTicks(3, 3, 5), [3, 3.2, 3.4, 3.6, 3.8, 4]);
});

test('logTicks covers the range with powers of ten', () => {
  assert.deepEqual(logTicks(0.14, 219), [0.1, 1, 10, 100, 1000]);
});

test('built case study has three svg charts, each with tooltips', () => {
  const html = readFileSync(new URL('../dist/projects/cflp-network-design/index.html', import.meta.url), 'utf8');
  const svgs = html.match(/<svg[\s\S]*?<\/svg>/g) ?? [];
  const charts = svgs.filter((s) => s.includes('class="chart"'));
  assert.equal(charts.length, 3);
  for (const s of charts) {
    assert.match(s, /<title>/);
    assert.match(s, /role="img" aria-label="[^"]+"/);
  }
});

test('empty or single-point data renders axes and "no data"', () => {
  const one = { n_demand: 1, n_candidates: 1, form: 'A', status: 'optimal', gap: 0, seconds: 1 };
  for (const s of [gapChart([]), timeChart([], 120), timeChart([one], 120), tradeoffChart([]), tradeoffChart([{ k_open_forced: 3, obj: 10 }])]) {
    assert.match(s, /<svg/);
    assert.match(s, /no data/);
    assert.match(s, /class="axis"/);
  }
});
