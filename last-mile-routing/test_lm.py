"""Fast ERP/score must equal the official ref/score.py. Run: .venv/bin/python test_lm.py"""
import random

import numpy as np

import lm
import score as ref

rng = random.Random(0)
for trial in range(40):
    n = rng.randint(3, 9)
    ids = [chr(65 + i) * 2 for i in range(n)]
    m = np.array([[0 if i == j else rng.choice([1, 2, 2, 3, 5, 8]) * 1.0 for j in range(n)] for i in range(n)])
    actual = ids[:]
    sub = [ids[0]] + rng.sample(ids[1:], n - 1)
    A, B = actual + [actual[0]], sub + [sub[0]]
    mat = {o: {d: float(m[i, j]) for j, d in enumerate(ids)} for i, o in enumerate(ids)}
    want = ref.score(A, B, mat)  # small integer times -> many exact ties, exercises tie-breaking
    got = lm.route_score(actual, sub, ids, m)
    assert abs(want - got) < 1e-9, (trial, want, got)

assert lm.route_score(ids, ids, ids, m) == 0
print("ok: fast score matches ref/score.py on 40 random cases")
