import argparse
import json
from pathlib import Path
from verification_experiments.common.config import (
    get_signal_order, get_unsafe_set, EXP_CONFIGS
)
from verification_experiments.classical.pipeline import (
    summarize_illegal_inputs,
    inputs_causing_illegal_at_stage1,
    inputs_causing_illegal_at_stage2,
)
from verification_experiments.classical.metrics import make_report, print_report

OUT_DIR = Path("verification_experiments/classical/results")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--exp", choices=list(EXP_CONFIGS.keys()), default="exp1")
    p.add_argument("--stage", choices=["1","2","all"], default="all")
    args = p.parse_args()

    exp = args.exp
    n1 = len(get_signal_order(exp, "1"))

    # we always compute the full report so plotting is consistent
    report = make_report(
        exp=exp,
        n=n1,
        U=get_unsafe_set(exp, "1"),
        enumerate_stage1=lambda: inputs_causing_illegal_at_stage1(exp),
        enumerate_stage2=lambda: inputs_causing_illegal_at_stage2(exp),
    )

    # print based on requested stage
    if args.stage in ("1","all"):
        print_report(report)
    elif args.stage == "2":
        # light console output for stage 2
        print(f"exp {exp} n {n1} stage2 count {report.stage2.count} runtime_ms {report.timing_stage2.total_ns/1e6:.3f}")

    # always write consistent artifacts
    metrics_path = OUT_DIR / f"{exp}_baseline_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(
            {
                "exp": report.exp,
                "n": report.n,
                "N_inputs": report.N_inputs,
                "U": report.U,
                "stage1": {
                    "count": report.stage1.count,
                    "examples": report.stage1.examples,
                    "runtime_ms": round(report.timing_stage1.total_ns / 1e6, 3),
                    "us_per_input": round(report.timing_stage1.per_input_ns / 1e3, 3),
                    "inputs_per_sec": int(report.timing_stage1.inputs_per_sec),
                },
                "stage2": {
                    "count": report.stage2.count,
                    "examples": report.stage2.examples,
                    "runtime_ms": round(report.timing_stage2.total_ns / 1e6, 3),
                    "us_per_input": round(report.timing_stage2.per_input_ns / 1e3, 3),
                    "inputs_per_sec": int(report.timing_stage2.inputs_per_sec),
                },
                "new_at_stage2_only": {
                    "count": report.new_at_stage2_only.count,
                    "examples": report.new_at_stage2_only.examples,
                },
                "recall": {
                    "stage1": report.recall_stage1,
                    "stage2": report.recall_stage2,
                },
            },
            f,
            indent=2,
        )

    summary_path = OUT_DIR / f"{exp}_baseline_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summarize_illegal_inputs(exp), f, indent=2)

    # optional stage2 only input dump
    if args.stage == "2":
        zs2 = inputs_causing_illegal_at_stage2(exp)
        with open(OUT_DIR / f"{exp}_stage2_inputs.json", "w") as f:
            json.dump({"exp": exp, "n": n1, "count": len(zs2), "examples": sorted(list(zs2))[:16]}, f, indent=2)

if __name__ == "__main__":
    main()
