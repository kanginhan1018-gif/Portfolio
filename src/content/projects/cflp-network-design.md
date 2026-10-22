---
title: "Where to open distribution centers: capacitated facility location on US cities"
domain: "Logistics / network design"
data_source:
  name: "U.S. Census Bureau: Vintage 2024 city population estimates and 2024 Gazetteer (places)"
  url: "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/cities/totals/sub-est2024.csv"
  license: "Public domain (U.S. government work, 17 U.S.C. 105)"
methods: ["MIP", "Facility location", "Formulation strengthening"]
solver: "HiGHS via highspy"
tags: ["network design", "MIP formulations", "logistics"]
repo: "https://github.com/kanginhan1018-gif/cflp-network-design"
date: 2026-10-21
charts: [gap, time, tradeoff]
---

## 1. Business problem

A company ships goods to the biggest US cities. It must choose which cities get a distribution center (DC), and which DC supplies each city. Opening a DC costs a fixed amount. Each DC can only handle so much. Shipping costs more when a city needs more goods or is farther away. The choice is made rarely and is hard to undo. Open too few DCs and there isn't enough capacity, or every shipment travels a long way. Open too many and the company pays for DCs it hardly uses. So the question is: how many DCs, and where? There is a second question for the person building the model: how do you write it so that an ordinary solver (off-the-shelf software that finds the best answer) can solve it fast at realistic sizes?

## 2. Data

There are two layers of data.

**US instance (the case study).** I took the 500 most populous US incorporated places. Population is `POPESTIMATE2024` from the Census Bureau's Vintage 2024 city and town estimates. Coordinates are the internal points (`INTPTLAT`/`INTPTLONG`) from the [2024 Gazetteer place file](https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_place_national.zip). Both are US Census Bureau data and in the public domain. Cleaning was simple:

- join the two files on GEOID (state + place);
- keep summary level 162 only;
- strip Census suffixes (" city", " town", " CDP", " (balance)", " metropolitan government") from names.

The script `scripts/build_us_cities.py` regenerates the file, and its sha256 is pinned in `data/SOURCES.md`. (SimpleMaps was tried first, but its download sits behind a Cloudflare challenge.)

A test problem (an "instance") of size $n_{\text{demand}} \times n_{\text{candidates}}$ uses the $n_{\text{demand}}$ biggest cities as customers. The $n_{\text{candidates}}$ biggest cities are the places where a DC could be built, so the two groups overlap. Each city gives these numbers to the model:

- demand $d_j$ = population / 1000;
- shipping cost $c_{ij} = 0.05 \cdot d_j \cdot \text{haversine}_{km}(i, j)$, the cost of supplying all of city $j$ from city $i$ (haversine = straight-line distance over the Earth's surface);
- fixed cost $f_i = 8000 \sqrt{\text{pop}_i / 10^5} \cdot U(0.8, 1.2)$, with seed 0 (a fixed random seed, so the result can be repeated), so bigger cities cost more to build in;
- capacity $u_i$, set by the rule in section 3.

Costs are in the model's own units, not dollars.

**OR-Library (validation only).** Beasley's warehouse location test problems cap41, cap71, cap101 and cap131 come with known best answers. I used them only to check that my model code is correct, not as the case study. All 12 runs (4 problems × 3 formulations, meaning three ways of writing the model) match the known best answer. The largest relative error is 6.3e-10 (`6.30167676893662e-10`, cap131/C). It is just rounding: the published answers have only three decimals (cap101 is published as 796648.437, and we get 796648.4375).

## 3. EDA

The data has no real capacities or building costs, so two numbers are my own assumptions: the capacity rule and the fixed-cost scale. Here I tried different settings to make sure the decision isn't trivial.

- **Capacity rule (changed).** In an earlier version (not in the final results), each site could handle 1.5× its average share of demand. Total capacity was then only 1.5× total demand, so at least two thirds of all sites had to open just to cover everyone. Most open/close choices were forced, and the balance between building cost and shipping cost hardly showed. I changed it to **3× the average share**: $u_i = 3 \cdot \frac{\sum_j d_j}{n_{\text{candidates}}} \cdot w_i$, where $w_i \propto \sqrt{\text{pop}_i}$ means bigger cities get more capacity, rescaled so the average weight is 1. Total capacity is now 3× demand, but capacity still matters: on the 100 × 40 problem, any 8 sites are too few (section 6).
- **Fixed-cost scale (assumption).** I chose 8000 so that the best plan on 100 × 40, with no forced number of sites, opens 18 of the 40 sites. That leaves room on both sides of the cost curve.
- **Instance shape (changed).** I also tried problems with more candidate sites than customers, for example 60 demand × 200 candidates. There, nearly every customer gets its own site and all three formulations run out of time, so these problems can't tell the formulations apart. I dropped them and grew the grid with more customers than candidates instead.

## 4. Prediction / forecasting

Not needed: demand is taken as given (2024 population).

## 5. Optimization model

Think of $y_i$ as an on/off switch for each possible DC: $y_i = 1$ means DC $i$ opens, $y_i = 0$ means it stays closed. Let $x_{ij} \in [0,1]$ be the share of city $j$'s demand supplied from DC $i$ (a city may be supplied by several DCs). The goal is the lowest total of building cost plus shipping cost, and every city's demand must be fully covered. All three formulations share this goal and this rule:

$$
\min_{x,\,y}\ \sum_i f_i\,y_i + \sum_i\sum_j c_{ij}\,x_{ij}
\quad\text{s.t.}\quad \sum_i x_{ij} = 1\ \ \forall j,\qquad 0 \le x_{ij} \le 1,\ \ y_i \in \{0,1\}.
$$

They differ only in how they write the rule "a closed DC ships nothing, and an open DC ships no more than its capacity."

**A, loose.** The first rule uses the total demand $\sum_k d_k$ as the limit for an open DC. That limit is so large that it never stops a DC from overloading, so A needs a second rule for capacity:

$$
\text{(A)}\qquad \sum_j d_j\,x_{ij} \le \Big(\sum_k d_k\Big)\,y_i, \qquad \sum_j d_j\,x_{ij} \le u_i \qquad \forall i.
$$

**B, one tighter rule.** A single rule does both jobs:

$$
\text{(B)}\qquad \sum_j d_j\,x_{ij} \le u_i\,y_i \qquad \forall i.
$$

**C, B plus a per-city rule.** It adds: a closed DC supplies no city at all.


$$
\text{(C)}\qquad \sum_j d_j\,x_{ij} \le u_i\,y_i, \qquad x_{ij} \le y_i \qquad \forall i, j.
$$

**Why C is stronger.** All three give the same final answers, but the solver starts by solving an easier version where a switch may be partly on (say, 30% open). This is called the LP relaxation. The less a formulation lets a DC cheat by being only barely "on", the closer that first estimate is to the truth, and the faster the solver finishes. The three nest inside each other: $P_C \subseteq P_B \subseteq P_A$. B contains both rules of A, because $y_i \le 1$ gives $u_i y_i \le u_i$, and $u_i \le \sum_k d_k$ gives $u_i y_i \le (\sum_k d_k) y_i$. Here the largest site's capacity is at most about 22% of total demand on the 100 × 40 problem, and about 9% on 500 × 150. C adds rules on top of B. How much can a DC cheat in each one?

- In A, a DC can be "open" by only $y_i = \text{load}_i / \sum_k d_k$. That is a tiny fraction, so the easy version pays almost none of the building cost.
- In B, the fraction rises to $\text{load}_i / u_i$.
- In C, $y_i \ge \max_j x_{ij}$. A DC that fully supplies even one city must be fully open, so the easy version pays the full building cost.

The first estimate gets closer to the truth in the same order (section 6).

**Size and solver.** The largest problem is 500 × 150. It has 150 on/off switches $y_i$, 75,000 shipping amounts $x_{ij}$, 500 "cover each city" rules and 150 capacity rules. A adds 150 more capacity rules, and C adds 75,000 rules of the form $x_{ij} \le y_i$. I solved with HiGHS 1.15.1 through highspy, on 1 thread with seed 0, default settings and a 120 s time limit per solve. "Optimal" here means the answer is proven to be within HiGHS's default tolerance `mip_rel_gap = 1e-4` (0.01%) of the best possible, not exactly equal to it.

## 6. Results & sensitivity

Each size was solved with all three formulations. Root gap is how far the solver's first estimate is from the final answer, $(\text{obj} - \text{root LP}) / \text{obj}$ (smaller is better). Time is the real elapsed time of the solve. Nodes count how many sub-problems the solver had to check.

| size (demand × candidates) | root gap A | root gap B | root gap C | time A (s) | time B (s) | time C (s) | nodes A / B / C |
|---|---|---|---|---|---|---|---|
| 100 × 40 | 68.5% | 36.5% | 0.2% | 0.7 | 1.5 | 0.1 | 1 / 1 / 1 |
| 200 × 60 | 78.5% | 38.4% | 1.0% | 10.5 | 11.1 | 6.5 | 133 / 3 / 3 |
| 300 × 80 | 80.2% | 34.8% | 1.6% | 42.7 | 25.1 | 18.2 | 2066 / 154 / 45 |
| 400 × 100 | 82.2% | 32.0% | 1.4% | 157.8 | 67.2 | 40.5 | 5782 / 788 / 267 |
| 500 × 150 | 88.7% | 26.3% | 0.8% | 219.8 (limit) | 60.2 | 121.2 | 504 / 73 / 178 |

- **C's first estimate is by far the closest** at every size: 0.2–1.6% off, against 26–38% for B and 68–89% for A. A's estimate gets worse as the problem grows.
- **C is not always the fastest.** It wins at the four smaller sizes. At 500 × 150, B finishes in 60.2 s while C takes 121.2 s and checks more sub-problems (178 against 73). A likely reason is that the 75,000 extra rules $x_{ij} \le y_i$ make each step slower, but I did not measure the cost per step. In this data, C's much better first estimate did not make it faster at the largest size.
- **Only A runs out of time.** At 500 × 150 it stopped with a 14.8% gap. Its best plan opened 51 sites at cost 1,266,018, about 1.5% worse than B's proven answer (52 sites, 1,247,094).
- **The time limit is not exact.** HiGHS checks the clock only between chunks of work, so three runs report more than 120 s: 400 × 100 A (157.8 s, still optimal), 500 × 150 A (219.8 s, time limit) and 500 × 150 C (121.2 s, optimal).
- **What "optimal" means here.** At 500 × 150, B and C both count as optimal but report slightly different costs, 1,247,094 and 1,247,119. They differ by 0.002%, which is inside the 0.01% tolerance.

The 88.7% root gap for A at 500 × 150 is measured against the best plan A itself found, not the proven best answer; measured against B's answer it would be about 88.6%.

The charts are below the article.

- *Final gap:* every run ends within the 0.01% tolerance except A at 500 × 150, which is left at 14.8%.
- *Solve time (log scale):* A's time grows fastest with size, and B overtakes C at the largest size.
- *Total cost vs. number of open DCs* (100 × 40, formulation C, exactly $k$ sites forced open): the curve is U-shaped, and $k \le 8$ is impossible.

### Reading the trade-off curve

The cheapest network opens **k = 18 DCs at a total cost of 954,823**, which is the same answer as the free optimum. With **k ≤ 8 no plan works**: on this 100 × 40 problem, even the eight biggest candidate sites together can handle only about 98% of total demand, so a ninth site is needed just to cover everyone.

The bottom of the curve is flat. Every $k$ from 15 to 20 costs within 0.72% of the optimum:

- k = 17 is 429 more (+0.045%);
- k = 19 is 2,078 more (+0.22%);
- k = 16 is 2,772 more (+0.29%);
- k = 20 is 6,847 more (+0.72%).

Away from the bottom, cost climbs fast: k = 12 is +5.9%, k = 9 is +27.1% and k = 40 (every site open) is +34.7%.

For a decision-maker, the model is more sure about a range of network sizes than about one exact number. Anything from 16 to 19 DCs is within 0.3% of the best plan. Inside that range, the choice can be made on things the model leaves out, such as lease terms, local labor, or room to grow, at almost no extra modeled cost. Outside it, cost rises quickly: k = 14 is +1.96% and k = 22 is +2.27%.

## 7. Limitations

- **Split sourcing is allowed.** A city's demand can be split across several DCs. Having just one DC per city ($x_{ij} \in \{0,1\}$) is more realistic but much harder to solve, and I did not try it.
- **One period, deterministic demand.** There is no growth, no seasons, no uncertain demand, and no plan for opening DCs over several years.
- **Assumed parameters.** Capacity (3× the average share) and the fixed-cost scale (8000) are my own choices, not real data, and the shipping rate is not matched to real freight prices. Where the cheapest point falls depends on these choices. The *pattern* in how the three formulations compare should not.
- **Default solver settings.** The only changes were 1 thread and seed 0. I did no tuning and gave the solver no hints or head start. The gap between B and C at the largest size might change with different solver settings.
- **One instance family.** All problems are cut from one US city list, each the top of the same list, with one random seed for building costs. OR-Library is used only to check correctness.
- **Single-run timings.** Each time is one run on one machine with HiGHS 1.15.1, 1 thread, seed 0, `mip_rel_gap` 1e-4 and a rough 120 s limit, recorded on 2026-10-21. I did not repeat runs, so treat small time differences as noise.

## 8. Reproduce

The repository is linked in the table above. Python 3.11+, with dependencies pinned in `pyproject.toml` (`highspy==1.15.1`, `numpy`, `pandas`):

    python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
    .venv/bin/python -m cflp.run     # writes results/{orlib,tradeoff,scaling}.json

A full run took 794 s on the machine used here. The charts on this page are drawn from copies of `scaling.json` and `tradeoff.json` made by that run.
