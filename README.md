# 🌌 Titan Fusion Quantum (Antigravity v3)

> **The Ultimate Hybrid AI Trading System**
>
> An institutional-grade trading engine that fuses **cTrader's** execution speed with **Python's** analytical power and **Gemini 2.0's** reasoning.

[![Version](https://img.shields.io/badge/version-1.3.2-blue.svg)](https://github.com/LucassVal/TitanFusion-cBot/releases)
[![Engine](https://img.shields.io/badge/engine-Antigravity_v3-purple.svg)](https://ai.google.dev)
[![Platform](https://img.shields.io/badge/platform-cTrader-orange.svg)](https://ctrader.com)

---

## 🎯 Architecture (The 4 Layers)

Titan Fusion isn't just a bot; it's a **Quantum Engine** that processes market data through 4 strict validation layers before taking any action.

### **L1: Technical & Structural Analysis (The Quant Lab)**

This layer is the "Mathematical Backbone" of the system. Before any AI inference, Python locally executes a **High-Performance Quant Scan** calculating 10+ professional indicators to build a "Bio-Scan" of the asset.

*   **13 Elite Patterns:** Automatically detects *Liquidity Sweeps, Fair Value Gaps (FVG), CHoCH, Wyckoff Springs, Order Blocks*, and more.
*   **L1+ Structure (Local):** Python natively calculates *Trend Bias (EMA)*, *Volatility (Bollinger Squeeze)*, and *Key Levels*.
*   **Scan Grid:** A visual matrix in the console showing the status of every pattern across M5, M15, M30, H1, and H4 timeframes.

#### **The Quant Matrix: Indicator x Strategy Mapping**
We calculate 10+ specific indices. Each one serves a critical role in validating specific strategies:

| Indicator / Metric | Function | Fast Scalp (M5) | Day Scalp (M15) | Momentum (H1) | Swing (H4) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **EMA Triple (20/50/200)** | Trend Alignment | ❌ Ignore | ✅ Required | ✅ Strict | ✅ Strict |
| **MACD (12,26,9)** | Trend Momentum | ❌ Ignore | ❌ Ignore | ✅ Signal Line | ✅ Histogram |
| **RSI (14)** | Overbought/Sold | ✅ Reversion | ✅ Divergence | ❌ Ignore | ❌ Ignore |
| **Stochastics (14,3,3)** | Fast Timing | ✅ Trigger | ✅ Trigger | ❌ Ignore | ❌ Ignore |
| **Williams %R** | Exhaustion | ✅ Extreme | ❌ Ignore | ❌ Ignore | ✅ Reversal |
| **Bollinger Width** | Volatility Cycle | ✅ Squeeze | ✅ Expansion | ✅ Breakout | ❌ Ignore |
| **ATR (14)** | Real Volatility | ✅ Dynamic TP/SL | ✅ Dynamic TP/SL | ✅ Dynamic TP/SL | ✅ Dynamic TP/SL |
| **OBV (On Balance Vol)**| Accumulation | ❌ Ignore | ❌ Ignore | ✅ Flow Check | ✅ Confirmation|
| **VWAP** | Inst. Fair Value | ❌ Ignore | ✅ Support/Res | ✅ Trend Filter | ❌ Ignore |
| **Flow Score** | Proprietary Algo | ❌ Ignore | ❌ Ignore | ✅ REQUIRED | ✅ REQUIRED |

> **Note:** "Ignore" means the AI is instructed to downweight that metric for that specific mode, preventing noise (e.g., ignoring RSI in a strong Momentum trade).

### **L2: Market Sentiment (Contrarian)**
*   **Real-Time Broker Data:** Reads the "Crowd Sentiment" directly from cTrader.
*   **The 75/25 Rule:** 
    *   If Crowd Buy > 75% -> **BLOCKS BUYS** (Sentient: Overbought).
    *   If Crowd Buy < 25% -> **BLOCKS SELLS** (Sentient: Oversold).
*   **Divergence Detection:** Identifies when Price is falling but Sentiment is rising (Smart Money accumulation).

### **L3: Artificial Intelligence (The Brain)**
*   **Gemini 2.0 Flash:** Receives the pre-digested L1+L2 data.
*   **Prompt Engineering v3:** Uses a "Persona-based" prompt to act as an Institutional Trader.
*   **Decision:** Determines the Strategy (*Scalp, Momentum, Swing*) and Confidence level. Only trades if Confidence > 75%.

### **L4: Intelligent Order Supervisor (NEW in v1.3)**

The L4 layer is no longer passive monitoring—it's an **Active Position Manager**:

*   **Global Position View:** Monitors ALL open positions across ANY symbol.
*   **Auto-Actions (Tight % Limits):**
    *   `SET_SL`: Auto-adds emergency SL (0.3% from entry) when missing.
    *   `BREAKEVEN`: Moves SL to entry when profit > 0.15%.
    *   `SET_TP`: Adjusts TP to optimize R:R ratio.
*   **Safety Rule:** `ClosePosition` is **INTENTIONALLY BLOCKED** in code—the system can adjust but NEVER close.
*   **Integrity Check:** Validates L1, L2, L3, L4 every cycle.

---

## 🚀 Key Features (v1.3)

### 📊 **Visual "War Room" Log**
The terminal provides a military-grade dashboard of what the bot is thinking:
```text
  🔍 ANALYZING XAUUSD:
    [L1 DNA]       Digits: 2 | Pip: 0.01 | MinVol: 1
    [L1 Scan]      Pattern Status (13/13):
      - M5 : [S:🟢 F:🔴 C:__ W:__ ...]
    [L1+ Structure] Trend: STRONG_BULLISH 🚀 | Momentum: OVERBOUGHT ⚠️
    [L2 Sentiment] 🚨 DIVERGENCE: Crowd Extreme Buying -> Look for SELL
    
    [L4 ORDER SUPERVISOR] Analyzing 2 positions...
      [XAUUSD] Order #12345 | SELL | PnL: $-1.50 🔴
        Entry: 2650.00 | SL: 0.00000 | TP: 2640.00
        ⚠️ ALERT: NO SL! Auto-setting emergency SL at 2657.95 (0.3%)
    [L4] 📤 Sent 1 command to cBot
    
  [INTEGRITY] ✅ CYCLE VALIDATED (L1,L2,L3,L4 OK) | Latency: 2.54s
```

### 📓 **Journaling System**
*   Every Approved Signal is saved to `Documents/TitanFusionAI/Journal/`.
*   Permanent text record of every trade decision for later review.

### 📊 **Signal Validator (NEW in v1.3.1)**
An independent script that validates your trading signals:
*   Calculates **Win Rate** per strategy (FAST_SCALP, SCALP, MOMENTUM, SWING).
*   Generates **charts** (bar + pie) via matplotlib.
*   Compares predictions vs actual market data.

Run via launcher (Option 2) or: `python signal_validator.py`

```text
═══════════════════════════════════════════════════════════
  SIGNAL VALIDATION REPORT - 2025-12-28
═══════════════════════════════════════════════════════════
Strategy       | Signals | Wins | Losses | Win Rate
───────────────────────────────────────────────────────────
FAST_SCALP     |   24    |  18  |   6    |   75% ✅
SCALP          |    5    |   3  |   2    |   60% ⚠️
───────────────────────────────────────────────────────────
Overall Win Rate: 71.0%
═══════════════════════════════════════════════════════════
```

---

## ⚡ Quick Start

### 1. Requirements
*   **cTrader Desktop** (Windows)
*   **Python 3.11+**
*   **Gemini API Key** (Free Tier allowed)

### 2. Installation
1.  **Clone** this repo to your Desktop.
2.  **Install Python Deps:** `pip install pandas numpy requests`
3.  **Install cBot:** Double-click `TitanFusion_QuantumBot.algo` (or build source).
4.  **Configure API:** Open `quantum_brain.py` and paste your `AIza...` key in line 18.

### 3. Launch
*   Use the **TitanFusion_Launcher.bat** included in the folder.
*   Or use the Desktop Shortcut if created.

---

## 📊 Validation System (NEW in v1.3.2)

Complete trade tracking for performance analysis:

### Closed Positions Export
When a position closes, cBot exports to `closed_positions.json`:
*   **close_type**: `HIT_TP` | `HIT_SL` | `MANUAL` | `PROFIT_CLOSE` | `LOSS_CLOSE`
*   Entry price, close price, PnL, strategy, volume

### Rejected Signals Log
Signals blocked due to portfolio limits are tracked in `rejected_signals.json`:
*   Reason: `MAX_POSITIONS`, `LOW_CONFIDENCE`, `DUPLICATE`
*   Timestamp, symbol, direction

### Auto-Validation on Exit
When you stop the engine (Ctrl+C), it automatically runs the Signal Validator:
```
📊 GENERATING SESSION VALIDATION REPORT...
Strategy       | Signals | Wins | Losses | Win Rate
FAST_SCALP     |   24    |  18  |   6    |   75% ✅
```

---

## 🛡️ Risk Management
*   **Hard Cap SL:** The system will REJECT any AI signal suggesting a Stop Loss > 1.5% (Swing) or > 0.3% (Scalp).
*   **Breakeven:** Auto-moves SL to Entry after fixed profit targets.
*   **Trailing Stop:** Dynamic trailing based on volatility.

---

## 🤝 Contributing
Found a bug? Want to add a new Pattern?
1.  Fork it.
2.  Create your feature branch (`git checkout -b feature/NewPattern`).
3.  Commit your changes (`git commit -m 'Add Wyckoff Upthrust'`).
4.  Push to the branch (`git push origin feature/NewPattern`).
5.  Open a Pull Request.

---
> **Disclaimer:** Trading involves risk. Titan Fusion provides analysis, not financial advice. Use at your own risk.

**Built by Lucas Valério** | *Powered by Antigravity Engine* 🌌
