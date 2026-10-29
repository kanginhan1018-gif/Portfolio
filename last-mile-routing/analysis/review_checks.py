"""Checks added after an external critical review of the case study.

  tsp        how far is the 1 s guided-local-search tour from a 20 s one (convergence proxy; no optimality gap)
  zone-null  does 'driver stays in the zone' exceed what the number of near candidates alone would give?
  windows    time-window order correlation with proper tie ranks and a random-order null
  windows-control  the same statistic on TSP, zone-TSP and random orders (is it just geography?)
  ends       first 15% vs last 15% of stops: planned service time and package volume (Guo, Mo, Wang 2023)
  quality    zone-first strength by route quality label (station-adjusted OLS) and by station

Usage (from last-mile-routing/): .venv/bin/python analysis/review_checks.py tsp|zone-null|windows|windows-control|ends|quality
"""
import json
import multiprocessing as mp
from collections import Counter, defaultdict
import random
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lm  # noqa: E402

which = sys.argv[1]
ACT = lm.load_actual()


def loop_time(order, m):
    return sum(m[a, b] for a, b in zip(order, order[1:] + order[:1]))


if which == "tsp":
    TT = lm.load_tt()
    _, val = lm.split(ACT)
    rids = random.Random(21).sample(val, 40)

    def solve(rid):
        ids, m = TT[rid]
        d = ids.index(ACT[rid][0])
        return rid, loop_time(lm.solve_tsp(m, d, 1), m), loop_time(lm.solve_tsp(m, d, 20), m)

    with mp.get_context("fork").Pool(6) as p:
        rows = p.map(solve, rids)
    gain = np.array([(a - b) / a for _, a, b in rows])
    print(f"{len(rows)} validation routes, plain TSP, tour time at 1 s vs 20 s of guided local search")
    print(f"20 s tour shorter by mean {100 * gain.mean():.2f}% (max {100 * gain.max():.2f}%, routes improved >0.5%: {(gain > 0.005).sum()}, worse: {(gain < -1e-9).sum()})")

elif which == "zone-null":
    TT = lm.load_tt()
    ZONES, _ = lm.load_zones()
    rids = random.Random(8).sample(sorted(ACT), 1500)  # same sample as the step-level analysis in the post
    for factor in (1.5, 3.0):
        obs, null, n_cand = [], [], []
        for rid in rids:
            ids, m = TT[rid]
            ix = {s: i for i, s in enumerate(ids)}
            q = [ix[s] for s in ACT[rid]]
            z = np.array([ZONES[rid][s] or "" for s in ids])
            rem = np.ones(len(ids), bool)
            rem[q[0]] = False
            for k in range(1, len(q) - 1):
                c, nxt = q[k], q[k + 1]
                rem[c] = False
                r = np.where(rem)[0]
                t = m[c, r]
                if t.min() <= 0:
                    continue
                w = t <= factor * t.min()  # candidates about as close as the closest one
                same = z[r[w]] == z[c]
                if same.all() or (~same).all():
                    continue
                obs.append(z[nxt] == z[c])
                null.append(same.mean())
                n_cand.append(w.sum())
        obs, null = np.array(obs, float), np.array(null)
        print(f"\nwindow = candidates within {factor}x of the nearest remaining stop; steps with both same- and other-zone candidates: {len(obs)}")
        print(f"driver stays in zone: {100 * obs.mean():.1f}%   expected if the driver picked uniformly among those candidates: {100 * null.mean():.1f}%")
        for lo, hi in [(0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 1.01)]:
            s = (null >= lo) & (null < hi)
            if s.sum():
                print(f"   share of same-zone among candidates {lo:.1f}-{min(hi, 1):.1f}: n={s.sum():6d}  expected {100 * null[s].mean():5.1f}%  observed {100 * obs[s].mean():5.1f}%")

elif which == "windows":
    rd = json.load(open(lm.DATA / "route_data.json"))
    pk = json.load(open(lm.DATA / "package_data.json"))
    f = lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timestamp()
    rng = random.Random(0)
    obs, nul, nwin = [], [], []
    for rid, stops in pk.items():
        pos = {s: p for p, s in enumerate(ACT[rid][1:])}
        end = {}
        for s, pkgs in stops.items():
            ws = [d["time_window"]["end_time_utc"] for d in pkgs.values() if isinstance(d["time_window"]["end_time_utc"], str)]
            if ws and s in pos:
                end[s] = min(f(w) for w in ws)
        if len(end) < 5 or len(set(end.values())) < 3:
            continue
        st = list(end)
        e = pd.Series([end[s] for s in st]).rank()  # average ranks for ties
        p = np.array([pos[s] for s in st], float)
        obs.append(e.corr(pd.Series(p).rank()))
        nul.append(e.corr(pd.Series(rng.sample(range(len(pos)), len(st))).rank()))  # random positions, same tie structure
        nwin.append(len(st))
    obs, nul = np.array(obs), np.array(nul)
    print(f"routes with >=5 windowed stops and >=3 distinct window ends: {len(obs)}  (windowed stops/route: mean {np.mean(nwin):.1f})")
    print(f"driver order vs window end: mean rho {obs.mean():+.3f} (se {obs.std() / np.sqrt(len(obs)):.3f}); share rho>0.3: {100 * (obs > .3).mean():.0f}%, <-0.3: {100 * (obs < -.3).mean():.0f}%")
    print(f"random positions (null):    mean rho {nul.mean():+.3f} (se {nul.std() / np.sqrt(len(nul)):.3f}); share rho>0.3: {100 * (nul > .3).mean():.0f}%, <-0.3: {100 * (nul < -.3).mean():.0f}%")

elif which == "windows-control":
    # is the window/order correlation just geography? same statistic on TSP and zone-TSP orders of the same routes
    TT = lm.load_tt()
    ZONES, _ = lm.load_zones()
    pk = json.load(open(lm.DATA / "package_data.json"))
    f = lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timestamp()

    def window_ends(rid):
        out = {}
        for s, pkgs in pk[rid].items():
            ws = [d["time_window"]["end_time_utc"] for d in pkgs.values() if isinstance(d["time_window"]["end_time_utc"], str)]
            if ws:
                out[s] = min(f(w) for w in ws)
        return out

    sample = [r for r in random.Random(11).sample(sorted(ACT), 400) if len(window_ends(r)) >= 5 and len(set(window_ends(r).values())) >= 3]

    def tsp(a):
        rid, P = a
        ids, m = TT[rid]
        return [ids[i] for i in lm.solve_tsp(lm.zone_penalty(m, ids, ZONES[rid], P), ids.index(ACT[rid][0]), 1)]

    with mp.get_context("fork").Pool(6) as p:
        T0 = p.map(tsp, [(r, 0) for r in sample])
        T1 = p.map(tsp, [(r, 1000) for r in sample])
    rng = random.Random(3)

    def shuffled(rid):
        o = ACT[rid][1:]
        rng.shuffle(o)
        return [ACT[rid][0]] + o

    def rho(order, rid):
        end = window_ends(rid)
        pos = {s: p for p, s in enumerate(order[1:])}
        st = [s for s in end if s in pos]
        return pd.Series([end[s] for s in st]).rank().corr(pd.Series([pos[s] for s in st], dtype=float).rank())

    orders = {"driver": [ACT[r] for r in sample], "TSP": T0, "zone-TSP (P=1000)": T1, "random order": [shuffled(r) for r in sample]}
    res = {k: np.array([rho(o, r) for o, r in zip(v, sample)]) for k, v in orders.items()}
    print(f"{len(sample)} routes with windows; mean rho (window end vs visit position), se across routes")
    for k, a in res.items():
        print(f"  {k:20s} {a.mean():+.3f} ({a.std() / np.sqrt(len(a)):.3f})")
    for c in ("TSP", "zone-TSP (P=1000)", "random order"):
        d = res["driver"] - res[c]
        print(f"  driver minus {c:19s} {d.mean():+.3f} +- {d.std() / np.sqrt(len(d)):.3f}")

elif which == "ends":
    # Guo, Mo, Wang (2023) report that drivers do stops with longer planned service time and larger packages
    # in the first part of a route. Compare the first 15% of delivery stops with the last 15% (their statistic).
    pk = json.load(open(lm.DATA / "package_data.json"))
    rng = random.Random(0)
    feat = {}
    for rid, stops in pk.items():
        feat[rid] = {
            s: (sum(d["planned_service_time_seconds"] for d in p.values()) / max(len(p), 1),
                sum(d["dimensions"]["depth_cm"] * d["dimensions"]["height_cm"] * d["dimensions"]["width_cm"] for d in p.values()))
            for s, p in stops.items()
        }

    def stat(order_of, k):
        first_bigger, ratio_hi = [], []
        for rid in ACT:
            st = [s for s in order_of(rid)[1:] if s in feat[rid]]
            n = max(int(0.15 * len(st)), 1)
            f = [feat[rid][s][k] for s in st]
            a, b = (np.nanmean(f[:n]), np.nanmean(f[-n:])) if k == 0 else (np.nansum(f[:n]), np.nansum(f[-n:]))
            if np.isfinite(a) and np.isfinite(b) and a != b:
                first_bigger.append(a > b)
                ratio_hi.append(b / a >= (1.22 if k == 0 else 3) if a > 0 else True)
        fb = np.array(first_bigger, float)
        return len(fb), fb.mean(), fb.std() / np.sqrt(len(fb)), np.mean(ratio_hi)

    def shuffled(rid):
        o = ACT[rid][1:]
        rng.shuffle(o)
        return [ACT[rid][0]] + o

    print("share of routes whose first 15% of stops has a larger value than the last 15%   (n, share, se, share with last/first >= paper threshold)")
    for k, name in ((0, "mean planned service time (threshold 1.22)"), (1, "total package volume (threshold 3)")):
        for label, fn in (("driver", lambda r: ACT[r]), ("random order", shuffled)):
            n, m, se, hi = stat(fn, k)
            print(f"  {name:45s} {label:13s} n={n}  {100 * m:.1f}% (se {100 * se:.1f})  last/first>=thr: {100 * hi:.1f}%")

elif which == "quality":
    # is zone-first stronger in routes Amazon labelled High? (labels reflect defects, customer satisfaction, productivity)
    TT = lm.load_tt()
    ZONES, STATION = lm.load_zones()
    quality = {r: v["route_score"] for r, v in json.load(open(lm.DATA / "route_data.json")).items()}
    rows = []
    for rid in ACT:
        ids, m = TT[rid]
        ix = {s: i for i, s in enumerate(ids)}
        q = [ix[s] for s in ACT[rid]]
        z = np.array([ZONES[rid][s] or "" for s in ids])
        zs = lm.zone_seq(ACT[rid], ZONES[rid])[1:-1]  # drop the depot at both ends
        rem = np.ones(len(ids), bool)
        rem[q[0]] = False
        n_closer = stay_closer = 0  # steps where another zone's nearest stop is closer than the nearest in the current zone
        for k in range(1, len(q) - 1):
            c, nxt = q[k], q[k + 1]
            rem[c] = False
            r = np.where(rem)[0]
            same = z[r] == z[c]
            if same.all() or (~same).all():
                continue
            a, b = m[c, r[same]].min(), m[c, r[~same]].min()
            if a <= 0 or b <= 0 or b >= a:
                continue
            n_closer += 1
            stay_closer += z[nxt] == z[c]
        rows.append((rid, STATION[rid], quality[rid], len(zs) - len(set(zs)), n_closer, stay_closer))
    df = pd.DataFrame(rows, columns=["rid", "station", "quality", "reentry", "n_closer", "stay_closer"])
    df["contig"] = (df.reentry == 0).astype(float)
    df["rate"] = np.where(df.n_closer >= 3, df.stay_closer / df.n_closer.clip(lower=1), np.nan)
    print("by route quality label (all 6,112 routes)")
    print(f"{'label':8s}{'routes':>8s}{'zone re-entries/route':>24s}{'fully contiguous':>18s}{'steps':>9s}{'stay when other zone closer':>30s}")
    for lab in ("High", "Medium", "Low"):
        d = df[df.quality == lab]
        print(f"{lab:8s}{len(d):8d}{d.reentry.mean():17.2f} ({d.reentry.std() / np.sqrt(len(d)):.2f}){100 * d.contig.mean():17.1f}%{d.n_closer.sum():9d}{100 * d.stay_closer.sum() / d.n_closer.sum():29.1f}%")

    def adjusted(col):
        """OLS with a dummy per station plus High and Low indicators (Medium = baseline)."""
        d = df.dropna(subset=[col])
        X = pd.get_dummies(d.station).astype(float)
        X["High"] = (d.quality == "High").astype(float)
        X["Low"] = (d.quality == "Low").astype(float)
        A, y = X.values, d[col].values
        beta = np.linalg.lstsq(A, y, rcond=None)[0]
        res = y - A @ beta
        cov = (res @ res / (len(y) - A.shape[1])) * np.linalg.inv(A.T @ A)
        i = {c: j for j, c in enumerate(X.columns)}
        return [(beta[i[c]], np.sqrt(cov[i[c], i[c]])) for c in ("High", "Low")], len(d)

    print("\nstation-adjusted difference vs Medium routes (OLS, station dummies; se from OLS, routes treated as independent)")
    for col, name in (("reentry", "zone re-entries per route"), ("contig", "share fully zone-contiguous"), ("rate", "stay rate when other zone closer")):
        (h, lo), n = adjusted(col)
        print(f"  {name:36s} n={n:5d}  High {h[0]:+.3f} (se {h[1]:.3f})   Low {lo[0]:+.3f} (se {lo[1]:.3f})")
    print("\nby station (heterogeneity)")
    print(f"{'station':8s}{'routes':>8s}{'re-entries/route':>18s}{'stay when other zone closer':>30s}{'High share':>12s}")
    for st, d in df.groupby("station"):
        print(f"{st:8s}{len(d):8d}{d.reentry.mean():18.2f}{100 * d.stay_closer.sum() / max(d.n_closer.sum(), 1):29.1f}%{100 * (d.quality == 'High').mean():11.0f}%")

elif which == "assignment":
    # Are zones assigned to drivers? Routes of the same station and day: do they share zones?
    # Null: pool that day's stops and deal them out to routes of the same sizes at random.
    rd = json.load(open(lm.DATA / "route_data.json"))
    ZONES, _ = lm.load_zones()
    groups = defaultdict(list)
    for rid, d in rd.items():
        groups[(d["station_code"], d["date_YYYY_MM_DD"])].append(rid)
    groups = {k: v for k, v in groups.items() if len(v) >= 2}
    rng = random.Random(0)
    level = {"full zone id": lambda z: z, "high-level part (before the dot)": lambda z: z.split(".")[0]}

    def measure(lists, lab):
        sets = [{lab(z) for z in zl} for zl in lists]
        inc = shared = 0
        for i, s in enumerate(sets):
            others = set().union(*[t for j, t in enumerate(sets) if j != i])
            inc += len(s)
            shared += len(s & others)
        cnt = defaultdict(Counter)
        for i, zl in enumerate(lists):
            for z in zl:
                cnt[lab(z)][i] += 1
        return inc, shared, sum(max(c.values()) for c in cnt.values()), sum(sum(c.values()) for c in cnt.values())

    obs = {k: np.zeros(4) for k in level}
    nul = {k: np.zeros(4) for k in level}
    for key, rids in groups.items():
        lists = [[ZONES[r][s] for s in ZONES[r] if ZONES[r][s]] for r in rids]
        sizes = [len(zl) for zl in lists]
        pool = [z for zl in lists for z in zl]
        for name, lab in level.items():
            obs[name] += measure(lists, lab)
            for _ in range(10):
                rng.shuffle(pool)
                cut, dealt = 0, []
                for n in sizes:
                    dealt.append(pool[cut:cut + n])
                    cut += n
                nul[name] += np.array(measure(dealt, lab)) / 10
    print(f"station-days with >=2 routes in the data: {len(groups)}  (routes in them: {sum(len(v) for v in groups.values())}, mean {np.mean([len(v) for v in groups.values()]):.1f} per day)")
    print("share of a route's zones that also appear in another route of the same station and day, and 'purity' = stops held by the route holding most of that zone's stops")
    for name in level:
        o, n = obs[name], nul[name]
        print(f"  {name:34s} shared zones: observed {100 * o[1] / o[0]:5.1f}%  random deal {100 * n[1] / n[0]:5.1f}%   purity: observed {100 * o[2] / o[3]:5.1f}%  random deal {100 * n[2] / n[3]:5.1f}%")
