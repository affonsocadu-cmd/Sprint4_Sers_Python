# simulacao.py
# Gera o cenário (sol, consumo, carros) e simula o balanço de energia
# a cada 15 minutos, com dois jeitos de controlar: sem otimização e inteligente.

import math
import random
import pandas as pd
from parametros import PASSO_H, PASSOS_POR_DIA
import metricas


def curva_sol(hora):
    # valor de 0 a 1 que imita o sol ao longo do dia (das 6h às 18h)
    x = (hora - 6) / 12
    if x <= 0 or x >= 1:
        return 0.0
    return math.sin(math.pi * x) ** 1.3


def gerar_cenario(p):
    random.seed(p["semente"])
    total = p["dias"] * PASSOS_POR_DIA

    # cada dia tem uma quantidade diferente de nuvens
    nuvem_dia = [random.uniform(0.35, 1.0) for _ in range(p["dias"])]

    fv, base, preco, horas = [], [], [], []
    ruido = 0
    for passo in range(total):
        dia = passo // PASSOS_POR_DIA
        hora = (passo % PASSOS_POR_DIA) * PASSO_H

        # nuvens passando durante o dia
        ruido = 0.7 * ruido + random.gauss(0, 0.07)
        nuvem = min(1.0, max(0.05, nuvem_dia[dia] * (1 + ruido)))
        fv.append(p["potencia_fv"] * p["desempenho_fv"] * curva_sol(hora) * nuvem)

        # consumo da própria estação (iluminação, câmeras, etc)
        consumo = 0.7 + random.gauss(0, 0.05)
        if 7 <= hora < 20:
            consumo += 0.8
        base.append(max(0.3, consumo))

        if p["ponta_inicio"] <= hora < p["ponta_fim"]:
            preco.append(p["tarifa_ponta"])
        else:
            preco.append(p["tarifa_normal"])
        horas.append(hora)

    # carros que chegam para recarregar
    sessoes = []
    for dia in range(p["dias"]):
        quantidade = random.randint(p["sessoes_min"], p["sessoes_max"])
        for _ in range(quantidade):
            chegada_h = random.uniform(7.5, 16.5)
            saida_h = min(chegada_h + random.uniform(3, 9), 22.0)
            energia = random.uniform(8, 30)
            # limite para sempre dar tempo de carregar
            energia = min(energia, 0.85 * p["carregador_kw"] * (saida_h - chegada_h))
            sessoes.append({
                "id": len(sessoes),
                "chegada": dia * PASSOS_POR_DIA + int(chegada_h / PASSO_H),
                "saida": dia * PASSOS_POR_DIA + int(saida_h / PASSO_H),
                "energia": energia,
            })

    return {"hora": horas, "fv": fv, "base": base, "preco": preco, "sessoes": sessoes}


# ---------- algoritmo inteligente ----------

def sol_insuficiente(passo, s, p):
    # previsão simples: estima a sobra de sol até o carro sair
    # (usa só 60% do céu limpo pra ser conservador e supõe consumo da estação de 1,5 kW)
    sobra_total = 0
    for k in range(passo, s["saida"]):
        hora = (k % PASSOS_POR_DIA) * PASSO_H
        previsto = p["potencia_fv"] * p["desempenho_fv"] * curva_sol(hora) * 0.6
        sobra_total += max(0, previsto - 1.5) * PASSO_H
    return sobra_total < s["restante"] * 1.2


def potencias_inteligente(passo, fv, base, preco, ativas, p):
    sobra = max(0, fv - base)
    em_ponta = preco > p["tarifa_normal"]
    resultado = {}

    # quem sai primeiro tem prioridade
    for s in sorted(ativas, key=lambda s: s["saida"]):
        horas_restantes = (s["saida"] - passo) * PASSO_H
        horas_necessarias = s["restante"] / p["carregador_kw"]
        folga = horas_restantes - horas_necessarias

        if folga <= 0.5:
            # quase sem tempo: carrega na potência máxima
            pot = p["carregador_kw"]
        else:
            # senão usa só a sobra do sol
            pot = min(p["carregador_kw"], sobra)
            # se o sol não vai bastar, antecipa com a rede, mas nunca na ponta
            if pot < p["carregador_kw"] and not em_ponta and sol_insuficiente(passo, s, p):
                pot = p["carregador_kw"]

        sobra = max(0, sobra - pot)
        resultado[s["id"]] = pot
    return resultado


def pode_descarregar_inteligente(hora, preco, soc, p):
    if preco > p["tarifa_normal"]:
        return True                      # na ponta pode usar a bateria à vontade
    if hora >= 21 or hora < 6:
        reserva = p["soc_min"]           # de madrugada pode esvaziar (o sol do dia seguinte recarrega)
    else:
        reserva = 0.45                   # de dia guarda uma reserva para a ponta
    return soc > reserva


# ---------- simulação ----------

def simular(cenario, politica, p):
    # politica: "sem_otimizacao" ou "inteligente"
    sessoes = [dict(s, restante=s["energia"]) for s in cenario["sessoes"]]
    soc = p["soc_inicial"]
    cap = p["bat_kwh"]
    efic = p["bat_efic"]
    linhas = []

    for passo in range(len(cenario["fv"])):
        fv = cenario["fv"][passo]
        base = cenario["base"][passo]
        preco = cenario["preco"][passo]
        hora = cenario["hora"][passo]

        ativas = [s for s in sessoes
                  if s["chegada"] <= passo < s["saida"] and s["restante"] > 0.000001]

        if politica == "inteligente":
            pedidos = potencias_inteligente(passo, fv, base, preco, ativas, p)
        else:
            pedidos = {s["id"]: p["carregador_kw"] for s in ativas}

        ev = 0.0
        for s in ativas:
            pot = min(pedidos[s["id"]], p["carregador_kw"], s["restante"] / PASSO_H)
            s["restante"] -= pot * PASSO_H
            ev += pot

        saldo = fv - (base + ev)
        carga = descarga = rede = exporta = 0.0

        if saldo >= 0:
            # sobrou energia: carrega a bateria e exporta o resto
            espaco = (1 - soc) * cap / PASSO_H / efic
            carga = min(saldo, p["bat_pot_max"], espaco)
            soc += carga * PASSO_H * efic / cap
            exporta = saldo - carga
        else:
            # faltou energia: usa a bateria (se pode) e o resto vem da rede
            falta = -saldo
            if politica == "inteligente":
                pode = pode_descarregar_inteligente(hora, preco, soc, p)
            else:
                pode = True
            if pode:
                disponivel = (soc - p["soc_min"]) * cap * efic / PASSO_H
                descarga = max(0, min(falta, p["bat_pot_max"], disponivel))
                soc -= descarga * PASSO_H / (efic * cap)
            rede = falta - descarga

        linhas.append({
            "dia": passo // PASSOS_POR_DIA, "hora": hora,
            "fv_kw": fv, "base_kw": base, "ev_kw": ev,
            "bat_carga_kw": carga, "bat_descarga_kw": descarga, "soc": soc,
            "rede_kw": rede, "exporta_kw": exporta, "preco": preco,
            "n_ativas": len(ativas),
            "solar_pct": 100 * fv / (p["potencia_fv"] * p["desempenho_fv"]),
        })

    df = pd.DataFrame(linhas)
    entregas = pd.DataFrame([{"energia": s["energia"], "entregue": s["energia"] - s["restante"]}
                             for s in sessoes])
    return df, entregas


def rodar(p):
    # roda as duas políticas no mesmo cenário e devolve tabelas e métricas
    cenario = gerar_cenario(p)
    df_b, ent_b = simular(cenario, "sem_otimizacao", p)
    df_i, ent_i = simular(cenario, "inteligente", p)
    return df_b, df_i, metricas.calcular(df_b, ent_b, p), metricas.calcular(df_i, ent_i, p)
