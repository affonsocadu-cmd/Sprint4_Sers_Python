# dashboard.py
# Para abrir:  streamlit run dashboard.py

import pandas as pd
import streamlit as st
from parametros import PADRAO
from simulacao import rodar
from assistente import responder

st.set_page_config(page_title="ChargeGrid", layout="wide")
st.title("ChargeGrid - Estação de recarga solar inteligente")
st.caption("Dados simulados no estilo de um sistema híbrido Goodwe. As premissas estão no README.")

# parâmetros ajustáveis na barra lateral
st.sidebar.header("Parâmetros")
kwp = st.sidebar.slider("Potência dos painéis (kWp)", 10, 50, 30, 5)
bateria = st.sidebar.slider("Bateria (kWh)", 0.0, 40.8, 20.4, 10.2)
tarifa_ponta = st.sidebar.slider("Tarifa de ponta (R$/kWh)", 0.8, 2.5, 1.6, 0.1)
semente = st.sidebar.number_input("Semente do cenário", 0, 999, 42)

p = dict(PADRAO, potencia_fv=float(kwp), bat_kwh=float(bateria),
         tarifa_ponta=float(tarifa_ponta), semente=int(semente))


@st.cache_data
def simular_tudo(kwp, bateria, tarifa_ponta, semente):
    return rodar(dict(PADRAO, potencia_fv=float(kwp), bat_kwh=float(bateria),
                      tarifa_ponta=float(tarifa_ponta), semente=int(semente)))


df_b, df_i, m_base, m_int = simular_tudo(kwp, bateria, tarifa_ponta, semente)

economia_pct = 100 * (m_base["custo_reais"] - m_int["custo_reais"]) / m_base["custo_reais"]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Custo da semana", f"R$ {m_int['custo_reais']:.0f}", f"-{economia_pct:.1f}% vs sem otimização",
            delta_color="inverse")
col2.metric("Rede na ponta", f"{m_int['rede_ponta_kwh']:.0f} kWh",
            f"{m_int['rede_ponta_kwh'] - m_base['rede_ponta_kwh']:.0f} kWh", delta_color="inverse")
col3.metric("Autossuficiência", f"{m_int['autossuficiencia_pct']:.0f}%",
            f"{m_int['autossuficiencia_pct'] - m_base['autossuficiencia_pct']:+.1f} p.p.")
col4.metric("CO2 evitado (vs combustão)", f"{m_int['co2_evitado_kg']:.0f} kg",
            f"{m_int['km_recarregados']:.0f} km recarregados")

aba1, aba2, aba3 = st.tabs(["Dia a dia", "Comparação", "Assistente virtual"])

with aba1:
    dia = st.selectbox("Dia", sorted(df_i["dia"].unique()), format_func=lambda d: f"Dia {d + 1}")
    d = df_i[df_i["dia"] == dia].set_index("hora")
    b = df_b[df_b["dia"] == dia].set_index("hora")
    st.subheader("Potência (kW) - algoritmo inteligente")
    st.line_chart(d[["fv_kw", "ev_kw", "rede_kw"]].rename(
        columns={"fv_kw": "Painéis", "ev_kw": "Carros", "rede_kw": "Rede"}))
    st.subheader("Carga da bateria")
    st.line_chart(d[["soc"]].rename(columns={"soc": "Inteligente"}).join(
        b[["soc"]].rename(columns={"soc": "Sem otimização"})))

with aba2:
    tabela = pd.DataFrame({"Sem otimização": m_base, "Inteligente": m_int}).round(2)
    st.dataframe(tabela)

with aba3:
    st.write("Exemplos: *quanto gerei hoje?*, *qual a economia?*, *como está a bateria?*")
    pergunta = st.chat_input("Digite sua pergunta")
    if pergunta:
        st.chat_message("user").write(pergunta)
        st.chat_message("assistant").write(responder(pergunta, df_i, m_int, m_base, p))
