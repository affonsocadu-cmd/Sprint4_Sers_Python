# ponte_arduino.py
# Liga o Arduino da Sprint 3 ao programa. Lê o JSON que o Arduino imprime,
# estima a geração dos painéis pelo LDR (solar_pct) e decide LIBERAR ou ADIAR a recarga.
#
# Testar sem Arduino:   python ponte_arduino.py --demo
# Com Arduino:          python ponte_arduino.py --porta COM3
# Obs: para o relé responder, o sketch precisa ler "RELE_ON" / "RELE_OFF" pela Serial
# (isso ainda precisa ser adaptado no sketch.ino).

import argparse
import json
from parametros import PADRAO

# pacotes de exemplo no formato da Sprint 3
EXEMPLOS = [
    {"solar_pct": 85.0, "tensao_v": 220.0, "corrente_a": 15.5, "status": "CARREGANDO"},
    {"solar_pct": 12.0, "tensao_v": 220.0, "corrente_a": 0.0, "status": "PARADO"},
    {"solar_pct": 55.0, "tensao_v": 220.0, "corrente_a": 9.0, "status": "CARREGANDO"},
]


def decidir(pacote, hora, urgente=False):
    p = PADRAO
    fv_estimado = pacote["solar_pct"] / 100 * p["potencia_fv"] * p["desempenho_fv"]
    sobra = fv_estimado - 1.5      # desconta o consumo da estação
    em_ponta = p["ponta_inicio"] <= hora < p["ponta_fim"]

    if urgente:
        comando, motivo = "RELE_ON", "carro precisa sair"
    elif em_ponta:
        comando, motivo = "RELE_OFF", "horário de ponta"
    elif pacote["solar_pct"] > 20 and sobra >= 1.0:     # mantém o limite de 20% da Sprint 3
        comando, motivo = "RELE_ON", f"sobra de sol de {sobra:.1f} kW"
    else:
        comando, motivo = "RELE_OFF", "pouco sol"
    return {"comando": comando, "motivo": motivo, "fv_estimado_kw": round(fv_estimado, 2)}


parser = argparse.ArgumentParser()
parser.add_argument("--demo", action="store_true")
parser.add_argument("--porta")
parser.add_argument("--hora", type=float, default=12.0)
args = parser.parse_args()

if args.demo or not args.porta:
    for pacote in EXEMPLOS:
        print(json.dumps({**pacote, **decidir(pacote, args.hora)}, ensure_ascii=False))
else:
    import serial
    with serial.Serial(args.porta, 9600, timeout=3) as arduino:
        while True:
            linha = arduino.readline().decode(errors="ignore").strip()
            if linha.startswith("{"):
                try:
                    pacote = json.loads(linha)
                except ValueError:
                    continue
                resultado = decidir(pacote, args.hora)
                print(json.dumps({**pacote, **resultado}, ensure_ascii=False))
                arduino.write((resultado["comando"] + "\n").encode())
