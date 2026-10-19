"""Parâmetros do sistema. Todos são HIPÓTESES ajustáveis (ver README, seção Premissas)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    station_id: str = "CHARGEGRID_GW_01"
    days: int = 7
    dt_h: float = 0.25            # passo de 15 min
    seed: int = 42

    # Geração fotovoltaica (inversor híbrido Goodwe série ET/EH + painéis)
    pv_kwp: float = 30.0
    pv_pr: float = 0.80           # performance ratio (perdas globais)

    # Armazenamento (2 módulos de ~10 kWh (ordem de grandeza de baterias Goodwe Lynx))
    bat_kwh: float = 20.4          # 2 módulos de ~10 kWh (ordem de grandeza de baterias Goodwe Lynx)
    bat_pmax_kw: float = 10.0
    bat_eff: float = 0.95         # eficiência de um sentido (ida e volta ≈ 0,90)
    bat_soc_min: float = 0.10
    bat_soc_init: float = 0.30

    # Recarga
    charger_pmax_kw: float = 7.4  # carregador AC monofásico 32 A / 230 V
    sessions_per_day: tuple = (4, 7)

    # Tarifa (R$/kWh) – valores ilustrativos de tarifa horária
    tariff_offpeak: float = 0.75
    tariff_peak: float = 1.60
    peak_hours: tuple = (18, 21)
    export_credit: float = 0.45

    # Emissões
    grid_ef: float = 0.04         # kgCO2/kWh – ordem de grandeza da média do SIN (conferir fator oficial MCTI)
    ice_ef_km: float = 0.19       # kgCO2/km – carro a combustão flex médio
    ev_km_per_kwh: float = 6.0    # eficiência do VE

    @property
    def steps_per_day(self) -> int:
        return int(round(24 / self.dt_h))
