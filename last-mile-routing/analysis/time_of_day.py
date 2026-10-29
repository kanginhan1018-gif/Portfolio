# Extracted verbatim from the working session that produced the case study (only this header was added).
# Run from last-mile-routing/ :  PYTHONPATH=. .venv/bin/python analysis/time_of_day.py
import json, random, collections
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import numpy as np, lm
rd = json.load(open(lm.DATA / "route_data.json")); ACT = lm.load_actual(); ZONES, ST = lm.load_zones()
TZ = {"LA": "America/Los_Angeles", "SE": "America/Los_Angeles", "AU": "America/Chicago", "BO": "America/New_York", "CH": "America/Chicago"}
info = {}
for r, d in rd.items():
    dt = datetime.strptime(d["date_YYYY_MM_DD"] + " " + d["departure_time_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(ZoneInfo(TZ[d["station_code"][1:3]]))
    info[r] = dict(h=dt.hour + dt.minute / 60, wd=dt.weekday())
train, val = lm.split(ACT); T, V = lm.fit_transitions(train, ACT, ZONES, ST)
qs = {s: np.percentile([info[r]["h"] for r in train if ST[r] == s], [33.3, 66.7]) for s in set(ST.values())}
rng = random.Random(0); shuf = {r: rng.randrange(3) for r in ACT}
BF = {"none (one bucket)": lambda r: 0, "hour (station terciles)": lambda r: int(np.searchsorted(qs[ST[r]], info[r]["h"])),
      "weekday vs weekend": lambda r: int(info[r]["wd"] >= 5), "weekday (7)": lambda r: info[r]["wd"], "shuffled (3)": lambda r: shuf[r]}
p0 = lambda st, a, b, al=.5: (T[st][a][b] + al) / (sum(T[st][a].values()) + al * max(len(V[st]), 1))
def fit(bf):
    C = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for r in train:
        z = lm.zone_seq(ACT[r], ZONES[r])
        for x, y in zip(z, z[1:]): C[(ST[r], bf(r))][x][y] += 1
    return C
def nll(r, bf, C, kappa):
    z = lm.zone_seq(ACT[r], ZONES[r]); o = []
    for a, b in zip(z, z[1:]):
        c = C[(ST[r], bf(r))][a]; o.append(-np.log((c[b] + kappa * p0(ST[r], a, b)) / (sum(c.values()) + kappa)))
    return np.mean(o)
for kappa in (5, 20):
    res = {k: np.array([nll(r, bf, fit(bf), kappa) for r in val]) if False else None for k, bf in BF.items()}
    for k, bf in BF.items():
        C = fit(bf); res[k] = np.array([nll(r, bf, C, kappa) for r in val])
    base = res["none (one bucket)"]
    print(f"\nkappa={kappa}: held-out NLL per zone transition (lower is better), n={len(val)} routes; one-bucket baseline {base.mean():.4f}")
    for k, v in res.items():
        d = base - v; print(f"  {k:26s} {v.mean():.4f}  vs baseline {d.mean():+.4f} +- {d.std()/len(d)**.5:.4f}  routes better {100*(d>0).mean():.0f}%")
