"""Amazon Last Mile Routing Challenge: data loading, fast official scorer, TSP baseline.

The official scorer (ref/score.py) is memoised recursion over tuples, which is
too slow for 100+ stop routes. `erp_per_edit` below is the same recurrence as an
iterative DP, with the same tie-breaking, checked against ref/score.py in test_lm.py.
"""
import json
import pickle
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "ref"))
from score import seq_dev  # noqa: E402  (official, cheap enough)

DATA = Path(__file__).parent / "data"
G = 1000  # official ERP gap penalty


def load_tt():
    """route_id -> (stop ids, travel-time matrix). Built once from the 1.8GB JSON."""
    cache = DATA / "tt.pkl"
    if cache.exists():
        return pickle.load(open(cache, "rb"))
    import ijson

    out = {}
    with open(DATA / "travel_times.json", "rb") as f:
        for rid, d in ijson.kvitems(f, ""):
            ids = sorted(d)
            ix = {s: i for i, s in enumerate(ids)}
            m = np.zeros((len(ids), len(ids)))
            for o, row in d.items():
                for t, v in row.items():
                    m[ix[o], ix[t]] = float(v)
            out[rid] = (ids, m)
    pickle.dump(out, open(cache, "wb"))
    return out


def load_actual():
    """route_id -> stop ids in driver order, depot first."""
    a = json.load(open(DATA / "actual_sequences.json"))
    return {r: sorted(v["actual"], key=v["actual"].get) for r, v in a.items()}


def load_zones():
    """(route_id -> {stop id: zone id}, route_id -> station code). The depot's zone_id is NaN in the data, mapped to None."""
    r = json.load(open(DATA / "route_data.json"))
    zones = {
        rid: {s: (v["zone_id"] if isinstance(v["zone_id"], str) else None) for s, v in d["stops"].items()}
        for rid, d in r.items()
    }
    return zones, {rid: d["station_code"] for rid, d in r.items()}


def split(rids, frac=0.8):
    """Deterministic train/validation split by route."""
    r = sorted(rids)
    random.Random(1).shuffle(r)
    k = int(len(r) * frac)
    return r[:k], r[k:]


def zone_seq(seq, zr):
    """Zone sequence of a stop sequence (depot = '', closed back at the depot, stays inside a zone collapsed)."""
    z = [zr[s] or "" for s in seq] + [""]
    return [x for i, x in enumerate(z) if i == 0 or x != z[i - 1]]


def zone_costs(ids, zr, m):
    """(zone list, mean stop-to-stop time between zones); the depot is zone ''."""
    z = np.array([zr[s] or "" for s in ids])
    uz = sorted(set(z))
    return uz, np.array([[m[np.ix_(z == a, z == b)].mean() for b in uz] for a in uz])


def nll_matrix_geo(ids, zr, st, T, m, tau, beta):
    """Like nll_matrix, but a zone pair never seen in training falls back on a geographic prior instead of uniform.

    p(b|a) = (count(a->b) + beta * g(b|a)) / (total(a) + beta), g = softmax(-zone-to-zone time / tau) over this route's zones.
    """
    uz, Z = zone_costs(ids, zr, m)
    N = np.zeros((len(uz), len(uz)))
    for i, a in enumerate(uz):
        c = T[st][a]
        tot = sum(c.values())
        others = np.arange(len(uz)) != i
        w = np.where(others, np.exp(-(Z[i] - Z[i][others].min()) / tau), 0.0)
        g = w / w.sum()
        for j, b in enumerate(uz):
            if a != b:
                N[i, j] = -np.log((c[b] + beta * g[j]) / (tot + beta))
    z = [zr[s] or "" for s in ids]
    ix = np.array([uz.index(x) for x in z])
    return N[np.ix_(ix, ix)]


def theta_matrix(ids, zr, st, TH):
    """Learned per-station zone-pair cost correction (seconds) expanded to stop pairs; 0 inside a zone."""
    z = [zr[s] or "" for s in ids]
    uz = sorted(set(z))
    N = np.array([[0.0 if a == b else TH.get(st, {}).get((a, b), 0.0) for b in uz] for a in uz])
    ix = np.array([uz.index(x) for x in z])
    return N[np.ix_(ix, ix)]


def split_dev(train, frac=0.8):
    """Split the training routes again so hyper-parameters can be tuned without touching validation."""
    r = sorted(train)
    random.Random(2).shuffle(r)
    k = int(len(r) * frac)
    return r[:k], r[k:]


def fit_transitions(train, actual, zones, stations):
    """Per station: zone->zone transition counts from driver sequences (depot = zone ''), plus zone vocabulary."""
    T = defaultdict(lambda: defaultdict(Counter))
    V = defaultdict(set)
    for rid in train:
        z = zone_seq(actual[rid], zones[rid])
        V[stations[rid]].update(z)
        for a, b in zip(z, z[1:]):
            T[stations[rid]][a][b] += 1
    return T, V


def nll_matrix(ids, zr, st, T, V, alpha=0.5):
    """-log P(next zone | this zone) between stops, 0 inside a zone. Additive smoothing; unseen zones -> uniform."""
    z = [zr[s] or "" for s in ids]
    uz = sorted(set(z))
    k = max(len(V[st]), 1)
    N = np.zeros((len(uz), len(uz)))
    for i, a in enumerate(uz):
        c = T[st][a]
        tot = sum(c.values())
        for j, b in enumerate(uz):
            if a != b:
                N[i, j] = -np.log((c[b] + alpha) / (tot + alpha * k))
    ix = np.array([uz.index(x) for x in z])
    return N[np.ix_(ix, ix)]


def zone_penalty(m, ids, zones, P):
    """m + P wherever the two stops are in different zones (depot counts as its own zone)."""
    z = np.array([zones[s] or "" for s in ids])
    return m + P * (z[:, None] != z[None, :])


def normalize(m):
    """Official normalisation: z-score over all entries, then shift so min is 0."""
    z = (m - m.mean()) / m.std()
    return z - z.min()


def erp_per_edit(a, b, nm, g=G):
    """ERP / #edits between index sequences a (actual) and b (submitted), same recurrence as ref."""
    n, k = len(a), len(b)
    D = np.zeros((n + 1, k + 1))
    C = np.zeros((n + 1, k + 1), dtype=np.int64)
    D[:, k] = g * np.arange(n, -1, -1)
    C[:, k] = np.arange(n, -1, -1)
    D[n, :] = g * np.arange(k, -1, -1)
    C[n, :] = np.arange(k, -1, -1)
    for i in range(n - 1, -1, -1):
        for j in range(k - 1, -1, -1):
            o1 = D[i + 1, j + 1] + nm[a[i], b[j]]
            o2 = D[i + 1, j] + g
            o3 = D[i, j + 1] + g
            d = min(o1, o2, o3)
            if d == o1:
                c = C[i + 1, j + 1] + (a[i] != b[j])
            elif d == o2:
                c = C[i + 1, j] + 1
            else:
                c = C[i, j + 1] + 1
            D[i, j], C[i, j] = d, c
    return 0 if C[0, 0] == 0 else D[0, 0] / C[0, 0]


def route_score(actual, sub, ids, m):
    """Official per-route score (lower is better). actual/sub: stop-id lists, depot first, no return leg."""
    ix = {s: i for i, s in enumerate(ids)}
    A, B = actual + [actual[0]], sub + [sub[0]]  # ref's route2list closes the loop
    return seq_dev(A, B) * erp_per_edit([ix[s] for s in A], [ix[s] for s in B], normalize(m))


def solve_tsp(m, depot, seconds=1):
    """Closed TSP from `depot` on integer-rounded times (OR-Tools guided local search). Returns node order."""
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2

    n = len(m)
    mi = np.rint(m * 10).astype(int)
    mi = mi - min(mi.min(), 0)  # a constant shift keeps the optimal tour and avoids negative arc costs
    mgr = pywrapcp.RoutingIndexManager(n, 1, depot)
    r = pywrapcp.RoutingModel(mgr)
    cb = r.RegisterTransitCallback(lambda i, j: int(mi[mgr.IndexToNode(i), mgr.IndexToNode(j)]))
    r.SetArcCostEvaluatorOfAllVehicles(cb)
    p = pywrapcp.DefaultRoutingSearchParameters()
    p.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    p.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    p.time_limit.FromMilliseconds(int(seconds * 1000))
    sol = r.SolveWithParameters(p)
    i, order = r.Start(0), []  # vehicle 0 starts at depot
    while not r.IsEnd(i):
        order.append(mgr.IndexToNode(i))
        i = sol.Value(r.NextVar(i))
    return order
