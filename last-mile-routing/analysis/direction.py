# Extracted verbatim from the working session that produced the case study (only this header was added).
# Run from last-mile-routing/ :  PYTHONPATH=. .venv/bin/python analysis/direction.py
import json, random, multiprocessing as mp, numpy as np, pandas as pd, lm
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
ACT = lm.load_actual(); ZONES, ST = lm.load_zones(); TT = lm.load_tt(); rd = json.load(open(lm.DATA / "route_data.json"))
TZ = {"LA": "America/Los_Angeles", "SE": "America/Los_Angeles", "AU": "America/Chicago", "BO": "America/New_York", "CH": "America/Chicago"}
def direction(order, rid):
    """Spearman(visit order, travel time from depot) over delivery stops; + = outward over the route."""
    ids, m = TT[rid]; ix = {s: i for i, s in enumerate(ids)}; q = [ix[s] for s in order]
    return pd.Series(np.arange(len(q) - 1), dtype=float).rank().corr(pd.Series(m[q[0], q[1:]], dtype=float).rank())
D = {r: direction(ACT[r], r) for r in ACT}; d = np.array(list(D.values()))
print(f"driver direction rho over {len(d)} routes: mean {d.mean():+.3f}, sd {d.std():.3f}; outward(>0.3) {100*(d>0.3).mean():.0f}%, inward(<-0.3) {100*(d<-0.3).mean():.0f}%, middle {100*(abs(d)<=0.3).mean():.0f}%")
# 1) geometry control: does TSP direction predict driver direction?
sample = random.Random(11).sample(sorted(ACT), 300)
def tsp(a):
    rid, P = a; ids, m = TT[rid]; ix = {s: i for i, s in enumerate(ids)}
    return [ids[i] for i in lm.solve_tsp(lm.zone_penalty(m, ids, ZONES[rid], P), ix[ACT[rid][0]], 1)]
with mp.get_context("fork").Pool(6) as p:
    T0 = p.map(tsp, [(r, 0) for r in sample]); T1 = p.map(tsp, [(r, 1000) for r in sample])
dr = np.array([D[r] for r in sample])
for name, T in (("TSP", T0), ("zone-TSP", T1)):
    t = np.array([direction(o, r) for o, r in zip(T, sample)])
    agree = np.mean(np.sign(t) == np.sign(dr))
    print(f"{name:9s} direction vs driver direction (300 routes): corr {np.corrcoef(t, dr)[0,1]:+.3f}, same sign {100*agree:.0f}%")
# 2) can pre-route facts predict the driver's direction on held-out routes?
train, val = lm.split(ACT); stations = sorted(set(ST.values())); q = {"High": 0, "Medium": 1, "Low": 2}
def feats(r):
    ids, m = TT[r]; ix = {s: i for i, s in enumerate(ids)}; dep = ix[ACT[r][0]]; x = np.delete(m[dep], dep)
    dt = datetime.strptime(rd[r]["date_YYYY_MM_DD"] + " " + rd[r]["departure_time_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(ZoneInfo(TZ[ST[r][1:3]]))
    g = [x.mean() / 1000, x.std() / 1000, ((x - x.mean()) ** 3).mean() / x.std() ** 3, len(x) / 100, np.median(x) / 1000, x.min() / 1000]
    return dict(station=[float(ST[r] == s) for s in stations], geometry=g, calendar=[float(dt.weekday() == i) for i in range(7)] + [dt.hour + dt.minute / 60],
                quality=[float(rd[r]["route_score"] == k) for k in q])
Fx = {r: feats(r) for r in ACT}
def X(rs, groups): return np.array([[1.0] + sum((Fx[r][g] for g in groups), []) for r in rs])
y = lambda rs: np.array([D[r] for r in rs])
def auc(score, pos):
    rk = pd.Series(score).rank().values; n1, n0 = pos.sum(), (~pos).sum(); return (rk[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
print("\nheld-out prediction of the driver's direction (validation routes):")
for name, groups in [("station only", ["station"]), ("geometry only", ["geometry"]), ("calendar only", ["calendar"]), ("quality label only", ["quality"]),
                     ("station + geometry", ["station", "geometry"]), ("all", ["station", "geometry", "calendar", "quality"])]:
    A, B = X(train, groups), X(val, groups); w = np.linalg.solve(A.T @ A + 1e-3 * np.eye(A.shape[1]), A.T @ y(train)); pr = B @ w
    r2 = 1 - ((y(val) - pr) ** 2).sum() / ((y(val) - y(train).mean()) ** 2).sum()
    yv = y(val); sel = (yv > 0.3) | (yv < -0.3); a = auc(pr[sel], (yv > 0.3)[sel])
    print(f"  {name:20s} val R2 {r2:+.3f}   AUC outward-vs-inward {a:.3f} (n={sel.sum()})")
