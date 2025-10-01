from typing import Dict, Set
from verification_experiments.common.config import (
    get_signal_order, get_unsafe_set, ExpName, StageName
)

def _bits_to_dict(bits: str, order: list[str]) -> Dict[str, int]:
    assert len(bits) == len(order)
    return {name: int(bits[i]) for i, name in enumerate(order)}

def _dict_to_bits(s: Dict[str, int], order: list[str]) -> str:
    return "".join("1" if s[name] else "0" for name in order)

# stage 1 transform
def f1(exp: ExpName, z_bits: str) -> str:
    order = get_signal_order(exp, "1")
    s = _bits_to_dict(z_bits, order)

    out: Dict[str, int] = {k: 0 for k in order}
    out["rst"] = s.get("rst", 0)
    out["en"]  = s.get("en", 0)

    if out["rst"] == 1:
        for k in out.keys():
            if k not in ("rst","en"):
                out[k] = 0
    else:
        # gate core activity by en if present
        for k in ("busA_drive","busB_drive","weA","weB"):
            if k in out:
                out[k] = 1 if (out["en"] == 1 and s.get(k,0) == 1) else 0
        # pass through others
        for k in out.keys():
            if k not in ("rst","en","busA_drive","busB_drive","weA","weB"):
                out[k] = s.get(k, 0)

    return _dict_to_bits(out, order)

# stage 2 transform
def f2(exp: ExpName, omega1_bits: str) -> str:
    order = get_signal_order(exp, "2")
    s = _bits_to_dict(omega1_bits, order if len(omega1_bits)==len(order) else get_signal_order(exp,"1"))

    # start from stage1 order then project to stage2 order
    tmp: Dict[str, int] = {k: s.get(k, 0) for k in set(order) | set(s.keys())}

    # bug inspired behavior
    contention = 1 if (tmp.get("busA_drive",0) == 1 and tmp.get("busB_drive",0) == 1) else 0
    both_we    = 1 if (tmp.get("weA",0) == 1 and tmp.get("weB",0) == 1) else 0

    if contention == 1 or both_we == 1:
        tmp["en"] = 0
    if both_we == 1:
        tmp["addr_eq"] = 1
    if tmp.get("rst",0) == 1:
        for k in ("busA_drive","busB_drive","weA","weB","addr_eq"):
            if k in tmp:
                tmp[k] = 0

    # pass through and extend with zeros for new stage2 wires
    out = {k: tmp.get(k, 0) for k in order}
    return _dict_to_bits(out, order)

# enumerators
def inputs_causing_illegal_at_stage1(exp: ExpName) -> Set[str]:
    order = get_signal_order(exp, "1")
    U = get_unsafe_set(exp, "1")
    n = len(order)
    bad: Set[str] = set()
    for x in range(1 << n):
        z = format(x, f"0{n}b")
        if f1(exp, z) in U:
            bad.add(z)
    return bad

def inputs_causing_illegal_at_stage2(exp: ExpName) -> Set[str]:
    order1 = get_signal_order(exp, "1")
    order2 = get_signal_order(exp, "2")
    U = get_unsafe_set(exp, "2")
    n = len(order1)
    bad: Set[str] = set()
    for x in range(1 << n):
        z = format(x, f"0{n}b")
        o1 = f1(exp, z)
        o2 = f2(exp, o1)
        if o2 in U:
            bad.add(z)
    return bad

def summarize_illegal_inputs(exp: ExpName) -> Dict[str, object]:
    order1 = get_signal_order(exp, "1")
    zs1 = inputs_causing_illegal_at_stage1(exp)
    zs2 = inputs_causing_illegal_at_stage2(exp)
    return {
        "exp": exp,
        "n_stage1": len(order1),
        "U_stage1": sorted(list(get_unsafe_set(exp,"1"))),
        "U_stage2": sorted(list(get_unsafe_set(exp,"2"))),
        "first 10 stage1": {"count": len(zs1), "examples": sorted(list(zs1))[:10]},
        "first 10 stage2": {"count": len(zs2), "examples": sorted(list(zs2))[:10]},
        "first 10 new_at_stage2_only": {
            "count": len(zs2 - zs1),
            "examples": sorted(list(zs2 - zs1))[:10],
        },
    }
