# Extracted verbatim from the working session that produced the case study (only this header was added).
# Run from last-mile-routing/ :  PYTHONPATH=. .venv/bin/python analysis/zone_matched_time.py
import json, random, numpy as np, lm
ACT = lm.load_actual(); ZONES, ST = lm.load_zones(); TT = lm.load_tt(); rd = json.load(open(lm.DATA / "route_data.json"))
rids = random.Random(8).sample(sorted(ACT), 1500)
tb = [(0, 15), (15, 30), (30, 60), (60, 120), (120, 240)]
acc = {(b, s): [0, 0] for b in tb for s in (True, False)}  # pairs, back-to-back
for rid in rids:
    ids, m = TT[rid]; ix = {s: i for i, s in enumerate(ids)}; st = ACT[rid][1:]; pos = {ix[s]: p for p, s in enumerate(st)}
    z = np.array([ZONES[rid][s] or "" for s in ids]); dep = ix[ACT[rid][0]]; sym = (m + m.T) / 2
    iu = np.triu_indices(len(ids), 1)
    for i, j in zip(*iu):
        if i == dep or j == dep: continue
        for b in tb:
            if b[0] <= sym[i, j] < b[1]:
                c = acc[(b, z[i] == z[j])]; c[0] += 1; c[1] += abs(pos[i] - pos[j]) == 1
print("pairs matched on matrix travel time: how often does the driver visit them back-to-back?")
print(f"{'matrix time':>12s}{'same zone: pairs':>18s}{'back-to-back':>14s}{'other zone: pairs':>19s}{'back-to-back':>14s}{'ratio':>8s}")
for b in tb:
    (n1, a1), (n0, a0) = acc[(b, True)], acc[(b, False)]
    print(f"{b[0]:>5d}-{b[1]:<5d}s{n1:18d}{100*a1/n1:13.1f}%{n0:19d}{100*a0/n0:13.1f}%{(a1/n1)/(a0/n0):8.1f}")
