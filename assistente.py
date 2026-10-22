# assistente.py
# Assistente virtual simples: procura palavras-chave na pergunta e responde
# com os dados da simulação. Dá pra ligar isso num bot de voz depois.

from parametros import PASSO_H


def responder(pergunta, df, m_int, m_base, p):
    q = pergunta.lower()
    ultimo_dia = df["dia"].max()
    hoje = df[df["dia"] == ultimo_dia]
    agora = df.iloc[-1]

    if "gerei" in q or "gerou" in q or "geração" in q or "geracao" in q or "solar" in q:
        return (f"Hoje os painéis geraram {hoje['fv_kw'].sum() * PASSO_H:.1f} kWh. "
                f"Na semana inteira foram {m_int['fv_kwh']:.0f} kWh.")

    if "bateria" in q or "soc" in q:
        return f"A bateria está com {agora['soc'] * 100:.0f}% de carga."

    if "economi" in q or "custo" in q or "gast" in q or "reais" in q:
        economia = m_base["custo_reais"] - m_int["custo_reais"]
        pct = 100 * economia / m_base["custo_reais"]
        return (f"Com o algoritmo inteligente o custo da semana foi R$ {m_int['custo_reais']:.2f}, "
                f"contra R$ {m_base['custo_reais']:.2f} sem otimização. "
                f"Economia de R$ {economia:.2f} ({pct:.0f}%).")

    if "co2" in q or "carbono" in q or "emiss" in q or "sustent" in q:
        return (f"As recargas da semana equivalem a {m_int['km_recarregados']:.0f} km rodados. "
                f"Isso evita cerca de {m_int['co2_evitado_kg']:.0f} kg de CO2 comparado a carros "
                f"a combustão (considerando as premissas do README).")

    if "ponta" in q or "pico" in q:
        return (f"Na ponta a estação importou {m_int['rede_ponta_kwh']:.1f} kWh com o algoritmo "
                f"inteligente e {m_base['rede_ponta_kwh']:.1f} kWh sem otimização.")

    if "carro" in q or "veículo" in q or "veiculo" in q or "recarga" in q or "status" in q:
        return (f"Agora tem {int(agora['n_ativas'])} carro(s) recarregando, usando {agora['ev_kw']:.1f} kW. "
                f"Painéis: {agora['fv_kw']:.1f} kW. Rede: {agora['rede_kw']:.1f} kW.")

    return ("Não entendi. Posso responder sobre geração solar, bateria, economia, CO2, "
            "horário de ponta e status das recargas.")
