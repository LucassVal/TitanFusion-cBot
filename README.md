# TitanFusion cBot (Open Source)

http://googleusercontent.com/image_generation_content/0

[![Platform](https://img.shields.io/badge/Platform-cTrader-green?style=for-the-badge)](https://ctrader.com)
[![Version](https://img.shields.io/badge/Version-v3.3_Certified-blue?style=for-the-badge)](releases)
[![Asset](https://img.shields.io/badge/Asset-XAUUSD_(Gold)-gold?style=for-the-badge)](https://www.tradingview.com/symbols/XAUUSD/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)](LICENSE)

**The "System Architect" Edition.**
A modular, open-source algorithmic trading system optimized for **XAUUSD (Gold)** on the **H1 Timeframe**.

> *TitanFusion is not just a bot; it is a portfolio of strategies working in harmony with a central Risk Controller.*

---

## 🌟 Our Philosophy & Architecture

### The "Architect" Philosophy (v3.3)
This version allows for **Phase Testing** through its `Operation Mode` selector. It is built to ensure statistical accuracy by letting you isolate performance before combining strategies.

### 🛡️ Core Protection
* **ATR Dynamic Stops:** All Stop Loss and Take Profit levels are calculated dynamically based on **Average True Range (ATR)**, making the bot resilient to rapid changes in Gold volatility.
* **Chaos Guard:** Prevents trading during extreme market spikes (e.g., NFP) when ATR exceeds set limits.
* **Smart Risk Dampening:** Automatically reduces position volume by **40%** when running in `All` mode to prevent over-leverage.

---

## 🧠 Core Strategies

### 1. Scalper (Mean Reversion)
* **Logic:** RSI (14) crossing back from extremes (70/30).
* **Execution:** Designed for quick entries; relies on tight stop and only enters after candle close (`OnBar`).

### 2. Breakout (Volatility)
* **Logic:** Capitalizes on volatility explosions after periods of calm (Squeeze).
* **Filter:** Checks `BandWidth` and **Body Ratio** to confirm the break is genuine.

### 3. Pullback (Trend Following)
* **Logic:** Buys dips in an uptrend and sells rallies in a downtrend, aligned with the macro trend (EMA 34/144).

---

## 🎮 Operation Modes (Modular Testing)

You can select the `Operation Mode` in the parameters to control the bot's behavior:

| Mode | Description | Best Use Case |
| :--- | :--- | :--- |
| **All (Default)** | Runs Scalper + Breakout + Pullback. | **Live Trading.** Activates Risk Dampening. |
| **ScalperOnly** | Runs only RSI logic. | **Optimization:** Tune RSI period/levels. |
| **BreakoutOnly** | Runs only BB logic. | **Optimization:** Tune Deviation/Squeeze. |
| **PullbackOnly** | Runs only Trend logic. | **Optimization:** Tune EMAs. |
| **Combinations** | e.g., `ScalperBreakout`. | **Correlation Testing.** |

---

## ⚙️ Installation & Setup

### Prerequisites
* **Platform:** cTrader Desktop (v4.8+ recommended).
* **Symbol:** XAUUSD (Gold) on H1 Timeframe.

### Installation Steps
1.  **Download Code:** Get the `TitanFusion_v3.3.cs` file from [Releases](../../releases).
2.  **Learn How to Create a cBot:** If you are new to cTrader Automate, refer to the [Official cTrader Documentation](https://help.ctrader.com/ctrader-algo/documentation/cbots/create-a-cbot/).
3.  **Build:** Open cTrader, go to the **Automate** tab, paste the code, and click **Build**.
4.  Add to an **XAUUSD H1** chart.

### ❗ Critical Stability Note (v3.3 Fix)
* The **Partial TP** function is now protected against the `InvalidStopLossTakeProfit` error. The system verifies if the position still exists before attempting to move the Stop Loss.

---

## 🤝 Disclaimer & Community

**TitanFusion is an enthusiast project.** I am not a financial advisor.

* **Risk Warning:** Trading Gold involves significant risk. Never trade with money you cannot afford to lose.
* **Community:** Found a bug? Have an idea? Open an [Issue](../../issues) or join the [Discussion](../../discussions).

**Let's democratize algorithmic trading.** 🚀
