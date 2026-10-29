# Extracted verbatim from the working session that produced the case study (only this header was added).
# Run from last-mile-routing/ :  PYTHONPATH=. .venv/bin/python analysis/driver_vs_tsp.py
import random, json, multiprocessing as mp, numpy as np, lm
TT, ACT = lm.load_tt(), lm.load_actual(); ZONES, ST = lm.load_zones()
train, _ = lm.split(ACT); rids = random.Random(7).sample(train, 200)

def tsp(rid):
    ids, m = TT[rid]; ix = {s: i for i, s in enumerate(ids)}
    return rid, [ids[i] for i in lm.solve_tsp(m, ix[ACT[rid][0]], 1)]
with mp.get_context("fork").Pool(6) as p:
    TSP = dict(p.map(tsp, rids))

rk = lambda x: np.argsort(np.argsort(x))
def stats(rid, seq):
    ids, m = TT[rid]; ix = {s: i for i, s in enumerate(ids)}
    q = [ix[s] for s in seq]; dep, stops = q[0], q[1:]
    z = [ZONES[rid][ids[i]] for i in stops]
    edges = [m[a, b] for a, b in zip(q, q[1:] + q[:1])]
    rem, cur, nn = set(stops), dep, 0
    for nxt in stops[:-1]:
        nn += min(rem, key=lambda j: m[cur, j]) == nxt; rem.discard(nxt); cur = nxt
    e = np.sort(edges)[::-1]
    return dict(total=sum(edges), nn=nn/(len(stops)-1), zsw=sum(z[i]!=z[i+1] for i in range(len(z)-1)),
                maxedge=e[0], top10=e[:max(1, len(e)//10)].sum()/sum(edges), mean_edge=np.mean(edges),
                outin=np.corrcoef(np.arange(len(stops)), rk(m[dep, stops]))[0, 1],
                edgeset={frozenset((a, b)) for a, b in zip(q, q[1:] + q[:1])})
rows = {"driver": [], "tsp": []}
for rid in rids:
    rows["driver"].append(stats(rid, ACT[rid])); rows["tsp"].append(stats(rid, TSP[rid]))
f = lambda k, w: np.mean([r[k] for r in rows[w]])
print(f"{'metric':38s}{'driver':>10s}{'TSP':>10s}")
for k, name in [("total","total loop time (s)"),("mean_edge","mean edge time (s)"),("maxedge","longest edge (s)"),
                ("top10","time share of longest 10% edges"),("nn","next = nearest unvisited"),
                ("zsw","zone switches per route"),("outin","order vs depot distance (Spearman)")]:
    print(f"{name:38s}{f(k,'driver'):10.2f}{f(k,'tsp'):10.2f}")
ov = np.mean([len(d["edgeset"] & t["edgeset"]) / len(d["edgeset"]) for d, t in zip(rows["driver"], rows["tsp"])])
print(f"{'driver edges also used by TSP':38s}{ov:10.2f}")
