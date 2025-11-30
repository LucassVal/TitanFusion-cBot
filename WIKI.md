# 🚀 Titan Pro - Hybrid GPU Trading System (Wiki)

## 📚 Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Trading Strategies](#trading-strategies)
5. [System Architecture](#system-architecture)
6. [Troubleshooting](#troubleshooting)

---

## 1. Introduction <a name="introduction"></a>
**Titan Pro** is a high-performance algorithmic trading system designed for **Deriv (Synthetic Indices)** and **Dukascopy (Forex/Metals)**. It utilizes a **Hybrid Architecture**:
*   **CPU Engine**: Handles live data processing, indicator calculation, and trade execution (<1ms latency).
*   **GPU Engine (OpenCL)**: Runs in the background, performing **Walk-Forward Optimization** on thousands of parameter combinations to adapt to changing market conditions.

---

## 2. Installation <a name="installation"></a>

### Prerequisites
*   Windows 10/11
*   Python 3.12+ ([Download](https://www.python.org/downloads/))
*   Git (Optional, for updates)

### One-Line Installer (PowerShell)
The easiest way to install Titan Pro is using our automated installer. Open **PowerShell** as Administrator and run:

```powershell
irm https://raw.githubusercontent.com/LucassVal/TitanFusion-cBot/main/install.ps1 | iex
```

This command will:
1.  Download the latest version of Titan Pro.
2.  Create a `TitanPro` folder in your user directory.
3.  Create a desktop shortcut.
4.  Guide you through installing Python dependencies.

### Manual Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/LucassVal/TitanFusion-cBot.git
    ```
2.  Install dependencies:
    ```bash
    pip install pandas pandas_ta numpy pyopencl websockets requests
    ```
3.  Run the launcher:
    ```bash
    python "Titan pro/launcher.py"
    ```

---

## 3. Configuration <a name="configuration"></a>

### First Run
When you launch Titan Pro, you will be prompted to configure:

1.  **Market Selection**: Choose from Synthetic Indices (e.g., R_75) or Real Markets (e.g., XAUUSD).
2.  **Timeframe**: Recommended is **M15** (15 minutes).
3.  **Risk Management**:
    *   **Risk per Trade**: Percentage of balance to risk (Default: 2%).
    *   **Daily Profit Goal**: Target profit to stop trading for the day.
    *   **Max Daily Loss**: Maximum loss allowed before stopping.
    *   **Total Profit Target**: Overall goal for the bot.
4.  **API Token (Deriv Only)**:
    *   Go to [Deriv API Settings](https://app.deriv.com/account/api-token).
    *   Create a token with **Read** and **Trade** scopes.
    *   Paste it into the launcher when prompted. It will be saved securely.

---

## 4. Trading Strategies <a name="trading-strategies"></a>
Titan Pro employs a **Multi-Strategy Portfolio** approach. The GPU engine dynamically weights these strategies based on recent performance.

### 1. Scalper (RSI + Bollinger)
*   **Logic**: Identifies overbought/oversold conditions within a trend.
*   **Key Indicators**: RSI (Relative Strength Index), Bollinger Bands.
*   **Best For**: Ranging markets and minor corrections.

### 2. Breakout (Volatility)
*   **Logic**: Captures explosive moves when price breaks out of a consolidation range.
*   **Key Indicators**: ATR (Average True Range), Donchian Channels (implied).
*   **Best For**: Trending markets and high volatility events.

### 3. Pullback (Trend Following)
*   **Logic**: Enters trades on retracements in the direction of the main trend.
*   **Key Indicators**: EMA (Exponential Moving Average) Crossovers.
*   **Best For**: Strong, sustained trends.

---

## 5. System Architecture <a name="system-architecture"></a>

### Hybrid Engine
*   **Live Loop (`titan_hybrid.py`)**: 
    *   Receives tick data via WebSocket.
    *   Aggregates ticks into candles (M1 -> M15).
    *   Executes trades based on optimized parameters.
*   **Optimizer (`titan_portfolio.cl`)**:
    *   Written in **OpenCL** for massive parallelism.
    *   Runs on **NVIDIA** and **Intel** GPUs simultaneously.
    *   Tests **100,000+** parameter combinations every week (or set interval).
    *   Uses **Walk-Forward Validation** to prevent overfitting.

### Data Management
*   **Dukascopy**: Downloads high-quality historical tick data for Forex/Metals.
*   **Deriv**: Downloads historical candle data for Synthetic Indices.
*   **Caching**: Data is cached locally (`.csv`) and auto-updated if older than 7 days.

---

## 6. Troubleshooting <a name="troubleshooting"></a>

### "API Token not set"
*   Run `launcher.py` again and ensure you enter a valid Deriv API token.
*   Check `titan_config.json` in the `Titan pro` folder.

### "No module named..."
*   You are missing Python libraries. Run:
    ```bash
    pip install pandas pandas_ta numpy pyopencl websockets requests
    ```

### Launcher closes immediately
*   The latest version has a pause on exit. Update your system using the installer command or option `[0]` in the launcher.

### "OpenCL Device Not Found"
*   Ensure you have GPU drivers installed (NVIDIA CUDA or Intel OpenCL Runtime).
*   The system will fallback to CPU if no GPU is found (slower optimization).

---
*Built with ❤️ by Lucas Valério & Antigravity*
