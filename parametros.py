# parametros.py
# Valores que dá pra mudar para testar outros cenários.
# As tarifas e os fatores de emissão são EXEMPLOS (não são dados oficiais).

PASSO_H = 0.25        # cada passo da simulação = 15 minutos
PASSOS_POR_DIA = 96

PADRAO = {
    "dias": 7,
    "semente": 42,

    # painéis solares
    "potencia_fv": 30.0,       # kWp
    "desempenho_fv": 0.80,     # perdas gerais do sistema

    # bateria (2 módulos de uns 10 kWh, como as baterias Lynx da Goodwe)
    "bat_kwh": 20.4,
    "bat_pot_max": 10.0,       # kW
    "bat_efic": 0.95,          # eficiência de um sentido (carregar ou descarregar)
    "soc_min": 0.10,
    "soc_inicial": 0.30,

    # carregadores dos carros
    "carregador_kw": 7.4,
    "sessoes_min": 4,          # carros por dia (mínimo)
    "sessoes_max": 7,          # carros por dia (máximo)

    # tarifa em R$/kWh
    "tarifa_normal": 0.75,
    "tarifa_ponta": 1.60,
    "ponta_inicio": 18,
    "ponta_fim": 21,
    "credito_exportacao": 0.45,

    # emissões
    "fator_rede": 0.04,        # kg de CO2 por kWh da rede
    "fator_combustao": 0.19,   # kg de CO2 por km de um carro a combustão
    "km_por_kwh": 6.0,         # km que o carro elétrico faz por kWh
}
