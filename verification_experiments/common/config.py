from dataclasses import dataclass
from typing import Literal, List, Dict, Set

ExpName = Literal["exp1", "exp2"]
StageName = Literal["1", "2", "all"]

@dataclass(frozen=True)
class StageCfg:
    name: str
    signal_order: List[str]
    unsafe_omegas: Set[str]  # exact signatures in omega space

@dataclass(frozen=True)
class ExpCfg:
    name: ExpName
    stages: Dict[str, StageCfg]

def _bits_from_names(order: List[str], ones: Set[str]) -> str:
    return "".join("1" if s in ones else "0" for s in order)

# exp1 n=7 both stages share order
_order7 = ["rst", "en", "busA_drive", "busB_drive", "weA", "weB", "addr_eq"]
exp1_u = {
    "1100000",
    "0011000",
    "0000111",
}
exp1_stage1 = StageCfg(name="1", signal_order=_order7, unsafe_omegas=exp1_u)
exp1_stage2 = StageCfg(name="2", signal_order=_order7, unsafe_omegas=exp1_u)

# exp2 stage1 n=14
_order14 = [
    "rst","en","busA_drive","busB_drive","weA","weB","addr_eq",
    "req","ack","mode0","mode1","parity_err","timeout","busy",
]
# choose 5 concrete omega signatures that mark hazards
_exp2_u1 = {
    _bits_from_names(_order14, {"rst","en"}),                                 # reset while enabled
    _bits_from_names(_order14, {"busA_drive","busB_drive"}),                  # bus contention
    _bits_from_names(_order14, {"weA","weB","addr_eq"}),                      # double write same addr
    _bits_from_names(_order14, {"ack"}),                                      # handshake contradiction ack without req
    _bits_from_names(_order14, {"mode0","mode1"}),                            # illegal mode 11
}
exp2_stage1 = StageCfg(name="1", signal_order=_order14, unsafe_omegas=_exp2_u1)

# exp2 stage2 n=16
_order16 = _order14 + ["hazard","stall"] # adds two additional signals
_exp2_u2 = {
    _bits_from_names(_order16, {"rst","en"}),                                 # reset while enabled persists
    _bits_from_names(_order16, {"busA_drive","busB_drive"}),                  # contention signature
    _bits_from_names(_order16, {"weA","weB","addr_eq"}),                      # double write
    _bits_from_names(_order16, {"parity_err"}),                               # parity error flagged
    _bits_from_names(_order16, {"timeout"}),                                  # timeout flagged
}
exp2_stage2 = StageCfg(name="2", signal_order=_order16, unsafe_omegas=_exp2_u2)

EXP_CONFIGS: Dict[ExpName, ExpCfg] = {
    "exp1": ExpCfg(name="exp1", stages={"1": exp1_stage1, "2": exp1_stage2}),
    "exp2": ExpCfg(name="exp2", stages={"1": exp2_stage1, "2": exp2_stage2}),
}

def get_cfg(exp: ExpName, stage: StageName) -> StageCfg:
    if stage == "all":
        raise ValueError("stage all has no single config")
    return EXP_CONFIGS[exp].stages[stage]

def get_signal_order(exp: ExpName, stage: StageName) -> List[str]:
    return get_cfg(exp, stage).signal_order

def get_unsafe_set(exp: ExpName, stage: StageName) -> Set[str]:
    return get_cfg(exp, stage).unsafe_omegas
