# TitanFusion cBot (Open Source)

[![Wiki](https://img.shields.io/badge/Documentation-Wiki-blue?style=for-the-badge&logo=read-the-docs)](../../wiki)
[![Platform](https://img.shields.io/badge/Platform-cTrader-green?style=for-the-badge)](https://ctrader.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

Hybrid Trading Algorithm for cTrader (cAlgo)
Optimized for XAUUSD (Gold) - H1 Timeframe

---

## Our Philosophy: Trading for Everyone

Welcome to the TitanFusion Project.

This repository aims to be more than just a collection of code; we are building a welcoming and inclusive community for algorithmic trading enthusiasts.

We believe that algorithmic trading shouldn't be restricted to hedge funds or math PhDs. Whether you are a seasoned C# developer or a trader just starting to explore automation, you are welcome here.

- We are all students: The market humbles everyone. We treat every idea with respect.
- Collaboration over Competition: We share knowledge freely to beat the market, not each other.
- Enthusiast Driven: This project is led by passion, not by a corporate agenda.

---

## Important Disclaimer

I am a financial market enthusiast, not a professional programmer.

This code is the result of my personal studies and testing. It reflects logic that has worked for my specific setup, but it may contain errors or inefficiencies.

- Do NOT use real money without extensive testing on a DEMO account.
- The code is provided "as is", without any warranty.
- I invite you to fork, fix, and improve this bot. The goal is to learn together.

---

## Strategy Overview (Fusion v2.5)

TitanFusion combines three classic strategies, protected by a "Chaos Guard" volatility filter.

### 1. Scalper (RSI)
Seeks mean reversion opportunities. It enters trades when the RSI indicates overbought or oversold conditions, confirming the entry only after the candle closes to avoid false signals.

### 2. Breakout (Bollinger Bands)
Capitalizes on volatility. It monitors for "squeezes" (low volatility) and triggers an entry when the price breaks out with momentum and strong candle body structure.

### 3. Pullback (Trend Following)
Respects the macro trend (H1). It uses Exponential Moving Averages (EMAs) to determine direction and buys the dips when RSI indicates a temporary correction.

---

## Key Features

- **Chaos Guard:** Automatically pauses trading if market volatility (ATR) exceeds safe levels (e.g., during war news or economic releases).
- **Auto-Compound:** Built-in money management that adjusts trade size based on account equity.
- **Timezone Lock:** Hardcoded to operate strictly during high-volume sessions (London & New York overlap) to avoid high spreads.
- **Optimization Ready:** Includes a custom fitness function that prioritizes a high Sharpe Ratio and low Drawdown.

---

## Installation Guide

1. Download the `.cs` source code file from this repository.
2. Open **cTrader Desktop**.
3. Navigate to the **Automate** tab.
4. Click on **New cBot**.
5. Paste the TitanFusion code into the editor and click **Build**.
6. Add an instance to an **XAUUSD (Gold)** chart on the **H1** timeframe.

> 📚 **Need detailed instructions?** [Click here to read the full Wiki](../../wiki)

---

## Join the Community & Contribute

We strongly encourage you to participate! You don't need to be an expert coder to help.

- Have an idea? Open a **Discussion** tab to chat about strategy improvements.
- Found a bug? Open an **Issue** so we can fix it.
- Optimized parameters? Share your `.cbotset` or backtest results with us.

Let's democratize algorithmic trading, one line of code at a time.
