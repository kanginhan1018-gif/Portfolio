# CFLP case study — design (2026-10-21)

## Intent
First real case study for the portfolio. Goal: a hiring reader concludes "this person has real OR expertise" by seeing a modeling decision (formulation strengthening) validated with numbers, on a problem industry actually solves (distribution-center network design).

## Problem
Capacitated facility location (CFLP): choose which DCs to open (fixed cost, capacity) and how to serve each demand node (transport cost ∝ distance) at minimum total cost. Fixed cost + capacity gives the natural big-M linking constraint.

## Data (two layers)
1. **Realistic:** public geographic data (e.g. US cities: population → demand, coordinates → haversine distance → transport cost). Exact source and license to be confirmed by the builder and recorded in frontmatter `data_source`.
2. **Validation:** OR-Library CFLP benchmark instances; the model must reproduce the published optimal values before any experiment is reported.

## Experiments
- Formulations: (A) loose big-M (`sum_j x_ij <= M y_i`, M large), (B) tight capacity (`sum_j d_j x_ij <= u_i y_i`), (C) strengthened with `x_ij <= y_i` (disaggregated linking).
- Solver: HiGHS via Python (free). Scale: increase number of candidate DCs / demand nodes; record root LP gap, final gap, time, node count under a fixed time limit.
- Decision view: total cost vs number of opened DCs for the realistic instance, with a business reading.

## Deliverables
- GitHub repo (new, separate from the site): model code, experiment scripts, results CSV, README with reproduce steps.
- Site: one case study in `src/content/projects/` following the existing 8-section template (KaTeX), with interactive charts built from the results CSV (static at build time or light client-side chart; builder's call, no heavy dependency) and the `repo` link.

## Non-goals
Multi-period/stochastic extensions, commercial solvers, a live solver in the browser, a CMS.

## Anti-goals
Reporting numbers not produced by the repo; claiming speedups without the benchmark check passing; a long essay that buries the formulation comparison.

## Constraints
Free tooling only. Site stays Astro static, deployable to GitHub Pages. `src/site.ts` placeholders (name/email/github) are a separate task, but the case-study `repo` field needs the real GitHub URL (user to supply username/repo name).

## Builder's calls (mine, not user-approved)
- Instance sizes, time limit, and exact chart library are left to the plan.
- Formulation C is included because it is the standard strengthening; if it is not clearly stronger on the data, report that honestly.
