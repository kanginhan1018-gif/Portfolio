# Extracted verbatim from the working session that produced the case study (only this header was added).
# Run from last-mile-routing/ :  PYTHONPATH=. .venv/bin/python analysis/package_test.py
import json, random, multiprocessing as mp, numpy as np, pandas as pd, lm
ACT = lm.load_actual(); ZONES, ST = lm.load_zones(); TT = lm.load_tt()
pk = json.load(open(lm.DATA / "package_data.json"))
F = {}  # route -> {stop: (total volume, max volume, n packages, service seconds)}; the depot is excluded below
for rid, stops in pk.items():
    o = {}
    for s, pkgs in stops.items():
        v = [d["dimensions"]["depth_cm"] * d["dimensions"]["height_cm"] * d["dimensions"]["width_cm"] for d in pkgs.values()]
        o[s] = (np.nansum(v) if v else np.nan, np.nanmax(v) if v else np.nan, len(v), sum(d["planned_service_time_seconds"] for d in pkgs.values()))
    F[rid] = o
del pk
assert all(len(F[r]) == len(ACT[r]) for r in ACT), "package stops should be route stops incl. depot"
assert all(F[r][ACT[r][0]][2] == 0 for r in ACT), "depot should hold 0 packages"
NAMES = ["total volume", "largest package", "n packages", "service time"]
def rho(order, rid):
    """Spearman (ranks, then Pearson) between visit position of delivery stops (depot excluded) and each feature."""
    st = list(order[1:]); pos = pd.Series(np.arange(len(st)), dtype=float)
    return [pos.rank().corr(pd.Series([F[rid][s][k] for s in st], dtype=float).rank()) for k in range(4)]
def top_pos(order, rid, q=0.9):
    st = list(order[1:]); mx = np.array([F[rid][s][1] for s in st]); pos = np.arange(len(st)) / (len(st) - 1)
    return np.nanmean(pos[mx >= np.nanquantile(mx, q)])
train, val = lm.split(ACT)
R = {r: rho(ACT[r], r) for r in ACT}
print("DRIVER, mean Spearman(visit order, feature) over routes (se); + = later; n routes")
for name, grp in [("all", list(ACT)), ("train", train), ("validation", val)]:
    a = np.array([R[r] for r in grp], float)
    print(f"  {name:11s} n={len(grp):5d} " + "  ".join(f"{NAMES[k]}: {np.nanmean(a[:,k]):+.3f} ({np.nanstd(a[:,k])/np.sqrt(len(a)):.3f})" for k in range(4)), flush=True)
rng = random.Random(0)
def shuffled(rid): o = ACT[rid][1:]; rng.shuffle(o); return [ACT[rid][0]] + o
a = np.array([rho(shuffled(r), r) for r in ACT], float)
print("RANDOM order, all routes (null check, should be ~0): " + "  ".join(f"{NAMES[k]}: {np.nanmean(a[:,k]):+.4f} ({np.nanstd(a[:,k])/np.sqrt(len(a)):.4f})" for k in range(4)), flush=True)
sample = random.Random(11).sample(sorted(ACT), 300)
def tsp(args):
    rid, P = args; ids, m = TT[rid]; ix = {s: i for i, s in enumerate(ids)}
    return [ids[i] for i in lm.solve_tsp(lm.zone_penalty(m, ids, ZONES[rid], P), ix[ACT[rid][0]], 1)]
with mp.get_context("fork").Pool(6) as p:
    T0 = p.map(tsp, [(r, 0) for r in sample]); T1 = p.map(tsp, [(r, 1000) for r in sample])
orders = {"driver": [ACT[r] for r in sample], "TSP": T0, "zone-TSP (P=1000)": T1, "random order": [shuffled(r) for r in sample]}
print("\nCONTROLS on 300 routes (same routes for every row)")
print(f"{'order':20s}" + "".join(f"{n:>17s}" for n in NAMES) + f"{'top-decile pos':>16s}")
res = {}
for name, od in orders.items():
    a = np.array([rho(o, r) for o, r in zip(od, sample)], float); tp = np.array([top_pos(o, r) for o, r in zip(od, sample)])
    res[name] = (a, tp)
    print(f"{name:20s}" + "".join(f"{np.nanmean(a[:,k]):+10.3f}({np.nanstd(a[:,k])/np.sqrt(300):.3f})" for k in range(4)) + f"{np.nanmean(tp):10.3f}({np.nanstd(tp)/np.sqrt(300):.3f})")
print("\ndriver minus control, paired (mean +- se):")
for c in ["TSP", "zone-TSP (P=1000)", "random order"]:
    d = res["driver"][0] - res[c][0]; dt = res["driver"][1] - res[c][1]
    print(f"  vs {c:19s}" + "  ".join(f"{NAMES[k]}: {np.nanmean(d[:,k]):+.3f}+-{np.nanstd(d[:,k])/np.sqrt(300):.3f}" for k in range(4)) + f"  top-decile pos: {np.nanmean(dt):+.3f}+-{np.nanstd(dt)/np.sqrt(300):.3f}")
