"""Baseline 1: plain TSP on travel time vs. the driver's sequence.

Usage: .venv/bin/python run_baseline.py [n_routes=300] [seconds_per_route=1]
Writes results/baseline_tsp.csv and prints mean official score (lower = closer to drivers).
"""
import csv
import json
import os
import pickle
import random
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import lm

TT, ACT = lm.load_tt(), lm.load_actual()
ZONES, STATION = lm.load_zones()
TRAIN, VAL = lm.split(ACT)  # transitions are learned on TRAIN only, scored on VAL
DEV = bool(os.environ.get("DEV"))  # DEV=1: tune on a dev split inside TRAIN, validation untouched
if DEV:
    TRAIN, VAL = lm.split_dev(TRAIN)
ALPHA = float(os.environ.get("ALPHA", 0.5))  # additive smoothing of the zone-transition model
GEO = tuple(map(float, os.environ["GEO"].split(","))) if os.environ.get("GEO") else None  # "tau,beta": geographic prior for unseen pairs
TRANS, VOCAB = lm.fit_transitions(TRAIN, ACT, ZONES, STATION)
SECONDS = int(sys.argv[2]) if len(sys.argv) > 2 else 1
P = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0  # zone-switch penalty in seconds; 0 = plain TSP
LAM = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0  # weight of learned zone-transition NLL, seconds per nat
TAG = sys.argv[5] if len(sys.argv) > 5 else ""  # learned zone-pair costs: data/theta_<TAG>.pkl from train_perceptron.py
THETA = pickle.load(open(lm.DATA / f"theta_{TAG}.pkl", "rb")) if TAG else None


def loop_time(order, m):
    return sum(m[a, b] for a, b in zip(order, order[1:] + order[:1]))


def one(rid):
    ids, m = TT[rid]
    ix = {s: i for i, s in enumerate(ids)}
    actual = ACT[rid]
    cost = lm.zone_penalty(m, ids, ZONES[rid], P)
    if THETA:  # with a theta tag, LAM scales theta (default 1)
        cost = cost + (LAM or 1.0) * lm.theta_matrix(ids, ZONES[rid], STATION[rid], THETA)
    elif LAM and GEO:
        cost = cost + LAM * lm.nll_matrix_geo(ids, ZONES[rid], STATION[rid], TRANS, m, *GEO)
    elif LAM:
        cost = cost + LAM * lm.nll_matrix(ids, ZONES[rid], STATION[rid], TRANS, VOCAB, ALPHA)
    order = lm.solve_tsp(cost, ix[actual[0]], SECONDS)
    sub = [ids[i] for i in order]
    return dict(
        route_id=rid,
        n_stops=len(ids),
        score=lm.route_score(actual, sub, ids, m),
        actual_time=loop_time([ix[s] for s in actual], m),
        tsp_time=loop_time(order, m),  # true time on the unpenalised matrix
    )


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    quality = {r: v["route_score"] for r, v in json.load(open(lm.DATA / "route_data.json")).items()}
    rids = random.Random(0).sample(VAL, n)
    with Pool() as p:
        rows = p.map(one, rids)
    for r in rows:
        r["quality"] = quality[r["route_id"]]
    Path("results").mkdir(exist_ok=True)
    with open(f"results/{'dev' if DEV else 'val'}_P{P:g}_L{LAM:g}_a{ALPHA:g}{'_geo%g_%g' % GEO if GEO else ''}{'_' + TAG if TAG else ''}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["route_id", "quality", "n_stops", "score", "actual_time", "tsp_time"])
        w.writeheader()
        w.writerows(rows)
    print(f"{'DEV' if DEV else 'VAL'} P={P:g} lam={LAM:g} alpha={ALPHA:g} geo={GEO or '-'} theta={TAG or '-'} n={n}  mean score={np.mean([r['score'] for r in rows]):.4f}  "
          f"driver/model time={np.mean([r['actual_time'] / r['tsp_time'] for r in rows]):.3f}")
    for q in ("High", "Medium", "Low"):
        s = [r for r in rows if r["quality"] == q]
        if s:
            print(f"  {q:6s} n={len(s):3d} score={np.mean([r['score'] for r in s]):.4f} "
                  f"driver/TSP time={np.mean([r['actual_time'] / r['tsp_time'] for r in s]):.3f}")
