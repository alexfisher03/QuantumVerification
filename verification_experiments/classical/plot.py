# multi engine small multiples with scienceplots
# comments are lowercase no punctuation

from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import scienceplots  # required

RESULTS_DIR = Path("verification_experiments/classical/results")

ENG_ORDER = ["classical", "cai", "quantum"]
ENG_COLORS = {
    "classical": "#4c78a8",
    "cai": "#f28e2b",
    "quantum": "#59a14f",
}

def _load(p: Path):
    with open(p, "r") as f:
        return json.load(f)

def _gather():
    files = sorted(RESULTS_DIR.glob("*_metrics.json"))
    out = {}  # exp -> engine -> {r1,r2}
    engines_seen = set()
    for p in files:
        d = _load(p)
        exp = d.get("exp") or p.stem.split("_")[0]
        eng = d.get("engine", "classical")
        r1 = d["stage1"]["runtime_ms"]
        r2 = d["stage2"]["runtime_ms"]
        out.setdefault(exp, {})[eng] = {"r1": r1, "r2": r2}
        engines_seen.add(eng)
    return out, [e for e in ENG_ORDER if e in engines_seen]

def main():
    plt.style.use(["science", "no-latex"])
    plt.rcParams.update({
        "figure.dpi": 200,
        "savefig.dpi": 300,
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "axes.linewidth": 0.8,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.grid": True,
        "grid.linestyle": "--",
        "grid.alpha": 0.25,
    })

    data, engines = _gather()
    if not data:
        print("no metrics found")
        return

    exps = ["exp1", "exp2"]
    exps = [e for e in exps if e in data] or list(data.keys())

    n = len(exps)
    fig_w = max(6, 4.3 * n)
    fig, axes = plt.subplots(1, n, figsize=(fig_w, 4.0), constrained_layout=False)
    if n == 1:
        axes = [axes]
    fig.subplots_adjust(left=0.10, right=0.98, top=0.82, bottom=0.24, wspace=0.28)

    stages = ["stage 1", "stage 2"]
    x = np.arange(2)

    m = len(engines)
    width = min(0.22, 0.7 / max(m, 1))
    gap = 0.04
    offsets = [(i - (m - 1) / 2) * (width + gap) for i in range(m)]

    for i, ax in enumerate(axes):
        exp = exps[i]
        r1_vals = []
        r2_vals = []
        for eng in engines:
            v = data.get(exp, {}).get(eng)
            r1_vals.append(v["r1"] if v else 0.0)
            r2_vals.append(v["r2"] if v else 0.0)

        ymax = max([*r1_vals, *r2_vals, 1e-9])
        ax.set_ylim(0, ymax * 1.20)
        ax.set_title(exp)
        ax.set_xticks(x, stages)

        # show y ticks on all subplots
        if i == 0:
            ax.set_ylabel("runtime ms")
        ax.tick_params(axis="y", which="both", labelleft=True)

        for j, eng in enumerate(engines):
            xpos = x + offsets[j]
            vals = [r1_vals[j], r2_vals[j]]
            ax.bar(
                xpos,
                vals,
                width=width,
                color=ENG_COLORS.get(eng, "#666"),
                label=eng,
                alpha=0.95,
                edgecolor="#222",
                linewidth=0.6,
            )

    # legend bottom center
    handles = [plt.Rectangle((0, 0), 1, 1, color=ENG_COLORS.get(e, "#666"), ec="#222") for e in engines]
    fig.legend(handles, engines, loc="lower center", ncol=len(engines), frameon=False, bbox_to_anchor=(0.5, 0.06))

    fig.suptitle("runtime per experiment and stage for all three engines", y=0.96, fontsize=11)

    out_png = RESULTS_DIR / "baseline_grouped.png"

    fig.savefig(out_png)
    plt.close(fig)
    print(f"[OK] wrote {out_png}")

if __name__ == "__main__":
    main()