# small multiples one subplot per experiment linear y
# comments are lowercase no punctuation

from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

RESULTS_DIR = Path("verification_experiments/classical/results")

def _load_json(p: Path):
    with open(p, "r") as f:
        return json.load(f)

def main():
    candidates = [RESULTS_DIR / "exp1_baseline_metrics.json",
                  RESULTS_DIR / "exp2_baseline_metrics.json"]
    present = [p for p in candidates if p.exists()]
    if not present:
        present = sorted(RESULTS_DIR.glob("*_baseline_metrics.json"))
    if not present:
        print("no metrics found")
        return

    data = [_load_json(p) for p in present]
    exps = [d.get("exp", p.stem.split("_")[0]) for d, p in zip(data, present)]

    r1 = [d["stage1"]["runtime_ms"] for d in data]
    r2 = [d["stage2"]["runtime_ms"] for d in data]

    n = len(exps)
    fig_w = max(6, 5 * n)
    fig, axes = plt.subplots(1, n, figsize=(fig_w, 5), dpi=150, squeeze=False)
    axes = axes[0]

    # stage colors consistent across experiments
    stage_colors = ["#007bff", "#ff5e00"]

    for i, ax in enumerate(axes):
        x = np.array([0, 1])
        vals = [r1[i], r2[i]]
        ax.bar(x, vals, width=0.48, color=stage_colors, alpha=0.95)

        ax.set_title(exps[i], fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(["stage 1", "stage 2"], fontsize=9)
        ax.grid(axis="y", linestyle="--", alpha=0.3)

        ymax = max(vals) if max(vals) > 0 else 1.0
        ax.set_ylim(0, ymax * 1.18)

        if i == 0:
            ax.set_ylabel("runtime ms", fontsize=9)
        else:
            ax.set_yticklabels([])

    legend_patches = [Patch(facecolor=stage_colors[0], label="stage 1 runtime"),
                    Patch(facecolor=stage_colors[1], label="stage 2 runtime")]
    fig.legend(handles=legend_patches, loc="lower center", ncol=2, frameon=False, fontsize=9,
            bbox_to_anchor=(0.5, -0.02))

    fig.suptitle("Classical Baseline Runtime Per Experiment", fontsize=10, y=0.98)
    fig.tight_layout(rect=[0, 0.08, 1, 0.94])


    outfile = RESULTS_DIR / "baseline_grouped.png"
    fig.savefig(outfile)
    plt.close(fig)
    print(f"[OK] wrote {outfile}")

if __name__ == "__main__":
    main()
