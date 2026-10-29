"""Learn per-station zone-pair cost corrections so that driver zone orders become optimal.

Zone-level structured perceptron (batch, averaged): solve each training route's zone TSP under
cost = mean zone-to-zone time + theta, then lower theta on transitions drivers use more than the
solver and raise it on the ones the solver uses more.

Usage: .venv/bin/python train_perceptron.py [filter=all|High|Medium] [epochs=6] [eta=30]
Writes data/theta_<filter>.pkl: {station: {(zone_a, zone_b): seconds}}, depot zone = ''.
"""
import json
import pickle
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool

import numpy as np

import lm


def solve_zone(task):
    uz, Z, th = task
    C = Z + np.array([[th.get((a, b), 0.0) for b in uz] for a in uz])
    order = lm.solve_tsp(C, uz.index(""), 0.1)
    z = [uz[i] for i in order] + [""]
    return Counter(zip(z, z[1:]))


if __name__ == "__main__":
    flt = sys.argv[1] if len(sys.argv) > 1 else "all"
    epochs = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    eta = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0

    TT, ACT = lm.load_tt(), lm.load_actual()
    ZONES, STATION = lm.load_zones()
    quality = {r: v["route_score"] for r, v in json.load(open(lm.DATA / "route_data.json")).items()}
    train, _ = lm.split(ACT)  # validation routes are never touched
    if flt != "all":
        train = [r for r in train if quality[r] == flt]

    jobs, D = [], defaultdict(Counter)
    for rid in train:
        ids, m = TT[rid]
        uz, Z = lm.zone_costs(ids, ZONES[rid], m)
        jobs.append((STATION[rid], uz, Z))
        zs = lm.zone_seq(ACT[rid], ZONES[rid])
        D[STATION[rid]].update(zip(zs, zs[1:]))
    del TT
    total = sum(sum(c.values()) for c in D.values())

    TH, AVG = defaultdict(dict), defaultdict(lambda: defaultdict(float))
    with Pool() as pool:
        for ep in range(epochs):
            res = pool.map(solve_zone, [(uz, Z, TH[st]) for st, uz, Z in jobs], chunksize=50)
            S = defaultdict(Counter)
            for (st, _, _), c in zip(jobs, res):
                S[st].update(c)
            hit = sum(min(S[s][p], D[s][p]) for s in D for p in D[s])
            print(f"epoch {ep + 1}: driver zone transitions reproduced {hit / total:.3f}", flush=True)
            for st in D:
                for p in set(D[st]) | set(S[st]):
                    d, s = D[st][p], S[st][p]
                    TH[st][p] = TH[st].get(p, 0.0) - eta * (d - s) / (d + s + 1)
            for st in TH:
                for p, v in TH[st].items():
                    AVG[st][p] += v

    theta = {st: {p: v / epochs for p, v in d.items()} for st, d in AVG.items()}
    pickle.dump(theta, open(lm.DATA / f"theta_{flt}.pkl", "wb"))
    print(f"saved data/theta_{flt}.pkl: {sum(len(d) for d in theta.values())} zone pairs, {len(theta)} stations")
