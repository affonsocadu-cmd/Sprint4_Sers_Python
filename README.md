#  ChargeGrid – Estação de Recarga Solar Inteligente com Tecnologia Goodwe
**Sprint 4 – Solução Final Integrada e Inovadora**

## 1. Equipe
> _ Carlos Eduardo Affonso - RM 569676
> _ Gabriel Oliveira Gusmão Florêncio dos Santos - RM 573747
> _ Gustavo de Souza Abreu - RM 574080
> _ Gabrieli de Lima Pettena de Oliveira - RM 569799
> _ Igor Massone Monteiro - RM 573853
> _ Temitope Kuku da Silva Ogunbanjo - RM 573772

## 2. Resumo
O **ChargeGrid** é uma estação de recarga de veículos elétricos (VEs) alimentada por energia solar com armazenamento em bateria.
Na Sprint 3 construímos o **nó de borda** (Arduino + LDR + relé) que liberava a recarga apenas com luminosidade > 20%.
Na Sprint 4 evoluímos para uma **solução integrada**: modelo de geração–armazenamento–consumo no padrão de um sistema híbrido Goodwe,
um **algoritmo inteligente** de agendamento de recargas, **dashboard**, **assistente virtual** e **métricas de impacto**.

**Resultado principal (simulação de 7 dias, 30 kWp + 20,4 kWh + 4–7 recargas/dia):** o algoritmo reduziu o custo de energia em **25%**
(R$ 157,27 → R$ 118,35) e a importação da rede no horário de ponta em **75%** (57,9 → 14,5 kWh), atendendo **100%** da energia solicitada pelos veículos.

>  **Transparência:** todos os dados de geração, carga e sessões são **sintéticos** (gerados em `chargegrid/data.py` com semente fixa).
> A integração com um inversor Goodwe real **não foi executada** nesta entrega; o formato de telemetria foi modelado para ser compatível (ver seção 4).

## 3. Arquitetura final

![Arquitetura](docs/img/arquitetura.png)

| Camada | Componente | Papel | Estado nesta entrega |
|---|---|---|---|
| Campo | Painéis FV + **inversor híbrido Goodwe** + **bateria Goodwe Lynx** + carregadores AC 7,4 kW | Gera, armazena e entrega energia | Simulado (`engine.py`) |
| Borda | Arduino Uno + LDR + relé (Sprint 3) | Mede luminosidade, aciona relé, emite JSON | Sprint 3 (Wokwi); ponte em `edge/edge_bridge.py` |
| Core | `chargegrid/` (Python) | Telemetria, política de controle, métricas | Implementado e testado |
| Interfaces | Streamlit, assistente virtual | Visualização e linguagem natural | Implementado |

**Fluxo de dados:** (1) telemetria em passos de 15 min → (2) o motor Smart decide a potência de cada sessão de recarga e o modo da bateria → (3) o motor de simulação aplica o balanço de energia → (4) métricas → (5) dashboard/assistente. Os comandos retornam ao campo (relé do Arduino / potência dos carregadores).

### 3.1 O algoritmo inteligente (`chargegrid/policies.py`)
1. **Urgência:** se a folga entre o tempo restante e o tempo mínimo para completar a carga ≤ 30 min, carrega à potência máxima → **garante o atendimento**.
2. **Sol primeiro:** fora da urgência, carrega apenas com o excedente solar (geração − carga base), priorizando quem sai antes.
3. **Previsão:** se o excedente solar previsto até a saída não cobre a energia faltante, antecipa a carga pela rede, **nunca na ponta** (18h–21h).
4. **Reserva dinâmica da bateria:** descarrega livremente na ponta; fora dela só usa o que excede uma reserva (45%) e, de madrugada, esvazia até o mínimo para abrir espaço ao sol do dia seguinte.

O **baseline** representa um sistema sem otimização: recarga imediata em potência máxima e bateria em autoconsumo simples (comportamento padrão de um inversor híbrido).

## 4. Alinhamento ao desafio Goodwe

| Ponto do desafio | Como a solução responde |
|---|---|
| Geração, armazenamento e uso de energia renovável | Balanço completo FV + bateria (eficiência ida/volta ≈ 90%, SOC mín. 10%) + rede + VEs |
| Tecnologias compatíveis Goodwe | Parâmetros dimensionados para inversor híbrido e baterias Lynx; telemetria com os mesmos conceitos de monitoramento (potência FV, SOC, potência de rede). **Caminho de integração real:** SEMS Portal (nuvem) ou leitura local do inversor (Modbus/UDP, p. ex. biblioteca Python `goodwe`) substituindo `data.py`/`engine.py` por leituras reais. _Verificar modelos e protocolos no datasheet do inversor escolhido; não testamos com hardware._ |
| Monitoramento inteligente | Telemetria a cada 15 min, KPIs e dashboard |
| Algoritmos inteligentes / automação | Política Smart com urgência, previsão e reserva dinâmica |
| Interface amigável e visualização | Dashboard Streamlit com parâmetros ajustáveis |
| Assistente virtual | `assistant.py`: perguntas em português ("quanto gerei hoje?"); reaproveitável via webhook para Alexa/Google ou trocável por um LLM |
| Sustentabilidade | Solar direto nos VEs, redução de pico, CO₂ evitado vs. combustão |

## 5. Resultados (reproduzíveis com `python run_simulation.py`)

![Perfil do dia](docs/img/perfil_dia.png)
![KPIs](docs/img/comparacao_kpis.png)

**Cenário base** (30 kWp, 20,4 kWh, 7 dias, semente 42):

| Indicador | Baseline | Smart | Variação |
|---|---:|---:|---:|
| Geração FV (kWh) | 906,0 | 906,0 | – |
| Energia entregue aos VEs (kWh) | 767,2 | 767,2 | – |
| **Atendimento das recargas (%)** | 100 | 100 | = |
| Importação da rede (kWh) | 257,9 | 255,5 | −1% |
| **Importação na ponta (kWh)** | 57,9 | 14,5 | **−75%** |
| **Custo da energia (R$/semana)** | 157,27 | 118,35 | **−25%** |
| Autoconsumo solar (%) | 79,05 | 79,00 | ≈ |
| Autossuficiência (%) | 73,1 | 73,3 | ≈ |
| Pico de demanda da rede (kW) | 27,8 | 32,9 | **+18% (piora)** |

**Robustez (20 cenários aleatórios):** economia média de custo **18,3%** (mín. 9,3% – máx. 32,6%); redução média da importação na ponta **70,9%**.

**Sensibilidade ao dimensionamento solar** (economia média do Smart sobre o baseline, 20 cenários cada):

| kWp | Custo baseline (R$/sem) | Economia Smart (R$/sem) |
|---:|---:|---:|
| 10 | 533,7 | 16,6 |
| 20 | 340,8 | 26,2 |
| 30 | 168,9 | 28,3 |
| 40 | 18,5 | 24,5 |

![Sensibilidade](docs/img/sensibilidade_pv.png)

**Pegada de carbono (premissas na seção 7):**
- Energia solar autoconsumida (~716 kWh/semana) evita ≈ **29 kg CO₂/semana** em relação à rede (a matriz brasileira já é limpa, então esse ganho é pequeno).
- A maior contribuição está na **eletrificação**: 4.603 km recarregados/semana evitam ≈ **864 kg CO₂** frente a carros a combustão.

**Resultados qualitativos:** o gráfico do dia mostra o comportamento esperado: o Smart adia recargas para o pico solar, enche a bateria no meio do dia e a usa na ponta, enquanto o baseline recarrega imediatamente e importa na ponta.

## 6. Avaliação crítica
**Benefícios**
- Ganho **financeiro e de rede** consistente (custo −25%, ponta −75%), sem prejudicar o serviço (100% atendido).
- Autoconsumo e autossuficiência **não pioraram** (a primeira versão da política piorou o autoconsumo; corrigimos com a reserva dinâmica).

**Limitações assumidas**
- **O ganho depende do dimensionamento:** com PV subdimensionado (10 kWp) a economia é de apenas ~3%; a otimização só rende quando há sol sobrando para deslocar. Com 40 kWp o benefício volta a cair, pois o custo já é baixo.
- **Quase todo o ganho é financeiro/tarifário**, não de energia: a importação total mudou ~1%.
- **Pico de demanda piorou** (27,8 → 32,9 kW): o Smart concentra recargas urgentes. Não otimizamos limite de potência contratada.
- Ainda há importação entre 20h e 21h quando a bateria esvazia antes do fim da ponta.
- A previsão solar é um fator fixo sobre o céu limpo (não usa meteorologia real); a heurística não é ótima (um otimizador/MPC ou aprendizado de máquina é o próximo passo).
- Dados 100% simulados; tarifas e fatores de emissão são ilustrativos; sem hardware Goodwe.

**Inovação:** agendamento ciente de prazos (garantia de atendimento), previsão simples, reserva dinâmica de bateria, ponte edge↔core, assistente conversacional e análise de sensibilidade/robustez (em vez de um único cenário favorável).

## 7. Premissas (todas editáveis em `chargegrid/config.py`)
Tarifa fora da ponta R$ 0,75/kWh, ponta (18–21h) R$ 1,60/kWh, crédito de exportação R$ 0,45/kWh (**valores ilustrativos**) · fator da rede 0,04 kgCO₂/kWh (ordem de grandeza da média do SIN; **conferir fator oficial vigente**) · carro a combustão 0,19 kgCO₂/km · VE 6 km/kWh · carregadores 7,4 kW (um por sessão) · PR do sistema FV 0,80.

## 8. Como executar
```bash
pip install -r requirements.txt
python run_simulation.py          # gera results/ e docs/img/
streamlit run dashboard.py        # dashboard + assistente virtual
python -m pytest -q tests         # balanço de energia, limites de SOC, atendimento, robustez
python edge/edge_bridge.py --demo # ponte com o Arduino (use --port COM3 com hardware)
```
(No Windows, se `import chargegrid` falhar, defina `set PYTHONPATH=.` antes.)

## 9. Estrutura do repositório
```
chargegrid/   config · data · policies · engine · metrics · assistant · viz
edge/         edge_bridge.py (Arduino → decisão Smart)
tests/        testes automatizados (pytest)
results/      CSVs de telemetria, metrics.json, robustness.json, sensitivity_pv.csv
docs/         img/ (gráficos e arquitetura) · roteiro_video.md
firmware/     (mover para cá o sketch.ino e o diagram.json da Sprint 3)
dashboard.py  run_simulation.py
```

## 10. Referências e ferramentas
Python 3, NumPy, pandas, Matplotlib, Streamlit, pytest · Arduino/Wokwi (Sprint 3) · Goodwe: SEMS Portal, inversores híbridos e baterias Lynx (consultar documentação oficial) · biblioteca Python `goodwe` (leitura local de inversores) · fatores de emissão do MCTI para o SIN.
