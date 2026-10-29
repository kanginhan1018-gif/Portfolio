# Extracted verbatim from the working session that produced the case study (only this header was added).
# Run from last-mile-routing/ :  PYTHONPATH=. .venv/bin/python analysis/zone_choice_step.py
import random, numpy as np, lm
ACT = lm.load_actual(); ZONES, ST = lm.load_zones(); TT = lm.load_tt()
rids = random.Random(8).sample(sorted(ACT), 1500)
edges = [0, 0.25, 0.5, 0.8, 1.25, 2, 4, 8, np.inf]
cnt = np.zeros(len(edges) - 1); same = np.zeros(len(edges) - 1); steps = skipped = 0
for rid in rids:
    ids, m = TT[rid]; ix = {s: i for i, s in enumerate(ids)}; q = [ix[s] for s in ACT[rid]]
    z = np.array([ZONES[rid][s] or "" for s in ids]); rem = np.ones(len(ids), bool); rem[q[0]] = False
    for k in range(1, len(q) - 1):  # from the first delivery stop on; the step out of the depot is skipped
        c, nxt = q[k], q[k + 1]; rem[c] = False
        r = np.where(rem)[0]; sz = z[r] == z[c]
        steps += 1
        if sz.all() or (~sz).all(): skipped += 1; continue
        a, b = m[c, r[sz]].min(), m[c, r[~sz]].min()
        if a <= 0 or b <= 0: skipped += 1; continue
        i = np.searchsorted(edges, b / a, side="right") - 1
        cnt[i] += 1; same[i] += z[nxt] == z[c]
print(f"steps {steps}, usable {int(cnt.sum())} (skipped {skipped}: only one kind of candidate left)")
print("b/a = (time to nearest OTHER-zone stop) / (time to nearest SAME-zone stop); b/a < 1 means another zone is closer")
print(f"{'b/a':>12s}{'steps':>9s}{'driver stays in zone':>24s}")
for i in range(len(cnt)):
    hi = "inf" if np.isinf(edges[i + 1]) else f"{edges[i+1]:g}"
    print(f"{edges[i]:>6g}-{hi:<5s}{int(cnt[i]):9d}{100*same[i]/max(cnt[i],1):23.1f}%")
