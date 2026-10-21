---
title: "Where to open distribution centers: capacitated facility location on US cities"
domain: "Logistics / network design"
data_source:
  name: "U.S. Census Bureau: Vintage 2024 city population estimates and 2024 Gazetteer (places)"
  url: "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/cities/totals/sub-est2024.csv"
  license: "Public domain (U.S. government work, 17 U.S.C. 105)"
methods: ["MIP", "Facility location", "Formulation strengthening"]
solver: "HiGHS via highspy"
tags: ["facility location", "network design", "MIP formulations", "logistics"]
repo: "https://github.com/"
date: 2026-10-21
charts: [gap, time, tradeoff]
---

## 1. Business problem

A distributor serving the largest US cities has to decide which candidate cities get a distribution center (DC) and which DC serves each city. Opening a DC has a fixed cost, every DC has a capacity limit, and shipping cost grows with demand times distance. The decision is made once every few years and is hard to undo. If it opens too few DCs, the network runs out of capacity or pays for long hauls on every shipment. If it opens too many, it pays fixed costs for sites it barely uses. The question is how many DCs to open and where. A second question matters just as much for the modeler: how do you write the model so a standard solver can answer the first question at realistic sizes?

## 2. Data

There are two layers of data.

**US instance (the case study).** I took the 500 most populous US incorporated places. Population is `POPESTIMATE2024` from the Census Bureau's Vintage 2024 city and town estimates. Coordinates are the internal points (`INTPTLAT`/`INTPTLONG`) from the [2024 Gazetteer place file](https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_place_national.zip). Both are US Census Bureau data and in the public domain. Cleaning was simple:

- join the two files on GEOID (state + place);
- keep summary level 162 only;
- strip Census suffixes (" city", " town", " CDP", " (balance)") from names.

The script `scripts/build_us_cities.py` regenerates the file, and its sha256 is pinned in `data/SOURCES.md`. (SimpleMaps was tried first, but its download sits behind a Cloudflare challenge.)

An instance of size $n_{\text{demand}} \times n_{\text{candidates}}$ uses the $n_{\text{demand}}$ most populous cities as customers. The $n_{\text{candidates}}$ most populous cities are the candidate DC sites, so the two sets overlap. Each city becomes these model parameters:

- demand $d_j$ = population / 1000;
- assignment cost $c_{ij} = 0.05 \cdot d_j \cdot \text{haversine}_{km}(i, j)$, the cost of serving all of $j$ from $i$;
- fixed cost $f_i = 8000 \sqrt{\text{pop}_i / 10^5} \cdot U(0.8, 1.2)$, with seed 0, so larger metros cost more to site;
- capacity $u_i$, given by the rule in section 3.

Costs are in model units, not dollars.

**OR-Library (validation only).** Beasley's capacitated warehouse location instances cap41, cap71, cap101 and cap131 have published optima. I used them only to check that the model code is right, not as the case study. All 12 runs (4 instances × 3 formulations) reproduce the published optimum. The largest relative error is 6.3e-10 (`6.30167676893662e-10`, cap131/C). It comes from rounding, because the published optima have three decimals (cap101 is published as 796648.437, and we get 796648.4375).

## 3. EDA

The data has no observed capacities or site costs, so two numbers are my own assumptions: the capacity rule and the fixed-cost scale. The exploration here was about where to set them so the decision is not trivial.

- **Capacity rule (changed).** The first version gave each site 1.5× its average share of demand. Total capacity was then only 1.5× total demand, so at least two thirds of the capacity had to be opened just to be feasible. The open/close decision was mostly forced, and the trade-off between fixed and transport cost hardly showed. I replaced it with **3× the average share**: $u_i = 3 \cdot \frac{\sum_j d_j}{n_{\text{candidates}}} \cdot w_i$, where $w_i \propto \sqrt{\text{pop}_i}$ is rescaled to mean 1. Total capacity is now 3× demand, and capacity still binds: on the 100 × 40 instance, any 8 sites are too few (section 6).
- **Fixed-cost scale (assumption).** I set the scale to 8000 so that the unconstrained optimum on 100 × 40 opens 18 of the 40 sites. That leaves room on both sides of the cost curve.
- **Instance shape (changed).** I also tried shapes with more candidates than customers, for example 60 demand × 200 candidates. There, nearly every customer gets its own site and all three formulations time out, so these shapes say nothing about formulation strength. I dropped them and grew the grid with more customers than candidates instead.

## 4. Prediction / forecasting

Not needed: demand is taken as given (2024 population).

## 5. Optimization model

Let $y_i \in \{0,1\}$ mean that DC $i$ opens. Let $x_{ij} \in [0,1]$ be the share of customer $j$'s demand served from $i$ (split sourcing is allowed). All three formulations share the objective and the assignment constraints:

$$
\min_{x,\,y}\ \sum_i f_i\,y_i + \sum_i\sum_j c_{ij}\,x_{ij}
\quad\text{s.t.}\quad \sum_i x_{ij} = 1\ \ \forall j,\qquad 0 \le x_{ij} \le 1,\ \ y_i \in \{0,1\}.
$$

They differ only in how capacity is tied to the open decision.

**A, loose big-M.** The link uses $M = \sum_k d_k$, the total demand. A link with that $M$ never enforces capacity, so A also needs a separate capacity row:

$$
\text{(A)}\qquad \sum_j d_j\,x_{ij} \le \Big(\sum_k d_k\Big)\,y_i, \qquad \sum_j d_j\,x_{ij} \le u_i \qquad \forall i.
$$

**B, capacity-scaled link.** One row does both jobs:

$$
\text{(B)}\qquad \sum_j d_j\,x_{ij} \le u_i\,y_i \qquad \forall i.
$$

**C, B plus the disaggregated link:**

$$
\text{(C)}\qquad \sum_j d_j\,x_{ij} \le u_i\,y_i, \qquad x_{ij} \le y_i \qquad \forall i, j.
$$

**Why C is stronger.** All three have the same integer solutions, but their LP relaxations are nested: $P_C \subseteq P_B \subseteq P_A$. B implies both rows of A, because $y_i \le 1$ gives $u_i y_i \le u_i$, and $u_i \le \sum_k d_k$ gives $u_i y_i \le (\sum_k d_k) y_i$. Here the largest site holds at most 22% of total demand. C adds rows on top of B. What do the relaxations let a site get away with?

- In A, a site can open at $y_i = \text{load}_i / \sum_k d_k$. That is a tiny fraction, so the LP pays almost none of the fixed cost.
- In B, the fraction rises to $\text{load}_i / u_i$.
- In C, $y_i \ge \max_j x_{ij}$. A site that serves even one city in full must be fully open, so the LP pays the full fixed cost.

The root LP bound improves in the same order (section 6).

**Size and solver.** The largest instance is 500 × 150. It has 150 binary $y_i$, 75,000 continuous $x_{ij}$, 500 assignment rows and 150 capacity rows. A adds 150 more capacity rows, and C adds 75,000 rows of the form $x_{ij} \le y_i$. I solved with HiGHS 1.15.1 through highspy, on 1 thread with seed 0, using default settings and a 120 s time limit per solve. "Optimal" means proven within HiGHS's default relative MIP gap of `mip_rel_gap = 1e-4` (0.01%), not exactly zero.

## 6. Results & sensitivity

Each size was solved with all three formulations. Root gap is $(\text{obj} - \text{root LP}) / \text{obj}$, and time is the MIP solve's wall-clock time.

| size (demand × candidates) | root gap A | root gap B | root gap C | time A (s) | time B (s) | time C (s) | nodes A / B / C |
|---|---|---|---|---|---|---|---|
| 100 × 40 | 68.5% | 36.5% | 0.2% | 0.7 | 1.5 | 0.1 | 1 / 1 / 1 |
| 200 × 60 | 78.5% | 38.4% | 1.0% | 10.5 | 11.1 | 6.5 | 133 / 3 / 3 |
| 300 × 80 | 80.2% | 34.8% | 1.6% | 42.7 | 25.1 | 18.2 | 2066 / 154 / 45 |
| 400 × 100 | 82.2% | 32.0% | 1.4% | 157.8 | 67.2 | 40.5 | 5782 / 788 / 267 |
| 500 × 150 | 88.7% | 26.3% | 0.8% | 219.8 (limit) | 60.2 | 121.2 | 504 / 73 / 178 |

- **C has by far the tightest root bound** at every size: 0.2–1.6%, against 26–38% for B and 68–89% for A. A's bound gets worse as the instance grows.
- **C is not always the fastest.** It wins at the four smaller sizes. At 500 × 150, B finishes in 60.2 s and C takes 121.2 s, because the 75,000 extra rows $x_{ij} \le y_i$ make every LP heavier. A tighter bound pays off only when fewer nodes outweigh the cost of solving each node's LP.
- **Only A hits the time limit.** At 500 × 150 it stopped with a 14.8% gap. Its best plan opened 51 sites at cost 1,266,018, about 1.5% worse than B's proven solution (52 sites, 1,247,094).
- **The limit is soft.** HiGHS checks the clock only between units of work, so three runs report more than 120 s: 400 × 100 A (157.8 s, still optimal), 500 × 150 A (219.8 s, time limit) and 500 × 150 C (121.2 s, optimal).
- **What "optimal" means here.** At 500 × 150, B and C both count as optimal but report different costs, 1,247,094 and 1,247,119. They differ by 0.002%, inside the 0.01% tolerance.

The charts are below the article.

- *Final MIP gap:* every run ends at or below the 0.01% tolerance except A at 500 × 150, which is left at 14.8%.
- *Solve time (log scale):* A's time grows fastest with size, and B overtakes C at the largest size.
- *Total cost vs. number of open DCs* (100 × 40, formulation C, exactly $k$ sites forced open): the curve is U-shaped, and $k \le 8$ is infeasible.

### Reading the trade-off curve

The cheapest network opens **k = 18 DCs at a total cost of 954,823**, which is the same answer as the free optimum. With **k ≤ 8 no plan is feasible**: even the eight largest candidate sites together hold only about 98% of total demand, so a ninth site is needed just to have room for everyone.

The bottom of the curve is flat. Every $k$ from 15 to 20 costs within 0.72% of the optimum:

- k = 17 is 429 more (+0.045%);
- k = 19 is 2,078 more (+0.22%);
- k = 16 is 2,772 more (+0.29%);
- k = 20 is 6,847 more (+0.72%).

Away from the bottom, cost climbs fast: k = 12 is +5.9%, k = 9 is +27.1% and k = 40 (every site open) is +34.7%.

For a decision-maker, the model pins down the range of network sizes more firmly than the exact number. Anything from 16 to 19 DCs is within 0.3% of the best plan. Inside that range, the choice can rest on things the model leaves out, such as lease terms, labor markets, or room to grow, at almost no modeled cost. Going below about 14 DCs or above about 22 costs real money: more than 1.9% and 2.2% respectively.

## 7. Limitations

- **Split sourcing is allowed.** A customer's demand can be divided across DCs. Single sourcing ($x_{ij} \in \{0,1\}$) is more realistic and much harder, and I did not try it.
- **One period, deterministic demand.** There is no growth, seasonality, or stochastic or robust demand, and no multi-period opening schedule.
- **Assumed parameters.** Capacity (3× the average share) and the fixed-cost scale (8000) are my modeling choices, not observed data, and the transport rate is not calibrated to real freight costs. The location of the minimum depends on these choices. The *shape* of the formulation comparison should not.
- **Default solver settings.** The only change was 1 thread and seed 0. There is no tuning, no custom cuts and no warm starts. The gap between B and C at the largest size might change with cut or presolve settings.
- **One instance family.** All instances are nested prefixes of a single US city list with one random seed for fixed costs. OR-Library is used only to validate correctness.
- **Single-run timings.** Each wall-clock time is a single run on one machine with HiGHS 1.15.1, 1 thread, seed 0, `mip_rel_gap` 1e-4 and a soft 120 s limit, recorded on 2026-10-21. There are no repeats or variance estimates, so read small time differences as noise.

## 8. Reproduce

The repository is linked in the table above. Python 3.11+, with dependencies pinned in `pyproject.toml` (`highspy==1.15.1`, `numpy`, `pandas`):

    python3 -m venv .venv && .venv/bin/pip install -e .[dev]
    .venv/bin/python -m cflp.run     # writes results/{orlib,tradeoff,scaling}.json

A full run took 794 s on the machine used here. The charts on this page are drawn from copies of `scaling.json` and `tradeoff.json` made by that run.
