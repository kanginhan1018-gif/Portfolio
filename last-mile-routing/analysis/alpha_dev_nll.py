# Extracted verbatim from the working session that produced the case study (only this header was added).
# Run from last-mile-routing/ :  PYTHONPATH=. .venv/bin/python analysis/alpha_dev_nll.py
import random, numpy as np, lm
ACT = lm.load_actual(); ZONES, ST = lm.load_zones()
train, val = lm.split(ACT)
r = random.Random(2); tr = sorted(train); r.shuffle(tr); k = int(.8 * len(tr)); fit, dev = tr[:k], tr[k:]
T, V = lm.fit_transitions(fit, ACT, ZONES, ST)
print(f"fit {len(fit)} routes, dev {len(dev)} routes (inside the training split; validation untouched)")
print("alpha   dev NLL per zone transition   | share of dev transitions never seen in fit")
for al in (0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005, 0.002, 0.001):
    tot = n = unseen = 0
    for rid in dev:
        z = lm.zone_seq(ACT[rid], ZONES[rid]); st = ST[rid]; kk = max(len(V[st]), 1)
        for a, b in zip(z, z[1:]):
            c = T[st][a]; tot += -np.log((c[b] + al) / (sum(c.values()) + al * kk)); n += 1; unseen += c[b] == 0
    print(f"{al:6.3f}  {tot/n:8.4f}                     | {unseen/n:.3f}")
