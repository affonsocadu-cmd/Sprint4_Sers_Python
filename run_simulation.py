"""Executa Baseline vs Smart, salva CSV/JSON/gráficos e a análise de sensibilidade/robustez."""
import json
from dataclasses import replace
import pandas as pd
from chargegrid.config import Config
from chargegrid.data import build_inputs
from chargegrid.engine import simulate
from chargegrid.policies import Baseline, Smart
from chargegrid.metrics import compute
from chargegrid import viz


def run(cfg):
    inp = build_inputs(cfg)
    (db, sb), (ds, ss) = simulate(inp, Baseline(), cfg), simulate(inp, Smart(), cfg)
    return db, ds, compute(db, sb, cfg), compute(ds, ss, cfg)


def saving(mb, ms):
    return 100 * (mb["cost_brl"] - ms["cost_brl"]) / mb["cost_brl"]


if __name__ == "__main__":
    cfg = Config()
    db, ds, mb, ms = run(cfg)
    db.to_csv("results/telemetry_baseline.csv", index=False)
    ds.to_csv("results/telemetry_smart.csv", index=False)
    json.dump({"baseline": mb, "smart": ms}, open("results/metrics.json", "w"), indent=2)

    last = ds.iloc[-1]   # pacote de telemetria no formato da Sprint 3, estendido
    json.dump({"station_id": cfg.station_id, "timestamp": str(last.timestamp), "solar_pct": round(last.solar_pct, 1),
               "pv_kw": round(last.pv_kw, 2), "ev_kw": round(last.ev_kw, 2), "battery_soc_pct": round(last.soc * 100, 1),
               "grid_kw": round(last.grid_import_kw - last.grid_export_kw, 2), "status": "CHARGING" if last.n_active else "STANDBY"},
              open("results/telemetry_sample.json", "w"), indent=2)

    best_day = int(ds.groupby("day").pv_kw.sum().idxmax())
    viz.plot_day(db, ds, best_day, "docs/img/perfil_dia.png")
    viz.plot_comparison(mb, ms, "docs/img/comparacao_kpis.png")
    viz.plot_architecture("docs/img/arquitetura.png")

    # Sensibilidade ao tamanho do sistema FV (cenário base com 20 sementes)
    rows = []
    for kwp in (10, 20, 30, 40):
        s, base_c = [], []
        for seed in range(20):
            _, _, b, m = run(replace(cfg, pv_kwp=kwp, seed=seed))
            s.append(b["cost_brl"] - m["cost_brl"]); base_c.append(b["cost_brl"])
        rows.append({"pv_kwp": kwp, "saving_brl_week": sum(s) / len(s), "min": min(s), "max": max(s),
                     "baseline_cost_brl_week": sum(base_c) / len(base_c)})
    sens = pd.DataFrame(rows); sens.to_csv("results/sensitivity_pv.csv", index=False)
    viz.plot_sensitivity(sens, "docs/img/sensibilidade_pv.png")

    # Robustez: 20 sementes no cenário base
    rob = [saving(*run(replace(cfg, seed=s))[2:]) for s in range(20)]
    pk = [(lambda r: 100 * (r[2]["peak_import_kwh"] - r[3]["peak_import_kwh"]) / r[2]["peak_import_kwh"])(run(replace(cfg, seed=s))) for s in range(20)]
    summary = {"cost_saving_mean_pct": float(pd.Series(rob).mean()), "cost_saving_min_pct": min(rob),
               "cost_saving_max_pct": max(rob), "peak_reduction_mean_pct": float(pd.Series(pk).mean())}
    json.dump(summary, open("results/robustness.json", "w"), indent=2)

    print(pd.DataFrame({"baseline": mb, "smart": ms}).round(2).to_string())
    print("\nSensibilidade FV:\n", sens.round(1).to_string(index=False))
    print("\nRobustez (20 sementes):", {k: round(v, 1) for k, v in summary.items()})
