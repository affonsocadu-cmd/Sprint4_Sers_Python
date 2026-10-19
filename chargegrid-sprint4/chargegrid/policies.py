"""Políticas de controle. Baseline = sem otimização; Smart = algoritmo do ChargeGrid."""
from dataclasses import dataclass
import numpy as np
from .data import clear_sky


@dataclass
class Ctx:
    t: int
    hour: float
    dt: float
    pv: float
    base: float
    price: float
    active: list
    soc: float
    cfg: object


class Baseline:
    """Recarrega assim que o carro conecta, em potência máxima; bateria em autoconsumo simples."""
    name = "baseline"

    def ev_power(self, c: Ctx):
        return {s.sid: s.pmax for s in c.active}

    def allow_discharge(self, c: Ctx):
        return True


class Smart:
    """
    Regras:
      1. URGÊNCIA: se a folga (tempo até a saída − tempo mínimo para completar) <= margem, carrega a pmax.
      2. SOL PRIMEIRO: fora da urgência, carrega apenas com o excedente solar (PV − carga base).
      3. SOL INSUFICIENTE: se a previsão de excedente até a saída não cobre a energia faltante,
         antecipa a carga com a rede, mas só FORA do horário de ponta.
      4. BATERIA: reserva dinâmica. Na ponta descarrega livremente; fora dela só usa a energia acima
         de uma reserva (para garantir a ponta) e, de madrugada (21h–6h), pode esvaziar até o mínimo,
         abrindo espaço para armazenar o excedente solar do dia seguinte.
    """
    name = "smart"

    def __init__(self, margin_h: float = 0.5, forecast_factor: float = 0.6, base_avg_kw: float = 1.5,
                 reserve_soc: float = 0.45):
        self.margin_h, self.ff, self.base_avg, self.reserve_soc = margin_h, forecast_factor, base_avg_kw, reserve_soc

    def _short_on_sun(self, c: Ctx, s) -> bool:
        steps = np.arange(c.t, s.dep)
        hours = (steps % c.cfg.steps_per_day) * c.dt
        fc = c.cfg.pv_kwp * c.cfg.pv_pr * clear_sky(hours) * self.ff
        expected = np.clip(fc - self.base_avg, 0, None).sum() * c.dt
        return expected < s.remaining * 1.2

    def ev_power(self, c: Ctx):
        out, surplus = {}, max(0.0, c.pv - c.base)
        is_peak = c.price > c.cfg.tariff_offpeak
        for s in sorted(c.active, key=lambda s: s.dep):          # prioriza quem sai antes
            slack = (s.dep - c.t) * c.dt - s.remaining / s.pmax
            if slack <= self.margin_h:
                p = s.pmax
            else:
                p = min(s.pmax, surplus)
                if p < s.pmax and not is_peak and self._short_on_sun(c, s):
                    p = s.pmax
            surplus = max(0.0, surplus - p)
            out[s.sid] = p
        return out

    def allow_discharge(self, c: Ctx):
        if c.price > c.cfg.tariff_offpeak:
            return True
        night = c.hour >= 21 or c.hour < 6
        reserve = c.cfg.bat_soc_min if night else self.reserve_soc
        return c.soc > reserve
