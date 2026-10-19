"""Dashboard ChargeGrid – execute com:  streamlit run dashboard.py"""
from dataclasses import replace
import streamlit as st
from chargegrid.config import Config
from run_simulation import run, saving
from chargegrid.assistant import Assistant

st.set_page_config(page_title="ChargeGrid", page_icon="⚡", layout="wide")
st.title("⚡ ChargeGrid – Estação de recarga solar inteligente (Goodwe)")
st.caption("Dados simulados no formato de telemetria de inversores híbridos Goodwe. Ver premissas no README.")

with st.sidebar:
    st.header("Parâmetros")
    kwp = st.slider("Potência FV (kWp)", 10, 50, 30, 5)
    bat = st.slider("Bateria (kWh)", 0.0, 40.8, 20.4, 10.2)
    peak = st.slider("Tarifa de ponta (R$/kWh)", 0.8, 2.5, 1.60, 0.1)
    seed = st.number_input("Semente do cenário", 0, 999, 42)


@st.cache_data
def simulate_all(kwp, bat, peak, seed):
    return run(replace(Config(), pv_kwp=float(kwp), bat_kwh=float(bat), tariff_peak=float(peak), seed=int(seed)))


cfg = replace(Config(), pv_kwp=float(kwp), bat_kwh=float(bat), tariff_peak=float(peak), seed=int(seed))
db, ds, mb, ms = simulate_all(kwp, bat, peak, seed)

c = st.columns(4)
c[0].metric("Custo semanal (Smart)", f"R$ {ms['cost_brl']:.0f}", f"{-saving(mb, ms):.1f}% vs baseline", delta_color="inverse")
c[1].metric("Importação na ponta", f"{ms['peak_import_kwh']:.0f} kWh", f"{ms['peak_import_kwh'] - mb['peak_import_kwh']:.0f} kWh", delta_color="inverse")
c[2].metric("Autossuficiência", f"{ms['self_sufficiency_pct']:.0f}%", f"{ms['self_sufficiency_pct'] - mb['self_sufficiency_pct']:+.1f} p.p.")
c[3].metric("CO₂ evitado vs combustão", f"{ms['co2_avoided_vs_ice_kg']:.0f} kg", f"{ms['km_charged']:.0f} km recarregados")

tab1, tab2, tab3 = st.tabs(["Dia a dia", "Comparação", "Assistente virtual"])
with tab1:
    day = st.selectbox("Dia", sorted(ds.day.unique()), format_func=lambda d: f"Dia {d + 1}")
    d = ds[ds.day == day].set_index("hour")
    b = db[db.day == day].set_index("hour")
    st.subheader("Potência (kW) – Smart")
    st.line_chart(d[["pv_kw", "ev_kw", "grid_import_kw"]].rename(columns={"pv_kw": "Geração FV", "ev_kw": "Recarga VEs", "grid_import_kw": "Rede"}))
    st.subheader("Bateria (SOC) – Smart vs Baseline")
    st.line_chart(d[["soc"]].rename(columns={"soc": "Smart"}).join(b[["soc"]].rename(columns={"soc": "Baseline"})))
with tab2:
    import pandas as pd
    st.dataframe(pd.DataFrame({"Baseline": mb, "Smart": ms}).round(2))
    st.bar_chart(pd.DataFrame({"Baseline": [mb["cost_brl"], mb["peak_import_kwh"]], "Smart": [ms["cost_brl"], ms["peak_import_kwh"]]},
                              index=["Custo (R$)", "Importação na ponta (kWh)"]))
with tab3:
    bot = Assistant(ds, ms, mb, cfg)
    st.write("Pergunte, por exemplo: *quanto gerei hoje?*, *qual a economia?*, *como está a bateria?*")
    q = st.chat_input("Digite sua pergunta")
    if q:
        st.chat_message("user").write(q)
        st.chat_message("assistant").write(bot.ask(q))
