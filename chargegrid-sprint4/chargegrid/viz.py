"""Gráficos e diagrama de arquitetura (gerados a partir dos resultados reais da simulação)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

C = {"pv": "#f5a623", "ev": "#2b7de9", "grid": "#d0021b", "bat": "#2e9e5b", "base": "#8a8a8a"}


def plot_day(df_b, df_s, day, path):
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    for ax, df, title in zip(axes, (df_b, df_s), ("Baseline (sem otimização)", "ChargeGrid Smart (algoritmo inteligente)")):
        d = df[df.day == day]
        ax.fill_between(d.hour, 0, d.pv_kw, color=C["pv"], alpha=.35, label="Geração FV")
        ax.plot(d.hour, d.base_kw + d.ev_kw, color=C["ev"], lw=1.8, label="Carga (estação + VEs)")
        ax.plot(d.hour, d.grid_import_kw, color=C["grid"], lw=1.8, label="Importação da rede")
        ax.axvspan(18, 21, color="#d0021b", alpha=.07)
        ax2 = ax.twinx()
        ax2.plot(d.hour, d.soc * 100, color=C["bat"], ls="--", lw=1.6, label="SOC da bateria (%)")
        ax2.set_ylim(0, 105); ax2.set_ylabel("SOC (%)")
        ax.set_title(f"{title} – dia {day + 1} (faixa vermelha = horário de ponta)", fontsize=11)
        ax.set_ylabel("kW"); ax.grid(alpha=.25)
        h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8, ncol=2)
    axes[1].set_xlabel("Hora do dia"); axes[1].set_xlim(0, 24)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def plot_comparison(mb, ms, path):
    items = [("cost_brl", "Custo de energia (R$)"), ("peak_import_kwh", "Importação na ponta (kWh)"),
             ("grid_import_kwh", "Importação total da rede (kWh)"), ("self_sufficiency_pct", "Autossuficiência (%)")]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.8))
    for ax, (k, t) in zip(axes, items):
        vals = [mb[k], ms[k]]
        bars = ax.bar(["Baseline", "Smart"], vals, color=["#9aa5b1", C["bat"]])
        ax.set_title(t, fontsize=10)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def plot_sensitivity(sens, path):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.fill_between(sens.pv_kwp, sens["min"], sens["max"], color=C["bat"], alpha=.15, label="mín–máx (20 cenários)")
    ax.plot(sens.pv_kwp, sens.saving_brl_week, "o-", color=C["bat"], label="média")
    ax.legend(fontsize=8)
    ax.set_xlabel("Potência FV instalada (kWp)"); ax.set_ylabel("Economia do Smart vs Baseline (R$/semana)")
    ax.set_title("Sensibilidade ao dimensionamento solar", fontsize=11); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def plot_architecture(path):
    fig, ax = plt.subplots(figsize=(13.4, 6.4)); ax.set_xlim(0, 13.4); ax.set_ylim(-0.2, 6.4); ax.axis("off")

    def box(x, y, w, h, txt, color, dashed=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc=color, ec="#333",
                                    lw=1.2, ls="--" if dashed else "-", alpha=.9))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=8.5)

    def arrow(x1, y1, x2, y2, txt=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.3))
        if txt:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + .12, txt, fontsize=7, ha="center", color="#444")

    ax.text(1.9, 6.1, "CAMPO (Goodwe)", ha="center", weight="bold"); ax.text(6.5, 6.1, "ChargeGrid CORE (Python)", ha="center", weight="bold")
    ax.text(11.2, 6.1, "INTERFACES E CONTROLE", ha="center", weight="bold")
    box(0.2, 4.6, 3.4, .9, "Painéis FV (30 kWp)", "#fde7b0", True)
    box(0.2, 3.3, 3.4, .9, "Inversor híbrido Goodwe\n(SEMS / Modbus-UDP)", "#cfe3ff", True)
    box(0.2, 2.0, 3.4, .9, "Bateria Goodwe Lynx\n(20,4 kWh)", "#cdeccf", True)
    box(0.2, 0.7, 3.4, .9, "Carregadores AC 7,4 kW\n+ Rede elétrica", "#e6e6e6", True)
    box(4.4, 4.6, 4.2, .9, "Edge Arduino (Sprint 3)\nLDR · corrente · relé → JSON", "#fff")
    box(4.4, 3.3, 4.2, .9, "Telemetria unificada\n(CSV / JSON a cada 15 min)", "#fff")
    box(4.4, 2.0, 4.2, .9, "Motor Smart\nprevisão solar + urgência + reserva de bateria", "#d8f0d8")
    box(4.4, 0.7, 4.2, .9, "Métricas: kWh, R$, CO₂, autossuficiência", "#fff")
    box(9.6, 3.3, 3.2, .9, "Dashboard Streamlit", "#e8defa")
    box(9.6, 2.0, 3.2, .9, "Comandos: potência por sessão\n+ modo da bateria", "#e8defa")
    box(9.6, 0.7, 3.2, .9, "Assistente virtual\n(linguagem natural)", "#e8defa")
    # campo (cascata)
    arrow(1.9, 4.6, 1.9, 4.2); arrow(1.9, 3.3, 1.9, 2.9); arrow(1.9, 2.0, 1.9, 1.6)
    # campo -> core
    arrow(3.6, 3.75, 4.4, 3.75, "dados")
    # core
    arrow(6.5, 4.6, 6.5, 4.2); arrow(6.5, 3.3, 6.5, 2.9); arrow(6.5, 2.0, 6.5, 1.6)
    # core -> interfaces
    arrow(8.6, 3.75, 9.6, 3.75); arrow(8.6, 2.45, 9.6, 2.45); arrow(8.6, 1.15, 9.6, 1.15)
    # realimentação: comandos voltam ao campo (rota por fora das caixas)
    ax.plot([12.8, 13.15, 13.15, 1.9], [2.45, 2.45, 0.2, 0.2], color="#333", lw=1.3)
    arrow(1.9, 0.2, 1.9, 0.68)
    ax.text(7.5, 0.28, "comandos (potência dos carregadores / modo da bateria)", fontsize=7.5, ha="center", color="#444")
    ax.text(6.7, -0.12, "Tracejado = camada de campo simulada nesta entrega (dados sintéticos no formato Goodwe)", ha="center", fontsize=8, style="italic")
    fig.savefig(path, dpi=140, bbox_inches="tight"); plt.close(fig)
