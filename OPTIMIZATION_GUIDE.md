# 🧪 Optimization Guide & Presets

This document provides the recommended configuration ranges for optimizing **TitanFusion v2.5** on **XAUUSD (Gold)** using the **H1 Timeframe**.

These ranges are calibrated for a small account balance (e.g., $50 - $100) aiming for high growth (5-10% daily target).

---

## 🔒 Part 1: Fixed Parameters (Do Not Optimize)

**Important:** To save CPU time and avoid overfitting, keep these parameters **FIXED** (unchecked in the Optimization tab).

| Group | Parameter | Fixed Value | Reason |
| :--- | :--- | :--- | :--- |
| **Money** | `Use Auto-Compound` | **True** | Essential for small account growth. |
| **Money** | `Enable Profit Shield` | **True** | Secures daily gains. |
| **Exits** | `Enable Trailing SAR` | **True** | Gold requires dynamic stops. |
| **Exits** | `Enable Partial TP` | **True** | Banks profit early to reduce risk. |
| **Visual** | `Show Text Info` | **FALSE** | ⚠️ **CRITICAL:** Must be FALSE to speed up optimization by 300%. |
| **Visual** | `Enable H1 Trend Filter` | **True** | We only trade with the H1 trend. |
| **Fitness** | `Min Trades/Month` | **5** | Filters out inactive settings. |
| **Weights** | `All Weights` | **Default** | Profit (1.0), Drawdown (0.5), etc. |

---

## 🎛️ Part 2: Optimization Ranges

Copy these values into the **Start**, **Stop**, and **Step** columns in cTrader.

### 💰 Risk & Management
| Parameter | Start | Stop | Step |
| :--- | :--- | :--- | :--- |
| `Risk % Per Trade` | 1.0 | 4.0 | 1.0 |
| `Max Daily Drawdown` | 15 | 30 | 5 |
| `Daily Target %` | 5 | 15 | 5 |

### 🏃 Smart Exits & Filters
| Parameter | Start | Stop | Step |
| :--- | :--- | :--- | :--- |
| `SAR Min AF` | 0.01 | 0.03 | 0.01 |
| `SAR Max AF` | 0.1 | 0.3 | 0.1 |
| `Partial Trigger (ATR)` | 0.5 | 1.5 | 0.5 |
| `Min Volatility (ATR)` | 2.0 | 4.0 | 1.0 |
| `Max Spread` | 2.5 | 4.5 | 1.0 |
| `Max Volatility (Chaos)`| 40 | 70 | 10 |
| `Flat Market Pips` | 1.0 | 3.0 | 0.5 |

### ⚡ Strategy A: Scalper
| Parameter | Start | Stop | Step |
| :--- | :--- | :--- | :--- |
| `RSI Period` | 10 | 16 | 2 |
| `Oversold Level` | 20 | 30 | 5 |
| `Overbought Level` | 70 | 80 | 5 |
| `Scalper TP (ATR)` | 2.0 | 4.0 | 1.0 |
| `Scalper SL (ATR)` | 1.0 | 2.0 | 0.5 |

### 💥 Strategy B: Breakout
| Parameter | Start | Stop | Step |
| :--- | :--- | :--- | :--- |
| `BB Period` | 18 | 22 | 2 |
| `BB Deviation` | 1.8 | 2.4 | 0.2 |
| `Max Band Width` | 40 | 60 | 10 |
| `Min Body Ratio` | 0.5 | 0.7 | 0.1 |
| `Breakout TP (ATR)` | 3.0 | 6.0 | 1.0 |
| `Breakout SL (ATR)` | 1.0 | 2.0 | 0.5 |

### 🌊 Strategy C: Pullback
| Parameter | Start | Stop | Step |
| :--- | :--- | :--- | :--- |
| `Trend EMA Fast` | 30 | 60 | 10 |
| `Trend EMA Slow` | 150 | 250 | 50 |
| `Pullback RSI Trigger` | 40 | 50 | 5 |
| `Pullback TP (ATR)` | 2.0 | 4.0 | 1.0 |
| `Pullback SL (ATR)` | 1.5 | 2.5 | 0.5 |

---

## 🛠️ How to Test Strategies Individually (Modular Testing)

To find the best parameters without noise, it is highly recommended to optimize one strategy at a time.

### Step 1: Isolate Strategy A (Scalper)
1.  Go to **Parameters**.
2.  Set `Enable Scalper?` = **Yes**.
3.  Set `Enable Breakout?` = **No**.
4.  Set `Enable Pullback?` = **No**.
5.  **Run Optimization** selecting only the "Scalper" ranges (Table A above).
6.  Apply the best settings found.

### Step 2: Isolate Strategy B (Breakout)
1.  Set `Enable Scalper?` = **No**.
2.  Set `Enable Breakout?` = **Yes**.
3.  Set `Enable Pullback?` = **No**.
4.  **Run Optimization** selecting only the "Breakout" ranges (Table B above).
5.  Apply the best settings found.

### Step 3: Isolate Strategy C (Pullback)
1.  Set `Enable Scalper?` = **No**.
2.  Set `Enable Breakout?` = **No**.
3.  Set `Enable Pullback?` = **Yes**.
4.  **Run Optimization** selecting only the "Pullback" ranges (Table C above).
5.  Apply the best settings found.

### Final Step: The "Fusion" Test
1.  Set **ALL** Strategies to **Yes**.
2.  Run a **Backtest** (not Optimization) using the combined best parameters from steps 1, 2, and 3.
3.  Check if the Drawdown remains acceptable when all strategies run together.
