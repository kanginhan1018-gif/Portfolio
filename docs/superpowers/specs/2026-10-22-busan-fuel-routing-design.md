# Busan fuel-aware routing case study — design (2026-10-22)

## Intent
Second case study for the portfolio, and the one that shows the "breadth" half of the T-shaped profile: forecasting on top of optimization. A reader should conclude "this person can forecast a real signal from messy public data and then optimize a decision with it, and is honest about what the data can't support."

The motivation, in the author's words: **reduce wasted fuel**. Idling at red lights is one source of waste, not the goal itself. Optimizing idle time alone would reward long detours that burn more fuel, so the objective is total fuel.

## Problem
One car drives from an origin to a destination in a road network in central Busan. Along the way the driver chooses (a) the route and (b) the speed on each road segment, which decides whether the car reaches the next signal on green. Signals have cycles, so arrival time determines waiting time. Traffic conditions vary by time of day and are re-forecast as the trip progresses; the plan is re-optimized from the current position each time.

Three plans are produced for every trip, and the relationship between them is the main result:
1. **Fastest:** minimizes travel time.
2. **Least fuel:** minimizes total fuel.
3. **Compromise:** a point on the time-versus-fuel trade-off curve (bi-objective, Pareto front). The curve itself is the deliverable; "compromise" is a representative point chosen on it, for example "x% fuel saved for y extra minutes", with the choice rule stated.

## Goals
- A time-versus-fuel trade-off curve, averaged over many simulated trips, comparing the three plans.
- Fuel = sum of: driving fuel as a function of speed and distance, stop-and-restart (acceleration) fuel at signals, and idle fuel while waiting. Use a published, citable fuel model; do not invent coefficients. Default vehicle: ordinary gasoline passenger car (assistant's call).
- A forecasting step: predict per-intersection delay and volume by hour and day type from the smart-intersection data. Baseline = mean by (day type × hour). A machine-learning model is included only to test whether it beats the baseline; if it does not, say so and use the baseline.
- Evaluation of live re-forecasting: hold out the last days of data, replay them in time order as if live, and compare (a) always-shortest-path car, (b) forecast-once-before-departure car, (c) continuously re-forecasting car.
- Sensitivity analysis on the assumed signal cycles (results with cycles perturbed), because most cycles are assumptions.
- A published case study following the existing template (sections 1-8), English and Korean, with charts, matching how the CFLP page is built.

## Non-goals
- Not a real-time system, an app, or a routing product. No live API calls in the shipped site.
- No fleet or multi-vehicle effects; one car, traffic is not changed by the car.
- No measured fuel from real cars; fuel is modeled.
- No validation of signal cycles against the field (that belongs to the separate Crosswalk project).
- No city-wide Busan; the scope is the area described below.

## Anti-goals (would count as failure even if it "works")
- Fuel savings that come from a detour the fuel model charges too little for, or from ignoring extra distance.
- Reporting estimated signal cycles as if they were measured.
- Publishing vehicle plate numbers or raw GPS.
- Showing only good news: if continuous re-forecasting does not beat forecast-once, or ML does not beat the baseline, that goes on the page.

## Scope: area
Central Busan around Seomyeon (about 35.16 N, 129.06 E). In a 0.02-degree cell there, the author's data has 6 smart intersections, 6 signal-cycle estimates and about 270 bus-speed segments, the densest overlap found. The builder may widen the box to get enough routing choices but should keep it to one contiguous area and say what the box is.

## Data (all produced by the author's private Crosswalk project at `~/Developer/crosswalk`)
Findings below were measured on 2026-10-22.

1. **Smart intersections, hourly** (`data/smart-intersection-hourly/*.json`, `scripts/output/busan-smart-intersections-strict.json` for the 157 with coordinates). Records `{h, name, lvl, delay, vol}` per intersection per hour, 34 files from 2026-09-17 to 2026-10-20. Real general-traffic volume (vehicles per hour) and signal delay (seconds). The last day has only 22 hours, so check completeness before using. Weekday peaks: volume at 08:00 and 17:00, delay at 17-18:00.
   - Known oddity: mean delay dips at 19:00 and spikes at about 43 s at 20:00 on weekdays (the weekend spike is at 19:00), while volume falls smoothly. The author's guess is commuting peaks; that explains the 17-18:00 rise but not the dip, so it is unexplained. **Investigate before using hours 19-20; do not feed them to the model unexamined.** These hours matter for evening trips.
2. **Bus-based road speed** (`scripts/output/road-congestion-data.json`). 75,926 rows `{routeId, nodeord, hourBucket, avgSpeedMs, sampleCount, hasBusLane}`, 183 routes, 3-hour buckets (0, 3, ..., 21). Coordinates come from the raw bus positions (`routeId`, `nodeord` to median lat/lng); 10,301 of 11,483 usable segments could be located. Caveats: it is bus speed, so it includes stop time at bus stops and is biased low in absolute terms; 3.3% of rows are bus lanes and should be excluded (they are about 2.5-3 km/h faster, same time-of-day shape). Use it mostly as a **relative** index (speed / the segment's own fastest bucket) of time-of-day congestion and of differences between segments. The all-city index is nearly flat (0.78-0.88, worst 15-18:00), so do not expect strong signal from it alone.
3. **Signal cycles** (`scripts/output/robust-signal-timing-20260925.json`, 1,944 rows of `{crossingId, weekday, hourBucket, cycleSec, phaseSec, ...}`, plus `harmonic-base-cycle.json`, `control-delay.json`). Estimated from bus GPS stops, **not validated in the field**; the Crosswalk roadmap states only one intersection passes its internal check, and some values (e.g. 39 s) may be GPS polling artifacts. Only 86 of 214 crossing IDs have local coordinates (OSM junction IDs in `scripts/cache/osm-signal-junctions-busan.json`); the other 128 are Firestore IDs without local coordinates. Only 9 of the 157 smart intersections are within 150 m of a signal-cycle estimate. **Therefore signal cycles are mostly assumed values**: a plausible fixed cycle per intersection (drawn from the distribution of the estimates), with estimated values used where they overlap, and a sensitivity analysis.
4. **Road network:** OpenStreetMap for the area (free; ODbL attribution required).
5. Bus-lane map (`scripts/cache/osm-bus-lanes-busan.json`) can support excluding bus-lane segments.

## Constraints
- **Public site:** publish aggregated results and code only. Raw bus GPS contains vehicle plate numbers and must never be published or committed to the portfolio repo.
- **Licenses unconfirmed:** the terms for TAGO and BusanBIMS data, and the Smart Intersection data source, have not been checked. Confirm and record in the `data_source` frontmatter before publishing; if redistribution is not allowed, publish only derived aggregates and say how to rebuild.
- Parity rules already enforced by `tests/i18n.test.mjs` apply (same numbers, math blocks, URLs and `##` headings in the English and Korean pages).
- Plain language: the author asked that explanations be easy to read (as was done for the CFLP page). Include a "Why this project" and "Background you need" part. Define terms such as Pareto front and idling in simple words.
- Solver and stack: the author uses Python and HiGHS elsewhere; reuse them where an LP or MIP is needed. Choice of algorithm is left to the builder.

## Decided by the author
- Switch from the original Daejeon idea to Busan because Busan data already exists.
- Assume signal cycles; do not wait for real signal data.
- Traffic changes by time of day; forecast it from the smart-intersection data and re-forecast during the trip.
- Success = fuel (and time) trade-off shown versus a shortest-path car. Objective is fuel, not idle time.
- Three models: fastest, least fuel, compromise.
- Scope around Seomyeon.

## Calls made by the assistant (author can override)
- Default vehicle: gasoline passenger car.
- Baseline forecaster first, ML second.
- Replay of held-out days as the "live" test.
- Compromise = a chosen point on the Pareto curve rather than one fixed weighting.
- Relative-index use of bus speed rather than absolute speed.
- Spec written in English to match the existing specs; the site pages are bilingual.

## Calls added after the builder check (assistant's calls, author can override)
- **Baseline car:** the shortest-distance route, driving at the forecast traffic speed on each segment with no speed choice, passing the same signals and the same realized traffic as the other plans. A weak baseline would inflate savings, so this is the strong, plain one.
- **Where segment speed comes from:** free-flow speed per road from OSM (speed limit if tagged, otherwise a documented default by road class), scaled by the bus-speed relative index for the hour. Smart-intersection delay is **not** added to segment speed; signal waiting is counted once, as the simulated wait at the signal. Smart-intersection delay and volume are used to forecast congestion and to check the simulated delays against the measured ones.
- **Box size:** the builder may widen the box until there are enough smart intersections for a meaningful network and forecast, and must report how many it contains. The forecaster is trained on all 157 intersections, not only those inside the box.
- **Speed bounds:** the chosen speed on a segment stays between the speed limit and a stated fraction of the forecast flow speed (a car cannot sit far below traffic or pass queued cars). The fraction is a parameter, varied in the sensitivity analysis, so "creep everywhere" cannot win by assumption.
- **Phase offsets between neighbouring signals:** random and independent by default; a coordinated green-wave case is run as a sensitivity variant, since it can swing the result.
- **Sensitivity may change the conclusion.** Run a small prototype on one corridor first to check that a fuel saving exists under the assumed cycles before building the full pipeline. If the saving disappears under plausible cycles, report that.
- **Plans are scored on realized traffic.** In the replay, each plan is built from forecast values and executed against what actually happened that day. Re-forecasting helps only if it reacts to the gap between forecast and realized.
- **Held-out days:** hold out about a week of complete days covering weekdays and weekend days, excluding the partial last day, and report bootstrap confidence intervals. If continuous re-forecasting is not distinguishable from forecast-once, say so.
- **19-20:00 anomaly:** keep the data but flag it. If it stays unexplained, exclude trips that overlap 19:00-20:59 from the headline results and show them separately.
- **Fuel model:** components may come from different cited sources (cruise, acceleration, idle) if units and vehicle class are consistent and each source is cited. The optimizer needs a cheap function per segment, so prefer closed-form models.

## Author decision after the builder check: private, not published
The author decided not to publish this project (the Crosswalk data overlaps a startup idea and data licenses are unchecked). It is built as a private project to show it can be demonstrated; the "published case study" goal above is on hold. Raw data stays out of the portfolio repo either way.

## Feasibility spike findings (2026-10-22, throwaway code in `~/Developer/busan-fuel-routing`)
- OSM extract of a box around Seomyeon (35.140-35.180 N, 129.040-129.085 E): 6,822 nodes, 13,661 directed edges, 82 traffic signals, one connected network. 11 of the 157 smart intersections lie in the box, 8 of them within 60 m of an OSM signal.
- Existing signal-cycle estimates range widely (10th/50th/90th percentile: 77/150/217 s), consistent with the doubts in the Crosswalk project; they are not a clean basis for assumed cycles.
- A time-expanded route-and-speed search over the box runs in about 0.3-0.7 s per query, so a sweep of many trips is computationally fine.
- Fuel coefficients: published values found for the Akcelik elemental/drag model (Toyota Corolla Ascent 2004, calibrated; Akcelik & Rahmi 2012, SIDRA TRIP slides, transportationgroup.nz): idle 889 mL/h, rolling A 12.2 mL/km, aero B 0.0036 (mL/km)/(km/h)^2, efficiency 0.0926 mL/kJ, mass 1250 kg. The per-km cruise formula idle/v + A + B v^2 is the assistant's reading of the drag-parameter definition and must be verified against the paper. The fuel-optimal cruise speed under it is about 50 km/h.
- Result on 60 simulated trips (6 origin-destination pairs 1.8-2.6 km apart, 5 departure offsets, 2 signal seeds; signals assumed: cycles 110-190 s, 50% green, random phases): versus a signal-blind fastest-route car, the fastest plan is about 15% quicker and uses about 17% less fuel; the least-fuel plan about 15% quicker and 19% less fuel. But the fastest and least-fuel plans differ by only about 3.3 s and 2.7 mL (about 2% of fuel) on average, and differ at all on 33 of 60 trips, so the time-versus-fuel curve is narrow in this setup.
- Caveat: the planner knows every signal's exact phase, so these gains are an upper bound. The next test is phase uncertainty, which is also where forecasting should matter and may widen the trade-off.
- Volume forecasting: on 7 held-out full days, the residual of one hour correlates 0.87 with the next hour, and adding half of the last residual cuts MAE from 312 to 201 vehicles/hour. Continuous re-forecasting of volume is plausible.
- Delay data is dirty: 49% of records are 0 s, median 2 s, maximum 95,723 s. Residual statistics on it are not reliable until it is cleaned or capped.
- Phase-uncertainty test (60 trips, planner believes signal phases with error sigma, executed against true phases): versus the signal-blind fastest-route car, the fastest plan's saving falls from about 15% time / 17% fuel at sigma 0 to about 8% / 12% at sigma 20 s; it stays positive. The least-fuel plan costs more time than the fastest (3 s at sigma 0, 9-15 s at sigma 5-10 s) but saves essentially no extra fuel (within about 3 mL, noise level), so the time-versus-fuel curve does not widen under uncertainty; it collapses. A safety margin on the green window did not clearly help. Conclusion: in dense urban driving the fuel-optimal speed (about 50 km/h) is at or above the actual flow speed, so fuel-optimal and time-optimal plans nearly coincide; the robust finding is signal-aware planning versus signal-blind planning, not a wide three-model curve. A wide curve would need faster roads (expressway or arterial segments where driving slower than the limit saves fuel) in the box.
- Wider box with fast roads (arterials and expressways, 16,007 nodes, 293 signals; 10 trips of 4.8-6.7 km, signal-aware plans versus a signal-blind fastest-route car): fastest plan -7% time / -8% fuel, least-fuel plan -5% / -11%. Least-fuel versus fastest: +8 s for -7.9 mL (-2.9% fuel). A time-versus-fuel curve exists but is narrow (a few percent of fuel for well under a minute); an intermediate weighting often gets most of the fuel saving for little time. Only 10 trips, so treat as indicative.
- Real-time budget (this Mac, pure Python, one thread): one re-plan takes 0.02 s (under 700 m remaining), 0.16 s (about 1 km), 1.0 s (about 2 km), 2.1 s median and 5.6 s at the 95th percentile (3-4 km); peak memory about 590 MB. Whole trips of 7-12 minutes with a re-plan at each signal: 2-8 re-plans, 1.4-8.8 s of compute in total, at most 1.4 s per re-plan. Under an assumed compact encoding (9 B per upcoming signal, 1 B congestion factor per segment, 16 B header; the assistant's assumption, not a standard) an update is about 100-230 B and a whole trip 280-1,224 B. Cited network figures: 5G one-way latency under 7 ms (downlink, best case) to about 18 ms (uplink, worst case) (Rohde & Schwarz and test-and-measurement write-ups), LTE data interruption about 40 ms at a handover (Nokia Bell Labs). Compute time dominates network time by roughly 40-100x at this payload size. Not found: a measured SPaT message size, median LTE round-trip time, and radio/CPU power figures; the LTE energy paper (Huang et al., MobiSys 2012) says the long high-power tail is the key cost, its numbers are in the next bullet. CPU energy remains unmeasured.
- Radio energy per update (published model, not measured here): from Huang's thesis (Table 6.1 and 6.2; 2012 Verizon 4G LTE, HTC ThunderBolt): promotion 1,210.7 mW for 260 ms, tail 1,060 mW for 11.576 s, transfer 1,288 mW base plus 438 mW per Mbps uplink and 52 mW per Mbps downlink. One update of about 230 B each way at 1 Mbps costs about 0.3 J (promotion) + 0.007 J (transfer) + 12.3 J (tail) = about 12.6 J, so the tail is about 97% and payload size barely matters. Updates are 1-5 minutes apart, longer than the tail, so each pays in full: a trip with 2-8 updates costs about 25-100 J, versus about 636 J for holding the connection open for 10 minutes. Against the wide-box fuel saving (about 33 mL, roughly 1.1 MJ at an assumed 34 kJ/mL for gasoline, a general figure not sourced here) that is about 0.01%. Lever: fewer or batched updates (for example, update only when the forecast drifts), not smaller payloads. Caveats: 2012 hardware and network, 5G figures not found, payload encoding is the assistant's assumption.
- Search bug fixed along the way: a search for an origin-destination pair with no reachable path (one-way streets) never terminated; the search now has a 3,600 s horizon and pairs are checked for reachability first.

## Left to the builder
- The exact optimization model (a time-dependent, bi-objective route-and-speed problem; speeds can be discretized; waiting at signals follows from arrival time and cycle). Choice of exact algorithm or heuristic, and the way the Pareto curve is traced (weighted sum, epsilon-constraint, etc.).
- Which published fuel model to use, after checking its applicability and recording the source.
- How to convert bus-based speeds into car speeds and how to simulate trips (origin-destination sampling, number of trips, departure times).
- The exact bounding box, network cleaning, and how to attach hourly volume and delay to network arcs when only 157 intersections have it (nearest-intersection rule, interpolation, or a stated simpler assumption).
- Chart design and page structure, following the CFLP page.

## Open items
- Explain or exclude the 19-20:00 delay anomaly.
- Optionally recover coordinates for the 128 Firestore crossings (needs access to the Crosswalk Firestore) to increase overlap with real signal estimates.
- Confirm data licenses.

## Verification
- Forecast evaluation on held-out days, reported against the baseline.
- Fuel model checked on simple cases (for example, idle fuel for a known wait, fuel versus speed curve shape) before any experiment is reported.
- On every trip the fastest plan is no slower than the least-fuel plan, and the least-fuel plan uses no more fuel than the fastest; otherwise there is a bug.
- `npm test` and `astro build` pass; en/ko parity test passes; the new page renders without console errors at phone width.
