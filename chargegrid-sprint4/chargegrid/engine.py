"""Motor de simulação de balanço de energia (PV + bateria + rede + VEs) em passos de 15 min."""
from dataclasses import replace
import pandas as pd
from .policies import Ctx


def simulate(inp, policy, cfg):
    dt, cap, eff = cfg.dt_h, cfg.bat_kwh, cfg.bat_eff
    sessions = [replace(s) for s in inp.sessions]        # cópia limpa por política
    soc, rows = cfg.bat_soc_init, []

    for t in range(len(inp.pv)):
        pv, base, price, hour = float(inp.pv[t]), float(inp.base[t]), float(inp.price[t]), float(inp.hour[t])
        active = [s for s in sessions if s.arr <= t < s.dep and s.remaining > 1e-6]
        ctx = Ctx(t, hour, dt, pv, base, price, active, soc, cfg)

        req = policy.ev_power(ctx) if active else {}
        ev = 0.0
        for s in active:
            p = min(req.get(s.sid, 0.0), s.pmax, s.remaining / dt)
            s.remaining -= p * dt
            ev += p

        net = pv - (base + ev)
        ch = dis = imp = exp = 0.0
        if net >= 0:
            ch = min(net, cfg.bat_pmax_kw, (1 - soc) * cap / dt / eff)
            soc += ch * dt * eff / cap
            exp = net - ch
        else:
            need = -net
            if policy.allow_discharge(ctx):
                avail = (soc - cfg.bat_soc_min) * cap * eff / dt
                dis = max(0.0, min(need, cfg.bat_pmax_kw, avail))
                soc -= dis * dt / (eff * cap)
            imp = need - dis

        rows.append(dict(step=t, hour=hour, day=t // cfg.steps_per_day, pv_kw=pv, base_kw=base, ev_kw=ev,
                         bat_charge_kw=ch, bat_discharge_kw=dis, soc=soc, grid_import_kw=imp,
                         grid_export_kw=exp, price=price, n_active=len(active),
                         solar_pct=100 * pv / (cfg.pv_kwp * cfg.pv_pr)))

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.Timestamp("2026-10-12") + pd.to_timedelta(df.step * dt, unit="h")
    sess = pd.DataFrame([dict(sid=s.sid, energy=s.energy, delivered=s.energy - s.remaining) for s in sessions])
    return df, sess
