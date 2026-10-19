"""Ponte Edge (Arduino da Sprint 3) -> ChargeGrid.
Lê o JSON de telemetria impresso pelo Arduino, estima a geração FV a partir do LDR (solar_pct) e decide
LIBERAR/ADIAR a recarga com as mesmas regras do algoritmo Smart (sol primeiro, nunca na ponta, exceto urgência).

Uso:  python edge/edge_bridge.py --demo
      python edge/edge_bridge.py --port COM3        (requer pyserial)
Para fechar o laço, o sketch precisa ler 'RELAY_ON'/'RELAY_OFF' da Serial e acionar o relé (adaptar ao sketch.ino)."""
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chargegrid.config import Config

DEMO = [  # pacotes no formato da Sprint 3
    {"station_id": "CHARGEGRID_UNO_01", "solar_pct": 85.0, "voltage_v": 220.0, "current_a": 15.5, "power_w": 3410.0, "status": "CHARGING"},
    {"station_id": "CHARGEGRID_UNO_01", "solar_pct": 12.0, "voltage_v": 220.0, "current_a": 0.0, "power_w": 0.0, "status": "STANDBY"},
    {"station_id": "CHARGEGRID_UNO_01", "solar_pct": 55.0, "voltage_v": 220.0, "current_a": 9.0, "power_w": 1980.0, "status": "CHARGING"},
]


def decide(pkt, hour, urgent=False, cfg=Config(), base_kw=1.5):
    pv_kw = pkt["solar_pct"] / 100 * cfg.pv_kwp * cfg.pv_pr
    surplus = pv_kw - base_kw
    in_peak = cfg.peak_hours[0] <= hour < cfg.peak_hours[1]
    if urgent:
        cmd, why = "RELAY_ON", "urgência: veículo precisa sair"
    elif in_peak:
        cmd, why = "RELAY_OFF", "horário de ponta"
    elif pkt["solar_pct"] > 20 and surplus >= 1.0:   # mantém o limiar de 20% da Sprint 3
        cmd, why = "RELAY_ON", f"excedente solar estimado de {surplus:.1f} kW"
    else:
        cmd, why = "RELAY_OFF", "sol insuficiente"
    return {"command": cmd, "reason": why, "pv_kw_est": round(pv_kw, 2)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--demo", action="store_true"); ap.add_argument("--port"); ap.add_argument("--hour", type=float, default=12.0)
    a = ap.parse_args()
    if a.demo or not a.port:
        for p in DEMO:
            print(json.dumps({**p, **decide(p, a.hour)}, ensure_ascii=False))
    else:
        import serial
        with serial.Serial(a.port, 9600, timeout=3) as ser:
            while True:
                line = ser.readline().decode(errors="ignore").strip()
                if line.startswith("{"):
                    try:
                        pkt = json.loads(line)
                    except ValueError:
                        continue
                    out = decide(pkt, a.hour); print(json.dumps({**pkt, **out}, ensure_ascii=False))
                    ser.write((out["command"] + "\n").encode())
