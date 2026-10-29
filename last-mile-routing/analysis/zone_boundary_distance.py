# Extracted verbatim from the working session that produced the case study (only this header was added).
# Run from last-mile-routing/ :  PYTHONPATH=. .venv/bin/python analysis/zone_boundary_distance.py
import json, random, numpy as np, lm
ACT = lm.load_actual(); ZONES, ST = lm.load_zones(); TT = lm.load_tt(); rd = json.load(open(lm.DATA / "route_data.json"))
rids = random.Random(8).sample(sorted(ACT), 1500)
bins = [(0, 50), (50, 100), (100, 200), (200, 400)]
acc = {(b, same): dict(n=0, t=[], adj=0) for b in bins for same in (True, False)}
for rid in rids:
    ids, m = TT[rid]; ix = {s: i for i, s in enumerate(ids)}; st = ACT[rid][1:]
    ll = np.array([[rd[rid]["stops"][s]["lat"], rd[rid]["stops"][s]["lng"]] for s in ids]); z = np.array([ZONES[rid][s] or "" for s in ids])
    la, lo = np.radians(ll[:, 0]), np.radians(ll[:, 1])
    a = np.sin((la[:, None] - la[None]) / 2) ** 2 + np.cos(la)[:, None] * np.cos(la)[None] * np.sin((lo[:, None] - lo[None]) / 2) ** 2
    dist = 2 * 6371000 * np.arcsin(np.sqrt(a)); pos = {ix[s]: p for p, s in enumerate(st)}
    dep = ix[ACT[rid][0]]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if i == dep or j == dep: continue
            for b in bins:
                if b[0] <= dist[i, j] < b[1]:
                    d = acc[(b, z[i] == z[j])]; d["n"] += 1; d["t"].append((m[i, j] + m[j, i]) / 2); d["adj"] += abs(pos[i] - pos[j]) == 1
print("pairs of stops that are physically close (straight-line distance), by same/different zone")
print(f"{'distance':>10s}{'':>6s}{'pairs':>9s}{'matrix time (s) mean/median':>30s}{'visited back-to-back by driver':>34s}")
for b in bins:
    for same in (True, False):
        d = acc[(b, same)]; t = np.array(d["t"])
        print(f"{b[0]:>4d}-{b[1]:<4d}m {'same ' if same else 'other'}{d['n']:9d}{t.mean():20.0f}/{np.median(t):<6.0f}{100*d['adj']/d['n']:28.1f}%")
