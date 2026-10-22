# graficos.py
# Gráficos e diagrama de arquitetura (usa matplotlib).

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def grafico_dia(df_b, df_i, dia, caminho):
    fig, eixos = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    titulos = ["Sem otimização", "Algoritmo inteligente"]
    for ax, df, titulo in zip(eixos, [df_b, df_i], titulos):
        d = df[df["dia"] == dia]
        ax.fill_between(d["hora"], 0, d["fv_kw"], color="orange", alpha=0.35, label="Geração solar")
        ax.plot(d["hora"], d["base_kw"] + d["ev_kw"], color="tab:blue", label="Consumo (estação + carros)")
        ax.plot(d["hora"], d["rede_kw"], color="tab:red", label="Energia da rede")
        ax.axvspan(18, 21, color="red", alpha=0.07)
        ax.set_title(f"{titulo} - dia {dia + 1} (faixa vermelha = horário de ponta)")
        ax.set_ylabel("kW")
        ax.grid(alpha=0.3)
        ax2 = ax.twinx()
        ax2.plot(d["hora"], d["soc"] * 100, color="green", linestyle="--", label="Bateria (%)")
        ax2.set_ylim(0, 105)
        ax2.set_ylabel("Bateria (%)")
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8, ncol=2)
    eixos[1].set_xlabel("Hora do dia")
    eixos[1].set_xlim(0, 24)
    fig.tight_layout()
    fig.savefig(caminho, dpi=140)
    plt.close(fig)


def grafico_comparacao(m_base, m_int, caminho):
    itens = [("custo_reais", "Custo (R$)"),
             ("rede_ponta_kwh", "Rede na ponta (kWh)"),
             ("rede_kwh", "Rede total (kWh)"),
             ("autossuficiencia_pct", "Autossuficiência (%)")]
    fig, eixos = plt.subplots(1, 4, figsize=(13, 3.8))
    for ax, (chave, titulo) in zip(eixos, itens):
        valores = [m_base[chave], m_int[chave]]
        barras = ax.bar(["Sem otim.", "Inteligente"], valores, color=["gray", "green"])
        ax.set_title(titulo, fontsize=10)
        for b, v in zip(barras, valores):
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(caminho, dpi=140)
    plt.close(fig)


def grafico_sensibilidade(tabela, caminho):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.fill_between(tabela["kwp"], tabela["min"], tabela["max"], color="green", alpha=0.15,
                    label="mínimo e máximo (20 cenários)")
    ax.plot(tabela["kwp"], tabela["economia_media"], "o-", color="green", label="média")
    ax.set_xlabel("Potência dos painéis (kWp)")
    ax.set_ylabel("Economia do inteligente (R$ por semana)")
    ax.set_title("Economia conforme o tamanho do sistema solar")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(caminho, dpi=140)
    plt.close(fig)


def diagrama_arquitetura(caminho):
    fig, ax = plt.subplots(figsize=(13.4, 6.4))
    ax.set_xlim(0, 13.4)
    ax.set_ylim(-0.2, 6.4)
    ax.axis("off")

    def caixa(x, y, w, h, texto, cor, tracejada=False):
        estilo = "--" if tracejada else "-"
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc=cor, ec="black",
                                    lw=1.2, ls=estilo, alpha=0.9))
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=8.5)

    def seta(x1, y1, x2, y2, texto=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.3))
        if texto:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.12, texto, fontsize=7, ha="center")

    ax.text(1.9, 6.1, "CAMPO (Goodwe)", ha="center", weight="bold")
    ax.text(6.5, 6.1, "PROGRAMA EM PYTHON", ha="center", weight="bold")
    ax.text(11.2, 6.1, "INTERFACES E CONTROLE", ha="center", weight="bold")

    caixa(0.2, 4.6, 3.4, 0.9, "Painéis solares (30 kWp)", "#fde7b0", True)
    caixa(0.2, 3.3, 3.4, 0.9, "Inversor híbrido Goodwe\n(SEMS / Modbus)", "#cfe3ff", True)
    caixa(0.2, 2.0, 3.4, 0.9, "Bateria Goodwe Lynx\n(20,4 kWh)", "#cdeccf", True)
    caixa(0.2, 0.7, 3.4, 0.9, "Carregadores 7,4 kW\n+ rede elétrica", "#e6e6e6", True)

    caixa(4.4, 4.6, 4.2, 0.9, "Arduino (Sprint 3)\nLDR + relé -> JSON", "white")
    caixa(4.4, 3.3, 4.2, 0.9, "Dados de telemetria\n(CSV / JSON, a cada 15 min)", "white")
    caixa(4.4, 2.0, 4.2, 0.9, "Algoritmo inteligente\nprevisão do sol + prazo + bateria", "#d8f0d8")
    caixa(4.4, 0.7, 4.2, 0.9, "Métricas: kWh, R$, CO2", "white")

    caixa(9.6, 3.3, 3.2, 0.9, "Dashboard (Streamlit)", "#e8defa")
    caixa(9.6, 2.0, 3.2, 0.9, "Comandos: potência dos\ncarregadores e bateria", "#e8defa")
    caixa(9.6, 0.7, 3.2, 0.9, "Assistente virtual", "#e8defa")

    seta(1.9, 4.6, 1.9, 4.2)
    seta(1.9, 3.3, 1.9, 2.9)
    seta(1.9, 2.0, 1.9, 1.6)
    seta(3.6, 3.75, 4.4, 3.75, "dados")
    seta(6.5, 4.6, 6.5, 4.2)
    seta(6.5, 3.3, 6.5, 2.9)
    seta(6.5, 2.0, 6.5, 1.6)
    seta(8.6, 3.75, 9.6, 3.75)
    seta(8.6, 2.45, 9.6, 2.45)
    seta(8.6, 1.15, 9.6, 1.15)

    # comandos voltam para o campo
    ax.plot([12.8, 13.15, 13.15, 1.9], [2.45, 2.45, 0.2, 0.2], color="black", lw=1.3)
    seta(1.9, 0.2, 1.9, 0.68)
    ax.text(7.5, 0.28, "comandos de volta para o campo", fontsize=7.5, ha="center")
    ax.text(6.7, -0.12, "Tracejado = parte simulada nesta entrega (dados sintéticos)",
            ha="center", fontsize=8, style="italic")

    fig.savefig(caminho, dpi=140, bbox_inches="tight")
    plt.close(fig)
