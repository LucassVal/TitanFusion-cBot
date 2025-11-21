# TitanFusion cBot (Open Source)

![TitanFusion Banner](https://github.com/LucassVal/TitanFusion-cBot/assets/placeholder-logo.png)
[![Platform](https://img.shields.io/badge/Platform-cTrader-green?style=flat-square)](https://ctrader.com)
[![Version](https://img.shields.io/badge/Version-v3.1_Architect-blue?style=flat-square)](releases)
[![Asset](https://img.shields.io/badge/Asset-XAUUSD_(Gold)-gold?style=flat-square)](https://www.tradingview.com/symbols/XAUUSD/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](LICENSE)

**The "System Architect" Edition.**
A modular, open-source algorithmic trading system optimized for **XAUUSD (Gold)** on the **H1 Timeframe**.

> *This is not just a bot; it is a portfolio of strategies working in harmony.*

---

## 🌟 What is TitanFusion?

TitanFusion is a C# trading robot developed for the cTrader platform. Unlike simple bots that rely on a single indicator, TitanFusion operates as a **Multi-Strategy System**.

It combines three distinct market approaches (Scalping, Breakout, and Trend Following) and manages them using a sophisticated **Risk Controller** that adapts exposure based on how many strategies are active.

### The "Architect" Philosophy (v3.1)
Version 3.1 introduces the **Modular Strategy Controller**. This allows traders to:
1.  **Isolate & Test:** Run specifically just the "Scalper" or just the "Breakout" to verify performance.
2.  **Combine & Conquer:** Run all strategies together with **Risk Dampening** (automatic volume reduction) to prevent over-leverage.

---

## 🧠 Core Strategies

### 1. The Scalper (Mean Reversion)
* **Logic:** Prices rarely move in a straight line. This module exploits overbought/oversold conditions using RSI.
* **Entry:** RSI (14) crossing back from extremes (70/30).
* **Safety:** Uses a tight stop and only enters after candle close (`OnBar`) to avoid "falling knives".

### 2. The Breakout (Volatility)
* **Logic:** Capitalizes on volatility explosions after periods of calm (Squeeze).
* **Entry:** Price closes outside Bollinger Bands with a strong candle body.
* **Filter:** Checks `BandWidth` to ensure the market was consolidated before the explosion.

### 3. The Pullback (Trend Following)
* **Logic:** "The Trend is your friend". Buys dips in an uptrend and sells rallies in a downtrend.
* **Entry:** * Trend defined by Fast/Slow EMAs (34/144).
    * Triggered when RSI dips into a "value zone" (e.g., 40-45) during a trend.

---

## 🛡️ Advanced Protection Systems

### 🌪️ Chaos Guard (Volatility Circuit Breaker)
Before every trade, the bot checks market violence using ATR (Average True Range).
* **If ATR > Max Limit (120 pips):** The market is in "News/Panic Mode". The bot **PAUSES** instantly to protect capital.

### ⚖️ Smart Risk Dampening (v3.1 Exclusive)
The bot automatically adjusts position sizing based on the active mode:
* **Single Strategy Mode:** Uses 100% of `RiskPerTrade`.
* **All Strategies Mode:** Automatically reduces volume by **40%** to allow multiple positions without blowing up the margin.

### 🔒 Timezone Lock & H1 Trend Filter
* **Hardcoded Hours:** Trades only during liquid sessions (London/NY Overlap: 07:00 - 20:00 UTC).
* **Trend Filter:** Forces the Scalper and Breakout to respect the H1 Macro Trend (optional but recommended).

---

## 🎮 Operation Modes (New in v3.1)

You can now select the `Operation Mode` in the parameters:

| Mode | Description | Use Case |
| :--- | :--- | :--- |
| **All (Default)** | Runs Scalper + Breakout + Pullback. | **Live Trading.** Uses Risk Dampening logic. |
| **ScalperOnly** | Runs only RSI logic. | **Optimization:** Tune RSI period/levels. |
| **BreakoutOnly** | Runs only BB logic. | **Optimization:** Tune Deviation/Squeeze. |
| **PullbackOnly** | Runs only Trend logic. | **Optimization:** Tune EMAs. |
| **Combinations** | e.g., `ScalperBreakout`. | **Testing:** Checking correlation between pairs. |

---

## ⚙️ Installation & Setup

### Prerequisites
* **Platform:** cTrader Desktop (v4.8+ recommended).
* **Account:** Hedging Account (Required for multi-strategy).
* **Symbol:** XAUUSD (Gold).
* **Timeframe:** H1 (1 Hour).

### How to Install
1.  Download the `TitanFusion_v3.1.cs` file from [Releases](../../releases).
2.  Open cTrader and go to the **Automate** tab.
3.  Click **New cBot**, delete the sample code, and paste the TitanFusion code.
4.  Click **Build**.
5.  Add to an **XAUUSD H1** chart.

---

## 📊 Default Parameters (Gold Optimized)

The bot comes pre-configured with settings optimized for Gold volatility:

* **Risk Per Trade:** 1.5% (Conservative start).
* **Min Volatility:** 15 pips (Avoids dead markets).
* **Max Volatility:** 120 pips (Avoids non-farm payroll spikes).
* **Max Spread:** 8.0 pips (Gold standard).

> **Note:** Always optimize parameters for your specific broker's data feed using the "ScalperOnly", "BreakoutOnly", etc., modes separately before running "All".

---

## 🤝 Disclaimer & Community

**TitanFusion is an enthusiast project.** I am not a financial advisor. This code is shared for educational purposes.

* **Risk Warning:** Trading Gold involves significant risk. Never trade with money you cannot afford to lose.
* **No Warranty:** The software is provided "as is".
* **Community:** Found a bug? Have an idea? Open an [Issue](../../issues) or join the [Discussion](../../discussions).

**Let's democratize algorithmic trading.** 🚀
