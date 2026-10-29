# Extracted verbatim from the working session that produced the case study (only this header was added).
# Run from last-mile-routing/ :  PYTHONPATH=. .venv/bin/python analysis/time_of_day_kappa.py
import json, random, collections
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import numpy as np, lm
rd = json.load(open(lm.DATA / "route_data.json")); ACT = lm.load_actual(); ZONES, ST = lm.load_zones()
TZ = {"LA": "America/Los_Angeles", "SE": "America/Los_Angeles", "AU": "America/Chicago", "BO": "America/New_York", "CH": "America/Chicago"}
h = {}
for r, d in rd.items():
    dt = datetime.strptime(d["date_YYYY_MM_DD"] + " " + d["departure_time_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(ZoneInfo(TZ[d["station_code"][1:3]]))
    h[r] = dt.hour + dt.minute / 60
train, val = lm.split(ACT); T, V = lm.fit_transitions(train, ACT, ZONES, ST)
qs = {s: np.percentile([h[r] for r in train if ST[r] == s], [33.3, 66.7]) for s in set(ST.values())}
rng = random.Random(0); shuf = {r: rng.randrange(3) for r in ACT}
BF = {"one bucket": lambda r: 0, "hour terciles": lambda r: int(np.searchsorted(qs[ST[r]], h[r])), "shuffled 3": lambda r: shuf[r]}
p0 = lambda st, a, b, al=.5: (T[st][a][b] + al) / (sum(T[st][a].values()) + al * max(len(V[st]), 1))
def fit(bf):
    C = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for r in train:
        z = lm.zone_seq(ACT[r], ZONES[r])
        for x, y in zip(z, z[1:]): C[(ST[r], bf(r))][x][y] += 1
    return C
def nll(r, bf, C, k):
    z = lm.zone_seq(ACT[r], ZONES[r]); o = []
    for a, b in zip(z, z[1:]):
        c = C[(ST[r], bf(r))][a]; o.append(-np.log((c[b] + k * p0(ST[r], a, b)) / (sum(c.values()) + k)))
    return np.mean(o)
Cs = {k: fit(bf) for k, bf in BF.items()}
print("kappa  hour-minus-baseline (se)   shuffled-minus-baseline")
for k in (50, 200, 1000, 5000):
    r = {n: np.array([nll(x, BF[n], Cs[n], k) for x in val]) for n in BF}
    d = r["one bucket"] - r["hour terciles"]; s = r["one bucket"] - r["shuffled 3"]
    print(f"{k:5d}  {d.mean():+.4f} +- {d.std()/len(d)**.5:.4f}      {s.mean():+.4f}")
