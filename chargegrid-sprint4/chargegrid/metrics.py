"""KPIs de eficiência, custo e sustentabilidade."""


def compute(df, sess, cfg) -> dict:
    dt = cfg.dt_h
    pv = df.pv_kw.sum() * dt
    load = (df.base_kw + df.ev_kw).sum() * dt
    imp = df.grid_import_kw.sum() * dt
    exp = df.grid_export_kw.sum() * dt
    peak_imp = df.loc[df.price > cfg.tariff_offpeak, "grid_import_kw"].sum() * dt
    cost = ((df.grid_import_kw * df.price - df.grid_export_kw * cfg.export_credit).sum()) * dt
    ev = df.ev_kw.sum() * dt
    co2_grid = imp * cfg.grid_ef
    co2_ice = ev * cfg.ev_km_per_kwh * cfg.ice_ef_km
    return {
        "pv_kwh": pv, "load_kwh": load, "ev_kwh": ev,
        "grid_import_kwh": imp, "grid_export_kwh": exp, "peak_import_kwh": peak_imp,
        "cost_brl": cost,
        "self_consumption_pct": 100 * (1 - exp / pv) if pv else 0.0,
        "self_sufficiency_pct": 100 * (1 - imp / load) if load else 0.0,
        "service_level_pct": 100 * sess.delivered.sum() / sess.energy.sum(),
        "peak_grid_kw": float(df.grid_import_kw.max()),
        "co2_station_kg": co2_grid,
        "co2_ice_equiv_kg": co2_ice,
        "co2_avoided_vs_ice_kg": co2_ice - co2_grid,
        "km_charged": ev * cfg.ev_km_per_kwh,
    }
