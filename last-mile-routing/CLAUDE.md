# last-mile-routing

Amazon Last Mile Routing Research Challenge (2021, CC BY-NC 4.0, cite Amazon/MIT). Goal: learn hidden route costs
(hard-to-access areas, time-of-day effects) from driver sequences, then route with the corrected costs.
Scores use `ref/score.py` (official); `lm.py` is a faster equivalent checked by `test_lm.py`.

## Hardware: Apple Silicon — write and tune code for it

This machine is an **Apple M4 (arm64), 4 performance + 6 efficiency cores, 24 GB unified memory**.

- Use arm64-native wheels and tools only; no Rosetta/x86 binaries.
- `multiprocessing` on macOS uses **spawn**: each worker re-imports the module. `run_baseline.py` loads `tt.pkl`
  (1.1 GB) at import, so 10 workers hold about 11 GB of the 24 GB. Keep per-worker memory small
  (load only what a worker needs, or pass data in tasks like `train_perceptron.py` does).
- Pool size: the 6 efficiency cores are slower. `Pool()` defaults to 10 workers; benchmark 4 vs 10 before
  choosing, do not assume more is faster.
- OR-Tools searches under a wall-clock limit, so the same limit gives worse solutions on a slow core and results
  vary a little run to run. Compare settings on the same sample and read differences against the paired
  standard error.
- Prefer vectorised NumPy over Python loops. `lm.erp_per_edit` is a pure-Python double loop (about n² steps per
  route) and is the first thing to speed up if scoring becomes the bottleneck.
- Measure before optimising: time the step, then change it.

## Run

```
.venv/bin/python run_baseline.py <n_val_routes> <seconds> <P> <lambda> [theta_tag]
.venv/bin/python train_perceptron.py [all|High|Medium] [epochs] [eta]
PYTHONPATH=ref .venv/bin/python test_lm.py
```

`data/` and `.venv/` are gitignored (data is about 2.3 GB). Validation routes are never used for learning.
