# testes.py
# Testes simples. Rode com:  python testes.py

from parametros import PADRAO
from simulacao import gerar_cenario, simular, rodar

p = dict(PADRAO)
cenario = gerar_cenario(p)

for politica in ["sem_otimizacao", "inteligente"]:
    df, entregas = simular(cenario, politica, p)

    # 1) conservação de energia: o que entra tem que ser igual ao que sai
    entra = df["fv_kw"] + df["rede_kw"] + df["bat_descarga_kw"]
    sai = df["base_kw"] + df["ev_kw"] + df["exporta_kw"] + df["bat_carga_kw"]
    assert (entra - sai).abs().max() < 0.000001, "balanço de energia não fechou"

    # 2) a bateria nunca passa dos limites
    assert df["soc"].min() >= p["soc_min"] - 0.000001
    assert df["soc"].max() <= 1.000001

    # 3) todos os carros recebem a energia que pediram
    atendimento = 100 * entregas["entregue"].sum() / entregas["energia"].sum()
    assert atendimento > 99.9, "algum carro ficou sem carga"

    print("ok:", politica)

# 4) o algoritmo inteligente não pode custar mais que o outro (testa com 10 sementes)
for semente in range(10):
    _, _, mb, mi = rodar(dict(p, semente=semente))
    assert mi["custo_reais"] <= mb["custo_reais"] * 1.01, f"semente {semente}: ficou mais caro"
print("ok: custo com 10 cenários diferentes")
print("Todos os testes passaram.")
