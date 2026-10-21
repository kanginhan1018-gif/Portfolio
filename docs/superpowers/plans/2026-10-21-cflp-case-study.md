# CFLP Case Study Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a CFLP formulation-strength case study: an experiments repo plus a site case study with charts generated from the repo's results.

**Architecture:** A separate Python repo (`~/Developer/cflp-network-design`) builds three CFLP formulations in HiGHS, validates against OR-Library optima, runs scaling experiments, and writes `results/*.json`. The Astro site copies those JSON files into `src/data/cflp/` and renders them as dependency-free inline-SVG charts via one component used by `src/pages/projects/[id].astro` when a case study lists `charts` in frontmatter.

**Tech Stack:** Python 3.13, `highspy`, numpy, pandas, pytest; Astro 6 (existing), plain SVG.

**Spec:** `docs/superpowers/specs/2026-10-21-cflp-case-study-design.md`

## Global Constraints

- Free tooling only; solver is HiGHS (`highspy`).
- Every number in the case study comes from `results/*.json` produced by the repo; none typed by hand.
- No results are reported until the OR-Library validation test passes.
- Site stays Astro static; no new npm dependencies; charts are inline SVG with `<title>` tooltips.
- Case study follows the existing 8-section template in `src/content/projects/template-case-study.md` (frontmatter: title, domain, data_source{name,url,license}, methods, solver, tags, repo, date).
- `repo` must be the real GitHub URL; username/repo name come from the user (git user is `kanginhan1018-gif`). Do not push or create the remote without the user's confirmation.
- If formulation C is not clearly stronger on the data, say so in the write-up.

## Review Focus

- Infeasible instance (total capacity < total demand): `Instance.validate()` raises `ValueError`, not a silent bad solve.
- Time limit hit with no incumbent: result row has `status="time_limit"`, `obj=None`, and charts skip it rather than plotting 0.
- Solver gap/time vary run to run: experiments pin `threads=1`, `random_seed=0` and record them in the result JSON.
- Raw dataset download unavailable/changed: loader fails with a message naming the file and URL, and a checksum is stored.
- Chart with empty or single-point series renders an axis and a "no data" label, not a broken SVG.

---

### Task 1: Repo scaffold, instance loaders, validation instances

**Files:**
- Create (in `~/Developer/cflp-network-design/`): `pyproject.toml`, `README.md`, `.gitignore`, `src/cflp/instance.py`, `data/` (OR-Library `cap41`, `cap71`, `cap101`, `cap131` text files + `data/orlib_optima.json`), `tests/test_instance.py`

**Interfaces:**
- Produces: `@dataclass Instance(name: str, capacity: np.ndarray[m], fixed: np.ndarray[m], demand: np.ndarray[n], cost: np.ndarray[m, n])` where `cost[i, j]` is the cost of serving ALL of customer j's demand from facility i; `load_orlib(path: str) -> Instance`; `Instance.validate() -> None` raising `ValueError` if `capacity.sum() < demand.sum()`.

- [ ] **Step 1:** `python3 -m venv .venv`, `pip install highspy numpy pandas pytest`; pin versions in `pyproject.toml`. `git init`.
- [ ] **Step 2:** Write failing tests `test_load_cap41_shape` (m=16, n=50) and `test_infeasible_instance_raises` (build an `Instance` with capacity sum < demand sum; expect `ValueError` from `validate()`).
- [ ] **Step 3:** Download the four OR-Library files from the OR-Library `capinfo` page (confirm exact URL and file format there; record URL and sha256 in `data/SOURCES.md`). Implement `load_orlib` and `validate`. Published optimal values go in `data/orlib_optima.json` copied from the OR-Library page, not recalled.
- [ ] **Step 4:** `pytest tests/test_instance.py -v` → PASS. Commit `feat: instance loader and OR-Library data`.

### Task 2: Three formulations, validated against published optima

**Files:**
- Create: `src/cflp/models.py`, `tests/test_models.py`

**Interfaces:**
- Consumes: `Instance` from Task 1.
- Produces: `class Formulation(str, Enum): LOOSE="A"; TIGHT="B"; STRONG="C"`; `solve(inst: Instance, form: Formulation, time_limit: float = 60.0, force_open: int | None = None) -> dict` returning keys `status` ("optimal"|"time_limit"|"infeasible"), `obj` (float|None), `bound` (best dual bound), `gap` (float|None), `root_lp` (float, LP relaxation value), `nodes` (int), `seconds` (float), `n_open` (int|None), `open` (list[int]|None). Uses `threads=1`, `random_seed=0`. `force_open=k` adds `sum_i y_i = k`.
- Formulations (x_ij ∈ [0,1] fraction of j's demand from i, y_i ∈ {0,1}; objective `sum fixed_i y_i + sum cost_ij x_ij`; each customer fully served): A: `sum_j d_j x_ij <= (sum_j d_j) y_i`; B: `sum_j d_j x_ij <= u_i y_i`; C: B plus `x_ij <= y_i`.

- [ ] **Step 1:** Failing tests: `test_all_forms_match_published_optimum[cap41,cap71,cap101,cap131 × A,B,C]` asserting `abs(obj - published) <= 1e-4 * published`; `test_root_lp_ordering` asserting `root_lp_A <= root_lp_B <= root_lp_C + 1e-6` on cap41; `test_force_open_counts` asserting `n_open == k` on cap41 for k=8.
- [ ] **Step 2:** Run → FAIL (no module).
- [ ] **Step 3:** Implement `solve` with `highspy` (build the model, extract root LP value by first solving the relaxation with integrality dropped, then solve the MIP with the time limit; read nodes/bound from the solver info).
- [ ] **Step 4:** `pytest tests/test_models.py -v` → PASS. If any published optimum is not matched, stop and debug the model; do not loosen the tolerance. Commit `feat: CFLP formulations validated on OR-Library`.

### Task 3: Realistic US instance

**Files:**
- Create: `src/cflp/us_cities.py`, `data/us_cities.csv` (+ entry in `data/SOURCES.md`), `tests/test_us_cities.py`

**Interfaces:**
- Consumes: `Instance`.
- Produces: `build_us_instance(n_demand: int, n_candidates: int, seed: int = 0) -> Instance`. Demand = city population scaled to units; candidates = the `n_candidates` most populous cities as DC sites; `cost[i,j] = rate * d_j * haversine_km(i,j)`; fixed cost and capacity per site are functions of population stated in code comments (capacity = 1.5 × average share so the instance is meaningfully constrained).

- [ ] **Step 1:** Choose a free city dataset with population + lat/lon (e.g. SimpleMaps US Cities Basic, CC BY 4.0; confirm license text on the source page and record name, URL, license in `data/SOURCES.md` and for the site's `data_source`).
- [ ] **Step 2:** Failing tests: `test_haversine_known_pair` (NYC–LA ≈ 3936 km ±20), `test_instance_feasible_and_shapes`, `test_deterministic_for_seed`.
- [ ] **Step 3:** Implement; run tests → PASS. Commit `feat: realistic US city instances`.

### Task 4: Experiment runner and results JSON

**Files:**
- Create: `src/cflp/run.py` (CLI: `python -m cflp.run`), `results/scaling.json`, `results/orlib.json`, `results/tradeoff.json`, `tests/test_run.py`

**Interfaces:**
- Consumes: `solve`, `build_us_instance`, `load_orlib`.
- Produces: `run_scaling(sizes: list[tuple[int,int]], time_limit: float) -> list[dict]` (one row per size×formulation: `n_demand, n_candidates, form` + all `solve` keys); `run_tradeoff(inst: Instance) -> list[dict]` (`k_open_forced, obj` for k = 1..n_candidates using formulation C with `force_open=k`); `main()` writes the three JSON files with a `meta` block (`highs_version, threads, seed, time_limit, date`).

- [ ] **Step 1:** Failing tests on tiny inputs: `test_scaling_rows_cover_all_forms` (sizes=[(10,5)] → 3 rows), `test_time_limit_row_invariant` (time_limit=0.01 on a larger size: if `status=="time_limit"` then `obj is None` or `gap > 0`), `test_tradeoff_has_row_per_k`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Tests PASS.
- [ ] **Step 5:** Run `python -m cflp.run` with sizes chosen so formulation A hits the time limit on the largest ones (start e.g. 20×50, 40×100, 60×200, 80×300 at 120 s; adjust until the contrast is visible, record the final choice in the README). Commit code and `results/`.

### Task 5: Site chart component

**Files:**
- Create: `src/components/Chart.astro`, `src/lib/chart.ts`, `src/data/cflp/` (copy of the three results JSON), `tests/chart.test.mjs`
- Modify: `src/content.config.ts` (add `charts: z.array(z.enum(['gap','time','tradeoff'])).default([])`), `src/pages/projects/[id].astro` (render a `<Chart>` for each name in `charts` after the markdown body), `package.json` (add `tests/chart.test.mjs` to the `test` script)

**Interfaces:**
- Produces: `niceTicks(min: number, max: number, n: number): number[]` in `src/lib/chart.ts` (e.g. `niceTicks(0,97,5)` → `[0,20,40,60,80,100]`); `<Chart kind="gap"|"time"|"tradeoff" />` importing its JSON from `src/data/cflp/`: `gap` = final gap (%) vs instance size per formulation (grouped bars A/B/C); `time` = solve seconds vs size per formulation (lines, log y); `tradeoff` = total cost vs number of open DCs (line, optimum marked). Each mark has a `<title>` tooltip; colors via existing CSS variables from `src/styles/global.css`; works in dark mode and at mobile width (SVG `viewBox`, `width:100%`). Empty/single-point data renders axes plus the text "no data".

- [ ] **Step 1:** Failing node tests (`node --test tests/chart.test.mjs`): `niceTicks(0,97,5)` equals `[0,20,40,60,80,100]`; after `astro build`, the built case-study HTML contains three `<svg` charts each with at least one `<title>`; a chart given empty data contains "no data".
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement helper, component, schema and page wiring. **Step 4:** `npm test` → PASS (existing 6 tests still pass).
- [ ] **Step 5:** Visual check with `npm run dev` in light and dark mode and at 390 px width; fix overflow. Commit `feat: inline SVG charts for case studies`.

### Task 6: Case study content

**Files:**
- Create: `src/content/projects/cflp-network-design.md`

**Interfaces:**
- Consumes: result JSON numbers (quote from files, never typed from memory), `Chart` via `charts: [gap, time, tradeoff]`.
- Frontmatter: `title`, `domain: "Logistics / network design"`, `data_source` (US city dataset from Task 3; OR-Library mentioned in the Data section), `methods: ["MIP", "Facility location", "Formulation strengthening"]`, `solver: "HiGHS via highspy"`, `tags`, `repo` (real URL), `date`.

- [ ] **Step 1:** Write the 8 sections: business problem (DC network, cost of a bad decision), data (both layers, cleaning), EDA (summary that changed a modeling choice, e.g. capacity set to be binding), prediction (state "not needed" in one line), model (A, B, C in KaTeX with the strengthening argument), results (the three charts, one sentence each stating what they show), business reading of the trade-off curve, limits (what was not tried, e.g. single-sourcing, no solver tuning beyond defaults).
- [ ] **Step 2:** `npm test` and `npm run test:base` → PASS; confirm KaTeX renders and the repo link is real.
- [ ] **Step 3:** Commit `feat: CFLP case study`.

### Task 7: Publish (needs user confirmation)

- [ ] **Step 1:** Ask the user for the GitHub repo name and confirmation, then create/push `cflp-network-design` (README: problem, install, `pytest`, `python -m cflp.run`, results table, data sources). Update the case study `repo` field with the URL and re-run `npm test`.
- [ ] **Step 2:** Ask whether to fill `src/site.ts` (name/email/github) and merge `feat/portfolio-site` into `main` (STATUS.md open items); do neither without a yes.

---

## Self-review

- Spec coverage: data layers → T1/T3; validation → T2; formulations A/B/C and metrics → T2/T4; decision curve → T4/T5; repo deliverable → T1/T4/T7; site case study with KaTeX, charts, repo link → T5/T6; non-goals untouched.
- Types: `Instance`, `Formulation`, `solve` keys (incl. `force_open`, declared in T2), and result-file names are consistent across T1–T6.
- Proportion: code is left to signatures and test assertions.
