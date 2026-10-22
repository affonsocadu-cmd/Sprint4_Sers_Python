# main.py
# Roda a simulação completa, salva os resultados em results/ e os gráficos em docs/img/

import json
import pandas as pd
from parametros import PADRAO
from simulacao import rodar
import graficos


def economia(m_base, m_int):
    return m_base["custo_reais"] - m_int["custo_reais"]


p = dict(PADRAO)
df_b, df_i, m_base, m_int = rodar(p)

# salva os dados
df_b.to_csv("results/telemetria_sem_otimizacao.csv", index=False)
df_i.to_csv("results/telemetria_inteligente.csv", index=False)
json.dump({"sem_otimizacao": m_base, "inteligente": m_int}, open("results/metricas.json", "w"), indent=2)

# exemplo de pacote de telemetria (parecido com o JSON do Arduino da Sprint 3)
u = df_i.iloc[-1]
exemplo = {
    "estacao": "CHARGEGRID_01",
    "solar_pct": round(u["solar_pct"], 1),
    "fv_kw": round(u["fv_kw"], 2),
    "carros_kw": round(u["ev_kw"], 2),
    "bateria_pct": round(u["soc"] * 100, 1),
    "rede_kw": round(u["rede_kw"] - u["exporta_kw"], 2),
    "status": "CARREGANDO" if u["n_ativas"] > 0 else "PARADO",
}
json.dump(exemplo, open("results/telemetria_exemplo.json", "w"), indent=2)

# gráficos (usa o dia com mais sol)
melhor_dia = int(df_i.groupby("dia")["fv_kw"].sum().idxmax())
graficos.grafico_dia(df_b, df_i, melhor_dia, "docs/img/perfil_dia.png")
graficos.grafico_comparacao(m_base, m_int, "docs/img/comparacao.png")
graficos.diagrama_arquitetura("docs/img/arquitetura.png")

# teste com vários tamanhos de sistema solar (20 cenários aleatórios para cada)
linhas = []
for kwp in [10, 20, 30, 40]:
    economias = []
    custos = []
    for semente in range(20):
        _, _, mb, mi = rodar(dict(p, potencia_fv=kwp, semente=semente))
        economias.append(economia(mb, mi))
        custos.append(mb["custo_reais"])
    linhas.append({"kwp": kwp,
                   "custo_sem_otimizacao": sum(custos) / 20,
                   "economia_media": sum(economias) / 20,
                   "min": min(economias), "max": max(economias)})
sens = pd.DataFrame(linhas)
sens.to_csv("results/sensibilidade_fv.csv", index=False)
graficos.grafico_sensibilidade(sens, "docs/img/sensibilidade.png")

# robustez: mesmo sistema (30 kWp) com 20 sementes diferentes
economia_pct, reducao_ponta = [], []
for semente in range(20):
    _, _, mb, mi = rodar(dict(p, semente=semente))
    economia_pct.append(100 * economia(mb, mi) / mb["custo_reais"])
    reducao_ponta.append(100 * (mb["rede_ponta_kwh"] - mi["rede_ponta_kwh"]) / mb["rede_ponta_kwh"])
robustez = {
    "economia_media_pct": sum(economia_pct) / 20,
    "economia_min_pct": min(economia_pct),
    "economia_max_pct": max(economia_pct),
    "reducao_ponta_media_pct": sum(reducao_ponta) / 20,
}
json.dump(robustez, open("results/robustez.json", "w"), indent=2)

# resumo no terminal
print(pd.DataFrame({"sem_otimizacao": m_base, "inteligente": m_int}).round(2).to_string())
print("\nSensibilidade:\n", sens.round(1).to_string(index=False))
print("\nRobustez:", {k: round(v, 1) for k, v in robustez.items()})
