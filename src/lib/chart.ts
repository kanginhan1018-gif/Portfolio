// Pure SVG chart builders for case-study pages. Plain TS (erasable syntax only) so node --test can import it.

export type ScalingRow = { n_demand: number; n_candidates: number; form: string; status: string; gap: number | null; seconds: number };
export type TradeoffRow = { k_open_forced: number; obj: number | null };

export function niceTicks(min: number, max: number, n: number): number[] {
  if (!(max > min)) max = min + 1;
  const raw = (max - min) / n;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const r = raw / mag;
  const step = (r <= 1 ? 1 : r <= 2 ? 2 : r <= 5 ? 5 : 10) * mag;
  const out: number[] = [];
  for (let i = Math.floor(min / step + 1e-9); i <= Math.ceil(max / step - 1e-9); i++) out.push(+(i * step).toPrecision(12));
  return out;
}

export function logTicks(min: number, max: number): number[] {
  const lo = Math.floor(Math.log10(min)), hi = Math.max(Math.ceil(Math.log10(max)), lo + 1);
  const out: number[] = [];
  for (let e = lo; e <= hi; e++) out.push(+(10 ** e).toPrecision(12));
  return out;
}

export const linear = (d0: number, d1: number, r0: number, r1: number) => (v: number) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);

const W = 640, H = 360;
const M = { l: 64, r: 64, t: 28, b: 56 };
const X0 = M.l, X1 = W - M.r, Y0 = H - M.b, Y1 = M.t;
const FORMS = ['A', 'B', 'C'];
const f2 = (v: number) => +v.toFixed(2);
const sizeLabel = (r: ScalingRow) => `${r.n_demand}×${r.n_candidates}`;
const svg = (label: string, body: string) =>
  `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${label}">${body}</svg>`;

// gridlines + y labels, x baseline, axis titles
function axes(yTicks: number[], y: (v: number) => number, fmt: (v: number) => string, xTitle: string, yTitle: string) {
  const grid = yTicks
    .map((t) => `<line class="grid" x1="${X0}" x2="${X1}" y1="${f2(y(t))}" y2="${f2(y(t))}"/><text class="tick" x="${X0 - 8}" y="${f2(y(t)) + 4}" text-anchor="end">${fmt(t)}</text>`)
    .join('');
  return `<g class="axis">${grid}<line class="base" x1="${X0}" x2="${X1}" y1="${Y0}" y2="${Y0}"/>` +
    `<text class="tick" x="${(X0 + X1) / 2}" y="${H - 8}" text-anchor="middle">${xTitle}</text>` +
    `<text class="tick" transform="translate(14 ${(Y0 + Y1) / 2}) rotate(-90)" text-anchor="middle">${yTitle}</text></g>`;
}
const noData = (xTitle: string, yTitle: string) =>
  svg(`${yTitle}: no data`, axes([0, 1], linear(0, 1, Y0, Y1), String, xTitle, yTitle) +
    `<text class="note" x="${(X0 + X1) / 2}" y="${(Y0 + Y1) / 2}" text-anchor="middle">no data</text>`);

function marker(form: string, x: number, y: number, title: string) {
  const t = `<title>${title}</title>`, c = `mark s-${form}`;
  if (form === 'B') return `<rect class="${c}" x="${f2(x - 4.5)}" y="${f2(y - 4.5)}" width="9" height="9">${t}</rect>`;
  if (form === 'C') return `<path class="${c}" d="M${f2(x)} ${f2(y - 6)}L${f2(x + 5.5)} ${f2(y + 4)}H${f2(x - 5.5)}Z">${t}</path>`;
  return `<circle class="${c}" cx="${f2(x)}" cy="${f2(y)}" r="5">${t}</circle>`;
}

function sizes(rows: ScalingRow[]) {
  return [...new Set(rows.map(sizeLabel))];
}

export function gapChart(rows: ScalingRow[]): string {
  const xT = 'instance size (demand × candidate DCs)', yT = 'final MIP gap (%)';
  rows = rows.filter((r) => r.gap != null);
  const S = sizes(rows);
  if (rows.length < 2) return noData(xT, yT);
  const pct = (r: ScalingRow) => (r.gap as number) * 100;
  const ticks = niceTicks(0, Math.max(...rows.map(pct)), 5);
  const y = linear(0, ticks[ticks.length - 1], Y0, Y1);
  const gw = (X1 - X0) / S.length, bw = gw * 0.22;
  const bars = rows.map((r) => {
    const i = S.indexOf(sizeLabel(r)), j = FORMS.indexOf(r.form);
    const x = X0 + gw * i + gw / 2 + (j - 1) * (bw + 3) - bw / 2, top = Math.min(y(pct(r)), Y0 - 1);
    const v = pct(r);
    return `<rect class="bar s-${r.form}" x="${f2(x)}" y="${f2(top)}" width="${f2(bw)}" height="${f2(Y0 - top)}"><title>${r.form}, ${sizeLabel(r)}: final gap ${v.toFixed(4)}% (${r.status}, ${r.seconds.toFixed(1)} s)</title></rect>` +
      `<text class="lbl" x="${f2(x + bw / 2)}" y="${f2(top - 5)}" text-anchor="middle">${r.form}</text>` +
      (v >= 1 ? `<text class="lbl" x="${f2(x + bw / 2)}" y="${f2(top - 20)}" text-anchor="middle">${v.toFixed(1)}%</text>` : '');
  }).join('');
  const xl = S.map((s, i) => `<text class="tick" x="${f2(X0 + gw * i + gw / 2)}" y="${Y0 + 20}" text-anchor="middle">${s}</text>`).join('');
  const worst = rows.reduce((a, b) => (pct(b) > pct(a) ? b : a));
  const rest = Math.max(...rows.filter((r) => r !== worst).map(pct));
  const label = `Grouped bar chart: final MIP gap in percent by instance size for formulations A, B and C. Largest is ${worst.form} at ${sizeLabel(worst)} with ${pct(worst).toFixed(2)}% (${worst.status}); every other run is at or below ${rest.toFixed(3)}%.`;
  return svg(label, axes(ticks, y, (t) => `${t}%`, xT, yT) + xl + bars);
}

export function timeChart(rows: ScalingRow[], limit: number): string {
  const xT = 'instance size (demand × candidate DCs)', yT = 'solve time (s, log scale)';
  const S = sizes(rows);
  if (S.length < 2) return noData(xT, yT);
  const secs = rows.map((r) => r.seconds);
  const ticks = logTicks(Math.min(...secs, limit), Math.max(...secs, limit));
  const ly = linear(Math.log10(ticks[0]), Math.log10(ticks[ticks.length - 1]), Y0, Y1);
  const y = (v: number) => ly(Math.log10(v));
  const x = linear(0, S.length - 1, X0 + 24, X1 - 24);
  const ref = `<line class="ref" x1="${X0}" x2="${X1}" y1="${f2(y(limit))}" y2="${f2(y(limit))}"><title>soft time limit: ${limit} s</title></line>` +
    `<text class="tick" x="${X0 + 6}" y="${f2(y(limit)) - 6}">time limit (soft)</text>`;
  const series = FORMS.map((f) => {
    const pts = rows.filter((r) => r.form === f).map((r) => ({ r, x: x(S.indexOf(sizeLabel(r))), y: y(r.seconds) }));
    if (!pts.length) return '';
    const last = pts[pts.length - 1];
    return `<polyline class="line s-${f}" points="${pts.map((p) => `${f2(p.x)},${f2(p.y)}`).join(' ')}"/>` +
      pts.map((p) => marker(f, p.x, p.y, `${f}, ${sizeLabel(p.r)}: ${p.r.seconds.toFixed(2)} s (${p.r.status})`)).join('') +
      `<text class="lbl" x="${f2(last.x + 12)}" y="${f2(last.y) + 4}">${f}</text>`;
  }).join('');
  const xl = S.map((s, i) => `<text class="tick" x="${f2(x(i))}" y="${Y0 + 20}" text-anchor="middle">${s}</text>`).join('');
  const lastS = S[S.length - 1];
  const at = FORMS.map((f) => rows.find((r) => r.form === f && sizeLabel(r) === lastS)).filter((r) => r).map((r) => `${r!.form} ${r!.seconds.toFixed(1)} s`).join(', ');
  const label = `Line chart, log scale: solve time in seconds by instance size for formulations A (circles), B (squares) and C (triangles). At ${lastS}: ${at}. Dashed line marks the soft ${limit} s time limit.`;
  return svg(label, axes(ticks, y, (t) => `${t}`, xT, yT) + xl + ref + series);
}

export function tradeoffChart(rows: TradeoffRow[]): string {
  const xT = 'number of open DCs (k, forced)', yT = 'total cost';
  const ok = rows.filter((r) => r.obj != null) as { k_open_forced: number; obj: number }[];
  if (ok.length < 2) return noData(xT, yT);
  const ks = ok.map((r) => r.k_open_forced), costs = ok.map((r) => r.obj);
  const xt = niceTicks(Math.min(...ks), Math.max(...ks), 7), yt = niceTicks(Math.min(...costs), Math.max(...costs), 5);
  const x = linear(xt[0], xt[xt.length - 1], X0 + 8, X1 - 8);
  const y = linear(yt[0], yt[yt.length - 1], Y0, Y1);
  const money = (v: number) => Math.round(v).toLocaleString('en-US');
  const best = ok.reduce((a, b) => (b.obj < a.obj ? b : a));
  const pts = ok.map((r) => `${f2(x(r.k_open_forced))},${f2(y(r.obj))}`).join(' ');
  const dots = ok.map((r) => `<circle class="dot" cx="${f2(x(r.k_open_forced))}" cy="${f2(y(r.obj))}" r="3.5"><title>k = ${r.k_open_forced}: total cost ${money(r.obj)}</title></circle>`).join('');
  const bx = x(best.k_open_forced), by = y(best.obj);
  const opt = `<circle class="opt" cx="${f2(bx)}" cy="${f2(by)}" r="7"><title>minimum: k = ${best.k_open_forced}, total cost ${money(best.obj)}</title></circle>` +
    `<text class="lbl" x="${f2(bx)}" y="${f2(by) + 24}" text-anchor="middle">min: k = ${best.k_open_forced}, ${money(best.obj)}</text>`;
  const xl = xt.map((t) => `<text class="tick" x="${f2(x(t))}" y="${Y0 + 20}" text-anchor="middle">${t}</text>`).join('');
  const infeasible = rows.filter((r) => r.obj == null).map((r) => r.k_open_forced);
  const lo = Math.min(...ks);
  const maxInf = infeasible.filter((k) => k < lo).length ? Math.max(...infeasible.filter((k) => k < lo)) : null;
  const note = maxInf != null ? `<text class="note" x="${X0 + 8}" y="${Y1 + 4}">k ≤ ${maxInf} infeasible</text>` : '';
  const label = `Line chart: total cost against number of open DCs, k = ${lo} to ${Math.max(...ks)}. Cost is U-shaped with its minimum ${money(best.obj)} at k = ${best.k_open_forced}${maxInf != null ? `; k ≤ ${maxInf} is infeasible` : ''}.`;
  return svg(label, axes(yt, y, (t) => `${(t / 1e6).toFixed(2)}M`, xT, yT) + xl + note + `<polyline class="line s-A" points="${pts}"/>` + dots + opt);
}
