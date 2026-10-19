"""Assistente virtual (offline, por intenções) que responde perguntas sobre a operação da estação.
Pode ser exposto a Alexa/Google Assistant via webhook, ou trocado por um LLM, reutilizando `ask()`."""
import re
import unicodedata


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[\u0300-\u036f]", "", t)


class Assistant:
    def __init__(self, df, m_smart, m_base, cfg):
        self.df, self.ms, self.mb, self.cfg = df, m_smart, m_base, cfg

    def ask(self, question: str) -> str:
        q, d, dt = _norm(question), self.df, self.cfg.dt_h
        today = d[d.day == d.day.max()]
        last = d.iloc[-1]
        if re.search(r"gerei|geracao|gerou|solar|painel", q):
            return (f"Hoje os painéis geraram {today.pv_kw.sum() * dt:.1f} kWh; "
                    f"na semana foram {self.ms['pv_kwh']:.0f} kWh.")
        if re.search(r"bateria|soc|carga da bateria", q):
            return f"A bateria está em {last.soc * 100:.0f}% (mínimo configurado: {self.cfg.bat_soc_min * 100:.0f}%)."
        if re.search(r"economi|custo|gast|dinheiro|reais", q):
            s = self.mb["cost_brl"] - self.ms["cost_brl"]
            return (f"Com o algoritmo inteligente o custo semanal foi R$ {self.ms['cost_brl']:.2f} contra "
                    f"R$ {self.mb['cost_brl']:.2f} sem otimização: economia de R$ {s:.2f} "
                    f"({100 * s / self.mb['cost_brl']:.0f}%).")
        if re.search(r"co2|carbono|emiss|ambient|sustent", q):
            return (f"Na semana, as recargas equivalem a {self.ms['km_charged']:.0f} km rodados. "
                    f"Evitamos cerca de {self.ms['co2_avoided_vs_ice_kg']:.0f} kg de CO₂ em comparação a carros "
                    f"a combustão (hipóteses no README).")
        if re.search(r"ponta|pico|horario de ponta", q):
            return (f"Importação na ponta: {self.ms['peak_import_kwh']:.1f} kWh com o Smart contra "
                    f"{self.mb['peak_import_kwh']:.1f} kWh sem otimização.")
        if re.search(r"carro|veiculo|recarga|carregando|status|estacao", q):
            return (f"Agora há {int(last.n_active)} veículo(s) em recarga, consumindo {last.ev_kw:.1f} kW. "
                    f"Rede: {last.grid_import_kw:.1f} kW importados; FV: {last.pv_kw:.1f} kW.")
        return ("Posso responder sobre geração solar, bateria, economia, CO₂, horário de ponta e status das recargas. "
                "Tente: 'quanto gerei hoje?' ou 'qual a economia?'.")
