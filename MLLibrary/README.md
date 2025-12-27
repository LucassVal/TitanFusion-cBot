# ML Library - cTrader Trading Bot Components

Biblioteca de Machine Learning reutilizável para bots de trading cTrader.
**Atualizado**: Dezembro 2024 | **14 Engines**

## Arquivos da Biblioteca

| Arquivo | Engine # | Descrição | Fonte |
|---------|----------|-----------|-------|
| `ML_AdaptiveATR.cs` | #1 | Ajusta threshold ATR baseado em precisão | Original |
| `ML_MinMTF.cs` | #2 | Ajusta alinhamento MTF mínimo | Original |
| `ML_RRRatio.cs` | #3 | Ajusta Risk/Reward baseado em win rate | Original |
| `ML_TunnelPeriod.cs` | #4 | Ajusta período HMA tunnel | Original |
| `ML_SwingStrength.cs` | #5 | Ajusta força de swing para S/R | Original |
| `ML_MACD_Adaptive.cs` | #6 | Ajusta parâmetros MACD com ADX | Original |
| `ML_Session.cs` | #7 | Identifica Golden/Dead hours | Original |
| `ML_VolatilityRegime.cs` | #8 | Detecta regime (Trending/Ranging/Spiking) | Original |
| `ML_RSI_Divergence.cs` | #9 | RSI adaptativo + detecção de divergência | Original |
| `ML_Correlation.cs` | #10 | Análise multi-símbolo para bias | Original |
| `ML_KAMASlope.cs` | #11 | KAMA Slope para trend/ranging | GitHub: opplieam |
| `ML_OrderFlow.cs` | #12 | Delta volume (buy/sell pressure) | GitHub: srlcarlg |
| `ML_StrategyScore.cs` | #13 | Score multi-fator para sinais | GitHub: johndpope |
| `ML_KalmanFilter.cs` | #14 | Filtro Kalman adaptativo | GitHub: johndpope |

---

## Engines v2.0 (Novos - GitHub)

### ML_KAMASlope (#11)
- **Fonte**: opplieam/ctrader-bot-indicator
- **Uso**: Detectar ranging (slope = 0) vs trending (+/-)
- **Funções**: `CalculateKAMA()`, `GetKAMASlope()`, `IsKAMARanging()`, `GetKAMADirection()`

### ML_OrderFlow (#12)
- **Fonte**: srlcarlg/srl-ctrader-indicators (conceito)
- **Uso**: Estimar pressão compra/venda usando estrutura de candle
- **Funções**: `CalculateOrderFlowDelta()`, `GetOrderFlowSignal()`, `IsOrderFlowConfirming()`

### ML_StrategyScore (#13)
- **Fonte**: johndpope/CryptoCurrencyTrader
- **Uso**: Score 0-100 de qualidade do sinal
- **Fatores**: Trend (20pts), RSI (15pts), ADX (15pts), Volume (10pts), ATR (10pts)
- **Funções**: `CalculateStrategyScore()`, `GetSignalQuality()`

### ML_KalmanFilter (#14)
- **Fonte**: johndpope/CryptoCurrencyTrader
- **Uso**: Suavização adaptativa de preço com redução de ruído
- **Funções**: `UpdateKalmanFilter()`, `GetKalmanDeviation()`, `AdaptKalmanToVolatility()`

---

## Como Usar

1. **Copie o código** do arquivo para dentro do seu indicador/bot
2. **Adicione os campos requeridos** (listados no cabeçalho de cada arquivo)
3. **Chame as funções** nos locais apropriados:
   - `OnStart()`: InitializeCorrelations
   - `OnBar()`: DetectVolatilityRegime, CalculateCorrelationBias, AdjustSessionSchedule
   - Após validar sinais: AdjustATRThreshold, AdjustMinMtfAlignment, etc.

## Parâmetros Recomendados

```csharp
[Parameter("Enable ML Engines", DefaultValue = true, Group = "ML")]
public bool EnableMLEngines { get; set; }

[Parameter("ML Adjustment Frequency", DefaultValue = 10, Group = "ML")]
public int MLAdjustmentFrequency { get; set; }

[Parameter("Use Multi-Symbol ML", DefaultValue = true, Group = "ML")]
public bool UseMultiSymbolML { get; set; }

[Parameter("ML Enable MACD", DefaultValue = true, Group = "ML")]
public bool MLEnableMACD { get; set; }
```

## Dependências

- cAlgo.API
- cAlgo.API.Indicators
- System.Linq
- System.Collections.Generic

---

## Fontes GitHub

| Repositório | Descrição | Linguagem |
|-------------|-----------|-----------|
| [srlcarlg/srl-ctrader-indicators](https://github.com/srlcarlg/srl-ctrader-indicators) | Order Flow, Volume Profile, Wyckoff | C# (cTrader) |
| [opplieam/ctrader-bot-indicator](https://github.com/opplieam/ctrader-bot-indicator) | KAMA, SSL, QQE | C# (cTrader) |
| [johndpope/CryptoCurrencyTrader](https://github.com/johndpope/CryptoCurrencyTrader) | Strategy Score, Kalman Filter | Python |

---

*Versão 2.0 | Dezembro 2024*
