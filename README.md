# 🚀 Titan Pro - Hybrid GPU Trading System

**Advanced multi-strategy algorithmic trading bot with GPU-accelerated optimization for Deriv (Synthetic Indices) and Forex markets.**

![Python](https://img.shields.io/badge/Python-3.12-blue)
![GPU](https://img.shields.io/badge/GPU-CUDA%20%2B%20OpenCL-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Production-success)

---

## 📋 Table of Contents
- [Quick Start](#-quick-start)
- [Key Features](#-key-features)
- [Trading Strategies](#-trading-strategies-detailed)
- [System Architecture](#-system-architecture)
- [Risk Management](#%EF%B8%8F-risk-management-system)
- [Installation](#-installation)
- [Configuration](#%EF%B8%8F-configuration)
- [Performance](#-performance-metrics)

---

## ⚡ Quick Start

### One-Line Installer
```powershell
irm https://raw.githubusercontent.com/LucassVal/TitanFusion-cBot/main/install.ps1 | iex
```

### Manual Installation
```bash
# 1. Clone repository
git clone https://github.com/LucassVal/TitanFusion-cBot.git
cd TitanFusion-cBot

# 2. Install dependencies
pip install pandas pandas_ta numpy pyopencl websockets requests

# 3. Run launcher
cd "Titan pro"
python launcher.py
```

---

## 🎯 Key Features

### 💰 Smart Capital Management
- **Real Balance Integration**: Fetches actual Deriv account balance
- **Working Capital Selection**: Trade with a fraction (e.g., 50%) or full balance
- **Dynamic Position Sizing**: Risk calculated on working capital

### 🛡️ Tiered Drawdown Protection
| Phase | DD Limit | Purpose |
|-------|----------|---------|
| Training | 25% | Allow aggressive discovery |
| Validation | 30% | Stress-test robustness |
| Live Trading | 12% | Maximum capital protection |

### 🧠 Full Revolution GPU Engine (v2.1)
- **500,000 Parameter Combinations** tested per cycle
- **40 Parameters per Strategy** (vs 15 previously)
- **New Indicators**: ADX, MFE, MAE, Sortino Ratio
- **Ultra-Robust Fitness**: Rewards volume (50-200 trades) and consistency

### 📈 5% Daily Profit Target
- Optimized fitness function rewards 4-6% daily returns
- **Volume Bonus**: Targets active trading frequency
- Conservative risk per trade (2-4%)

### 🔄 Auto-Reconnection
- **Ping Keepalive**: Every 30 seconds
- **Exponential Backoff**: 2s → 4s → 8s → 16s → 30s
- **Auto-Resubscribe**: Seamless tick stream recovery

---

## 🎲 Trading Strategies (DETAILED)

Titan Pro uses a **multi-strategy portfolio** approach where THREE independent strategies compete for two simultaneous position slots. The system uses GPU optimization to find the best parameter combination for each strategy.

---

### 1️⃣ SCALPER (RSI Mean Reversion)

**Philosophy**: Exploit overbought/oversold extremes with quick reversals.

#### Entry Rules 📊

**BUY Conditions**:
```python
1. RSI crosses ABOVE oversold threshold (default: 30)
   - Previous RSI <= oversold_level
   - Current RSI > oversold_level
2. Time filter: 7 AM - 8 PM (UTC)
3. Volatility filter: ATR between 2.5 and 500 pips
4. Less than 2 active positions
```

**SELL Conditions**:
```python
1. RSI crosses BELOW overbought threshold (default: 70)
   - Previous RSI >= overbought_level
   - Current RSI < overbought_level
2. Same time and volatility filters as BUY
```

#### Exit Rules 🎯

**Take Profit**:
```
TP Distance = ATR × TP_Multiplier × 0.10
Default TP_Multiplier: 3.0
Example: ATR=50 pips → TP = 50 × 3.0 × 0.10 = 15 pips
```

**Stop Loss**:
```
SL Distance = ATR × SL_Multiplier × 0.10
Default SL_Multiplier: 2.0
Example: ATR=50 pips → SL = 50 × 2.0 × 0.10 = 10 pips
```

#### Parameters Optimized 🔧
| Parameter | Range | Purpose |
|-----------|-------|---------|
| RSI Period | 5-14 | Sensitivity of RSI indicator |
| Oversold | 20-40 | BUY trigger threshold |
| Overbought | 60-80 | SELL trigger threshold |
| TP Multiplier | 1.5-5.0 | Profit target (ATR multiple) |
| SL Multiplier | 1.0-3.0 | Stop loss (ATR multiple) |

#### Best For 🎯
- Ranging/sideways markets
- High volatility synthetic indices (R_75, R_100)
- Quick scalps (5-15 minute trades)

---

### 2️⃣ BREAKOUT (Bollinger Band Squeeze + Momentum)

**Philosophy**: Capture explosive moves when price breaks out of consolidation.

#### Entry Rules 📊

**BUY Conditions**:
```python
1. Bollinger Band Squeeze detected:
   - Band Width = (Upper BB - Lower BB) × 10
   - Width <= Max_Width threshold (default: 500 pips)

2. Strong bullish candle:
   - Close > Upper Bollinger Band
   - Candle body >= 50% of total range
   - Close > Open (bullish candle)

3. Momentum confirmation:
   - RSI(14) > 55 (bullish momentum)
   - Close > EMA(100) (above trend)

4. Time & volatility filters (same as Scalper)
```

**SELL Conditions**:
```python
1. Bollinger Band Squeeze detected (same as BUY)

2. Strong bearish candle:
   - Close < Lower Bollinger Band
   - Candle body >= 50% of total range
   - Close < Open (bearish candle)

3. Momentum confirmation:
   - RSI(14) < 45 (bearish momentum)
   - Close < EMA(100) (below trend)
```

#### Exit Rules 🎯

**Take Profit**:
```
TP Distance = ATR × TP_Multiplier × 0.10
Default TP_Multiplier: 5.0 (wider than Scalper)
Example: ATR=50 pips → TP = 50 × 5.0 × 0.10 = 25 pips
```

**Stop Loss**:
```
SL Distance = ATR × SL_Multiplier × 0.10
Default SL_Multiplier: 2.0
Example: ATR=50 pips → SL = 50 × 2.0 × 0.10 = 10 pips
```

#### Parameters Optimized 🔧
| Parameter | Range | Purpose |
|-----------|-------|---------|
| BB Period | 10-30 | Bollinger Band lookback |
| BB Deviation | 1.5-2.5 | Standard deviations for bands |
| Max Width | 200-1000 pips | Squeeze detection threshold |
| TP Multiplier | 2.0-10.0 | Profit target (larger moves) |
| SL Multiplier | 1.0-3.0 | Stop loss |

#### Best For 🎯
- Trend initiation
- News events / high volatility
- Breakout from consolidation

---

### 3️⃣ PULLBACK (EMA Trend Following)

**Philosophy**: Enter on retracements in the direction of the major trend.

#### Entry Rules 📊

**BUY Conditions**:
```python
1. Uptrend confirmed:
   - Fast EMA (default: 34) > Slow EMA (default: 144)

2. Pullback detected:
   - RSI(14) < RSI_Trigger (default: 40)
   - Price retraced but trend intact

3. Time & volatility filters (same as others)
```

**SELL Conditions**:
```python
1. Downtrend confirmed:
   - Fast EMA < Slow EMA

2. Pullback detected:
   - RSI(14) > (100 - RSI_Trigger)
   - Default: RSI > 60

3. Same filters as BUY
```

#### Exit Rules 🎯

**Take Profit**:
```
TP Distance = ATR × TP_Multiplier × 0.10
Default TP_Multiplier: 4.0
Example: ATR=50 pips → TP = 50 × 4.0 × 0.10 = 20 pips
```

**Stop Loss**:
```
SL Distance = ATR × SL_Multiplier × 0.10
Default SL_Multiplier: 2.0
Example: ATR=50 pips → SL = 50 × 2.0 × 0.10 = 10 pips
```

#### Parameters Optimized 🔧
| Parameter | Range | Purpose |
|-----------|-------|---------|
| Fast EMA | 20-50 | Short-term trend |
| Slow EMA | 100-200 | Long-term trend |
| RSI Trigger | 30-50 | Pullback detection level |
| TP Multiplier | 2.0-6.0 | Profit target |
| SL Multiplier | 1.0-3.0 | Stop loss |

#### Best For 🎯
- Strong trending markets
- Forex pairs (EUR/USD, XAU/USD)
- Continuation moves

---

## 🎯 Strategy Priority System

When multiple strategies trigger simultaneously, priority is:

```
1st Priority: SCALPER
2nd Priority: PULLBACK  
3rd Priority: BREAKOUT
```

**Rationale**: Scalper has highest win rate, Pullback has best risk/reward, Breakout is most volatile.

**Position Slots**: Maximum 2 concurrent positions (prevents overexposure).

---

## 🛡️ Risk Management System

### Position Sizing Formula
```python
position_size = (working_capital × risk_per_trade) / (stop_loss_distance × 10)

Example:
- Working Capital: $50
- Risk per Trade: 2% = $1.00
- SL Distance: 10 pips
- Position Size = ($50 × 0.02) / (10 × 10) = $1.00 / 100 = 0.01 lots
```

### Drawdown Contingencies

**Training Phase (15% DD)**:
- Purpose: Find only ultra-robust parameters
- Action if hit: Parameter combo rejected immediately
- Result: Only conservative strategies pass

**Validation Phase (20% DD)**:
- Purpose: Stress-test in adverse market
- Action if hit: Parameter combo rejected
- Result: Ensures no overfitting

**Live Trading (12% DD)**:
- Purpose: Protect real capital
- Action if hit: **STOP ALL TRADING**
- Recovery: Manual review required

### Daily Stops

**Daily Profit Goal** (Default: 5% of working capital):
```
Action: PAUSE trading for rest of the day
Reason: Prevent giving back gains
```

**Max Daily Loss** (Default: 5% of working capital):
```
Action: STOP trading for rest of the day
Reason: Prevent snowballing losses
```

**Consecutive Losses** (3 in a row):
```
Action: PAUSE for 1 hour
Reason: Possible adverse market conditions
```

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│                    LAUNCHER.PY                         │
│  • Fetch Deriv Balance                                 │
│  • Select Working Capital                              │
│  • Configure Risk Parameters                           │
│  • Download Historical Data (3 months)                 │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│                 TITAN_HYBRID.PY                        │
│                                                        │
│  ┌──────────────────────────────────────────────┐    │
│  │         GPU ENGINE (OpenCL)                  │    │
│  │  ┌────────────────────────────────────┐      │    │
│  │  │  Phase 1: TRAINING (15% DD)        │      │    │
│  │  │  • Test 100k combinations          │      │    │
│  │  │  • Find best on 70% of data        │      │    │
│  │  └────────────────────────────────────┘      │    │
│  │  ┌────────────────────────────────────┐      │    │
│  │  │  Phase 2: VALIDATION (20% DD)      │      │    │
│  │  │  • Test best on remaining 30%      │      │    │
│  │  │  • Reject if overfitted            │      │    │
│  │  └────────────────────────────────────┘      │    │
│  └──────────────────────────────────────────────┘    │
│                     │                                  │
│                     ▼                                  │
│  ┌──────────────────────────────────────────────┐    │
│  │      CPU ENGINE (Live Trading)               │    │
│  │  • Execute with Phase 3 params (12% DD)      │    │
│  │  • <1ms latency per candle                   │    │
│  │  • Track P&L, DD, Win Rate                   │    │
│  └──────────────────────────────────────────────┘    │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│               DERIV_CLIENT.PY                          │
│  • WebSocket connection to Deriv API                   │
│  • Ping keepalive (30s)                                │
│  • Auto-reconnect with backoff                         │
│  • Real-time tick streaming                            │
└────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

### Launcher Options

**1. Market Selection**:
- Synthetic: R_75, R_100, R_25, R_50
- Forex: EUR/USD, USD/JPY, XAU/USD, GBP/USD

**2. Timeframe**:
- M1, M5, M15 (recommended), M30, H1

**3. Risk Per Trade**:
- Range: 0.1% - 10%
- Default: 2%

**4. Daily Profit Goal**:
- Dollar amount (e.g., $50)
- Target: 5% of working capital

**5. Max Daily Loss**:
- Dollar amount (e.g., $25)
- Limit: 5% of working capital

**6. Working Capital**:
- Enter dollar amount: `50`
- Or percentage: `50%`, `100%`

### Advanced Parameters

Edit `titan_hybrid.py` to customize:

```python
# Optimization
OPTIMIZATION_INTERVAL = 100  # Re-optimize every 100 candles
HISTORY_SIZE = 8640          # Keep 90 days of M15 data

# Walk-Forward
WALK_FORWARD_TRAIN_SIZE = 0.7  # 70% training
WALK_FORWARD_TEST_SIZE = 0.3   # 30% validation
```

---

## 📊 Performance Metrics

### Expected Performance
- **Win Rate**: 55-65% (after optimization)
- **Average RR**: 1.5:1 to 2.5:1
- **Max Drawdown**: <12% (live), <20% (validation)
- **Daily Volatility**: 3-7% of capital

### Optimization Speed
- **100k Combinations**: ~2-3 minutes
- **Dual GPU**: 50% faster than single GPU
- **Re-calibration**: Weekly or every 100 candles

---

## 📝 License

MIT License - Open Source

---

## 🤝 Contributing

Pull requests welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## ⚠️ Disclaimer

**Trading involves substantial risk**. Past performance does not guarantee future results. Only trade with capital you can afford to lose. This bot is provided "as-is" without warranty.

---

## 📧 Contact

- **Author**: Lucas Valério
- **GitHub**: [@LucassVal](https://github.com/LucassVal)
- **Project**: [TitanFusion-cBot](https://github.com/LucassVal/TitanFusion-cBot)

---

**⚡ Titan Pro - Precision. Power. Profit.**
