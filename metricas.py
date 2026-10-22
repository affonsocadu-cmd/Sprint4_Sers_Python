# metricas.py
# Calcula custo, autossuficiência, CO2, etc. a partir da tabela da simulação.

from parametros import PASSO_H


def calcular(df, entregas, p):
    fv = df["fv_kw"].sum() * PASSO_H
    consumo = (df["base_kw"] + df["ev_kw"]).sum() * PASSO_H
    rede = df["rede_kw"].sum() * PASSO_H
    exportado = df["exporta_kw"].sum() * PASSO_H
    ev = df["ev_kw"].sum() * PASSO_H

    na_ponta = df[df["preco"] > p["tarifa_normal"]]
    rede_ponta = na_ponta["rede_kw"].sum() * PASSO_H

    custo = (df["rede_kw"] * df["preco"]).sum() * PASSO_H \
        - exportado * p["credito_exportacao"]

    km = ev * p["km_por_kwh"]
    co2_estacao = rede * p["fator_rede"]
    co2_combustao = km * p["fator_combustao"]

    return {
        "fv_kwh": fv,
        "consumo_kwh": consumo,
        "ev_kwh": ev,
        "rede_kwh": rede,
        "exportado_kwh": exportado,
        "rede_ponta_kwh": rede_ponta,
        "custo_reais": custo,
        "autoconsumo_pct": 100 * (1 - exportado / fv),
        "autossuficiencia_pct": 100 * (1 - rede / consumo),
        "atendimento_pct": 100 * entregas["entregue"].sum() / entregas["energia"].sum(),
        "pico_rede_kw": float(df["rede_kw"].max()),
        "km_recarregados": km,
        "co2_estacao_kg": co2_estacao,
        "co2_combustao_kg": co2_combustao,
        "co2_evitado_kg": co2_combustao - co2_estacao,
    }
