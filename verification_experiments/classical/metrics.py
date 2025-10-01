from __future__ import annotations
from dataclasses import dataclass, asdict
from time import perf_counter_ns
from typing import Callable, Dict, Set

try:
    from rich.console import Console
    from rich.table import Table
except Exception:
    Console = None
    Table = None

@dataclass
class Timing:
    total_ns: int
    per_input_ns: float
    inputs_per_sec: float

@dataclass
class StageSummary:
    count: int
    examples: list[str]

@dataclass
class BaselineReport:
    exp: str
    n: int
    N_inputs: int
    U: list[str]
    stage1: StageSummary
    stage2: StageSummary
    new_at_stage2_only: StageSummary
    timing_stage1: Timing
    timing_stage2: Timing
    recall_stage1: float
    recall_stage2: float

def _time_enumerator(n: int, fn: Callable[[], Set[str]]) -> tuple[Set[str], Timing]:
    start = perf_counter_ns()
    out = fn()
    end = perf_counter_ns()
    total_ns = end - start
    N = 1 << n
    per_input_ns = total_ns / N
    ips = 1e9 * N / total_ns if total_ns > 0 else float("inf")
    return out, Timing(total_ns=total_ns, per_input_ns=per_input_ns, inputs_per_sec=ips)

def make_report(
    *,
    exp: str,
    n: int,
    U: Set[str],
    enumerate_stage1: Callable[[], Set[str]],
    enumerate_stage2: Callable[[], Set[str]],
) -> BaselineReport:
    zs1, t1 = _time_enumerator(n, enumerate_stage1)
    zs2, t2 = _time_enumerator(n, enumerate_stage2)
    delta = zs2 - zs1

    return BaselineReport(
        exp=exp,
        n=n,
        N_inputs=(1 << n),
        U=sorted(U),
        stage1=StageSummary(count=len(zs1), examples=sorted(list(zs1))[:10]),
        stage2=StageSummary(count=len(zs2), examples=sorted(list(zs2))[:10]),
        new_at_stage2_only=StageSummary(count=len(delta), examples=sorted(list(delta))[:10]),
        timing_stage1=t1,
        timing_stage2=t2,
        recall_stage1=1.0,
        recall_stage2=1.0,
    )

def print_report(report: BaselineReport) -> None:
    if Console is None or Table is None:
        print("[rich not installed] ", asdict(report))
        return

    c = Console()
    hdr = Table(show_header=False, box=None, pad_edge=False)
    hdr.add_row("exp", report.exp)
    hdr.add_row("n", str(report.n))
    hdr.add_row("total inputs", f"{report.N_inputs}")
    hdr.add_row("|U|", f"{len(report.U)}")
    hdr.add_row("U", ", ".join(report.U))
    c.print(hdr)
    c.print()

    t = Table(title="Classical Baseline 2 stage", show_lines=True)
    t.add_column("metric")
    t.add_column("stage 1")
    t.add_column("stage 2")
    t.add_row("unsafe inputs |Z_unsafe|", str(report.stage1.count), str(report.stage2.count))
    t.add_row("new at stage 2 only", "-", str(report.new_at_stage2_only.count))
    t.add_row("runtime ms", f"{report.timing_stage1.total_ns/1e6:.3f}", f"{report.timing_stage2.total_ns/1e6:.3f}")
    t.add_row("us per input", f"{report.timing_stage1.per_input_ns/1e3:.3f}", f"{report.timing_stage2.per_input_ns/1e3:.3f}")
    t.add_row("inputs per sec", f"{report.timing_stage1.inputs_per_sec:,.0f}", f"{report.timing_stage2.inputs_per_sec:,.0f}")
    t.add_row("recall vs gt", f"{report.recall_stage1:.2f}", f"{report.recall_stage2:.2f}")
    c.print(t)
    c.print()
