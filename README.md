# 🌌 Titan Fusion Quantum (Antigravity v3)

> **The Ultimate Hybrid AI Trading System**
>
> An institutional-grade trading engine that fuses **cTrader's** execution speed with **Python's** analytical power and **Gemini 2.0's** reasoning.

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/LucassVal/TitanFusion-cBot/releases)
[![Engine](https://img.shields.io/badge/engine-Antigravity_v3-purple.svg)](https://ai.google.dev)
[![Platform](https://img.shields.io/badge/platform-cTrader-orange.svg)](https://ctrader.com)

---

## 🎯 Architecture (The 4 Layers)

Titan Fusion isn't just a bot; it's a **Quantum Engine** that processes market data through 4 strict validation layers before taking any action.

### **L1: Technical & Structural Analysis**
*   **13 Elite Patterns:** Automatically detects *Liquidity Sweeps, Fair Value Gaps (FVG), CHoCH, Wyckoff Springs, Order Blocks*, and more.
*   **L1+ Structure (Local):** Python natively calculates *Trend Bias (EMA)*, *Volatility (Bollinger Squeeze)*, and *Key Levels* without spending API tokens.
*   **Scan Grid:** A visual matrix in the console showing the status of every pattern across M5, M15, M30, H1, and H4 timeframes.

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

### **L4: Management & Integrity**
*   **Portfolio Guard:** Prevents overexposure by limiting max 3 open positions per symbol.
*   **Risk Guard:** Hard-coded limits on SL/TP (e.g., Max SL 0.3% for Scalp) that override AI hallucinations.
*   **Supervisor:** A background process that validates the success of L1, L2, L3, and L4 every cycle.

---

## 🚀 Key Features (v1.1)

### 📊 **Visual "War Room" Log**
The terminal provides a military-grade dashboard of what the bot is thinking:
```text
  🔍 ANALYZING XAUUSD:
    [L1 DNA]       Digits: 2 | Pip: 0.01 | MinVol: 1
    [L1 Scan]      Pattern Status (13/13):
      - M5 : [S:🟢 F:🔴 C:__ W:__ ...]
    [L2 Sentiment] 🚨 DIVERGENCE: Crowd Extreme Buying -> Look for SELL
    [L3 Decision]  ⛔ WAIT (Scalp) | Conf: 60% | Reason: H4 trend conflict
    [L4 Mgmt]      Monitoring 2 orders | 🟢 In Profit
  [INTEGRITY] ✅ CYCLE VALIDATED (L1,L2,L3,L4 OK) | Latency: 0.85s
```

###  dziennik **Journaling System**
*   Every Approved Signal is saved to `Documents/TitanFusionAI/Journal/`.
*   You get a permanent text record of every trade decision for later review.

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
