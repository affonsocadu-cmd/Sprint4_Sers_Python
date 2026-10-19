import pytest
from dataclasses import replace
from chargegrid.config import Config
from chargegrid.data import build_inputs
from chargegrid.engine import simulate
from chargegrid.policies import Baseline, Smart
from chargegrid.metrics import compute


@pytest.mark.parametrize("policy", [Baseline(), Smart()])
def test_balanco_de_energia_e_limites(policy):
    cfg = Config(); df, sess = simulate(build_inputs(cfg), policy, cfg)
    lhs = df.pv_kw + df.grid_import_kw + df.bat_discharge_kw
    rhs = df.base_kw + df.ev_kw + df.grid_export_kw + df.bat_charge_kw
    assert (lhs - rhs).abs().max() < 1e-9                       # conservação de energia
    assert df.soc.min() >= cfg.bat_soc_min - 1e-9 and df.soc.max() <= 1 + 1e-9
    assert compute(df, sess, cfg)["service_level_pct"] > 99.9   # todos os VEs são atendidos


def test_smart_nao_custa_mais_que_baseline_em_varias_sementes():
    for seed in range(10):
        cfg = replace(Config(), seed=seed); inp = build_inputs(cfg)
        cb = compute(*simulate(inp, Baseline(), cfg), cfg)["cost_brl"]
        cs = compute(*simulate(inp, Smart(), cfg), cfg)["cost_brl"]
        assert cs <= cb * 1.01, f"seed {seed}: smart {cs:.1f} > baseline {cb:.1f}"
