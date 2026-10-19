"""Geração dos cenários de entrada: irradiância/PV, carga da estação e sessões de recarga."""
from dataclasses import dataclass, field
import numpy as np
from .config import Config


@dataclass
class Session:
    sid: int
    arr: int          # passo de chegada
    dep: int          # passo de saída
    energy: float     # kWh necessários até a saída
    pmax: float       # kW máximos do carregador
    remaining: float = field(init=False)

    def __post_init__(self):
        self.remaining = self.energy


@dataclass
class Inputs:
    hour: np.ndarray
    pv: np.ndarray
    base: np.ndarray
    price: np.ndarray
    sessions: list


def clear_sky(hour):
    """Curva de céu limpo normalizada (0–1), nascer ~6h, pôr ~18h."""
    x = (np.asarray(hour, dtype=float) - 6.0) / 12.0
    return np.where((x > 0) & (x < 1), np.sin(np.pi * np.clip(x, 0, 1)) ** 1.3, 0.0)


def build_inputs(cfg: Config) -> Inputs:
    rng = np.random.default_rng(cfg.seed)
    spd, n = cfg.steps_per_day, cfg.days * cfg.steps_per_day
    t = np.arange(n)
    hour = (t % spd) * cfg.dt_h
    day = t // spd

    cloud_day = rng.uniform(0.35, 1.0, cfg.days)                       # nebulosidade diária
    noise = np.convolve(rng.normal(0, 0.15, n), np.ones(5) / 5, mode="same")
    cloud = np.clip(cloud_day[day] * (1 + noise), 0.05, 1.0)
    pv = cfg.pv_kwp * cfg.pv_pr * clear_sky(hour) * cloud

    base = 0.7 + 0.8 * ((hour >= 7) & (hour < 20)) + rng.normal(0, 0.05, n)  # iluminação, câmeras, TI
    base = np.clip(base, 0.3, None)

    p0, p1 = cfg.peak_hours
    price = np.where((hour >= p0) & (hour < p1), cfg.tariff_peak, cfg.tariff_offpeak)

    sessions, sid = [], 0
    for d in range(cfg.days):
        for _ in range(rng.integers(cfg.sessions_per_day[0], cfg.sessions_per_day[1] + 1)):
            arr_h = rng.uniform(7.5, 16.5)
            dep_h = min(arr_h + rng.uniform(3, 9), 22.0)
            stay = dep_h - arr_h
            energy = min(rng.uniform(8, 30), 0.85 * cfg.charger_pmax_kw * stay)  # sempre viável
            sessions.append(Session(sid, d * spd + int(arr_h / cfg.dt_h),
                                    d * spd + int(dep_h / cfg.dt_h), float(energy), cfg.charger_pmax_kw))
            sid += 1
    return Inputs(hour, pv, base, price, sessions)
