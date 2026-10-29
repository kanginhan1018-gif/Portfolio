"""Figures for the portfolio case study. Numbers are copied from the run logs, not recomputed here:
results/final_val.log (scores, time ratios) and the step-level zone choice test printed in the session
(driver stays in its zone vs. relative closeness of the nearest other-zone stop).

Usage: .venv/bin/python make_figures.py <out_dir>
"""
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "AppleGothic", "axes.unicode_minus": False, "axes.spines.top": False, "axes.spines.right": False})

# 1) driver choice: stay in the current zone vs. how much closer the nearest other-zone stop is
labels = ["0–0.25", "0.25–0.5", "0.5–0.8", "0.8–1.25", "1.25–2", "2–4", "4–8", "8+"]
stay = [49.6, 80.5, 91.6, 97.1, 99.1, 99.7, 99.8, 99.8]
steps = [1571, 3368, 7579, 18200, 34808, 52318, 34160, 28098]
fig, ax = plt.subplots(figsize=(8.5, 4.4))
ax.bar(labels, stay, color="#3b6ea5")
for i, (s, n) in enumerate(zip(stay, steps)):
    ax.text(i, s + 1.2, f"{s:.1f}%", ha="center", fontsize=9)
    ax.text(i, 3, f"n={n:,}", ha="center", fontsize=7.5, color="white")
ax.text(-0.45, 107, "항상 가장 가까운 곳으로 가는 규칙이라면: b/a < 1 구간은 0%, b/a > 1 구간은 100%", fontsize=8.5, color="#c0392b")
ax.set_ylim(0, 112)
ax.set_xlabel("b/a = 가장 가까운 다른 구역 정차까지 시간 ÷ 가장 가까운 같은 구역 정차까지 시간 (작을수록 다른 구역이 더 가까움)", fontsize=8.5)
ax.set_ylabel("기사가 같은 구역에 머문 비율 (%)")
ax.set_title("기사는 다른 구역이 더 가까워도 지금 구역을 먼저 끝낸다")
fig.tight_layout()
fig.savefig(out / "fig-zone-choice.png", dpi=130)

# 2) similarity to drivers and matrix-time efficiency for the three routers (1,223 validation routes)
names = ["순수 TSP", "구역 우선 TSP", "구역 우선 +\n학습한 순서"]
score, se, ratio = [0.0940, 0.0616, 0.0418], [0.0016, 0.0010, 0.0011], [1.101, 1.047, 1.030]
fig, ax = plt.subplots(1, 2, figsize=(9.5, 4))
ax[0].bar(names, score, yerr=se, capsize=4, color=["#9aa5b1", "#6c8fb5", "#3b6ea5"])
for i, s in enumerate(score):
    ax[0].text(i, s + 0.006, f"{s:.4f}", ha="center", fontsize=9)
ax[0].set_title("기사 경로와의 차이 (낮을수록 기사와 비슷)", fontsize=10)
ax[0].set_ylim(0, 0.112)
ax[1].bar(names, [r - 1 for r in ratio], bottom=1, color=["#9aa5b1", "#6c8fb5", "#3b6ea5"])
for i, r in enumerate(ratio):
    ax[1].text(i, r + 0.004, f"{r:.3f}", ha="center", fontsize=9)
ax[1].axhline(1, color="gray", lw=0.8, ls=":")
ax[1].set_ylim(0.98, 1.13)
ax[1].set_title("기사 이동시간 ÷ 모델 이동시간 (행렬 기준)", fontsize=10)
fig.suptitle("검증 경로 1,223개: TSP는 가장 빠르지만 가장 기사와 다르다", fontsize=11)
fig.tight_layout()
fig.savefig(out / "fig-scores.png", dpi=130)

# 3) the example map drawn earlier in the session
shutil.copy(Path(__file__).parent / "results" / "example_zoom.png", out / "fig-example-map.png")
print("saved", sorted(p.name for p in out.iterdir()))
