# 📚 TITAN PRO - COMPLETE WIKI

**Comprehensive Technical Documentation for Advanced Multi-Strategy GPU Trading System**

---

## Table of Contents
1. [Algorithm Deep Dive](#1-algorithm-deep-dive)
2. [Trading Strategies Explained](#2-trading-strategies-explained)
3. [GPU Optimization Engine](#3-gpu-optimization-engine)
4. [Risk Management & Contingencies](#4-risk-management--contingencies)
5. [System Components](#5-system-components)
6. [Configuration Guide](#6-configuration-guide)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Algorithm Deep Dive

### 1.1 Core Trading Loop (OpenCL Kernel v2.1)

The system runs a **portfolio simulation** for each parameter combination:

```c
for each candle (i = 1 to num_candles):
    1. Update Indicators:
       - RSI (multiple periods)
       - Bollinger Bands
       - EMAs (Fast + Slow)
       - ADX (Trend Strength)
       - ATR (Volatility)
    
    2. Check Exits (Existing Positions):
       - Hit Stop Loss? → Close with loss
       - Hit Take Profit? → Close with profit
       - Update Balance, Drawdown, Win Count
       - Track MFE (Max Favorable Excursion) and MAE (Max Adverse Excursion)
    
    3. Check Drawdown:
       - If DD >= Threshold → KILL this parameter combo
       - Threshold varies by phase (25%/30%/12%)
    
    4. Check Entries (If slots available):
       - Evaluate Scalper signals (RSI + ADX + ATR)
       - Evaluate Pullback signals (EMA + RSI + ADX)
       - Evaluate Breakout signals (BB + RSI + EMA)
       - Take FIRST valid signal (priority order)
    
    5. Record Results:
       - Net Profit, Total Trades, Wins, Max DD
       - Total MFE, Total MAE (for efficiency scoring)
```

### 1.2 Indicator Calculations

#### ADX (Average Directional Index)
Added in v2.1 to filter weak trends.
```c
TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
+DM = (high - prev_high) > (prev_low - low) ? max(high - prev_high, 0) : 0
-DM = (prev_low - low) > (high - prev_high) ? max(prev_low - low, 0) : 0

Smoothed TR, +DM, -DM (Wilder's Smoothing)
DX = (|+DI - -DI| / (+DI + -DI)) * 100
ADX = Smoothed DX
```

#### RSI (Relative Strength Index)
```c
// Wilder's Smoothed RSI
avg_gain = (prev_avg_gain × (period-1) + current_gain) / period
avg_loss = (prev_avg_loss × (period-1) + current_loss) / period

RS = avg_gain / avg_loss
RSI = 100 - (100 / (1 + RS))
```

---

## 2. Trading Strategies Explained

### 2.1 SCALPER (RSI Mean Reversion)

#### Entry Logic (BUY)
```plaintext
Conditions (ALL must be true):
├─ RSI Crossover
│  └─ RSI < RSI_Buy_Threshold (Dynamic: 10-50)
├─ Trend Filter (ADX)
│  └─ ADX > ADX_Min (Dynamic: 0-50)
├─ Time Filter
│  └─ Hour >= Start_Hour AND Hour <= End_Hour
├─ Volatility Filter
│  ├─ ATR >= ATR_Min
│  └─ ATR <= ATR_Max
└─ Candle Body Filter
   └─ Body % >= Body_Min (Avoid Dojis)
```

**Optimized Parameters (15 Total)**:
- `rsi_period`, `rsi_buy`, `rsi_sell`
- `atr_min`, `atr_max`, `adx_min`
- `hour_start`, `hour_end`
- `tp`, `sl`, `body_min`

### 2.2 BREAKOUT (Bollinger Squeeze + Momentum)

#### Entry Logic (BUY)
```plaintext
Conditions (ALL must be true):
├─ Bollinger Squeeze
│  └─ Band Width <= Max_Width
├─ Strong Bullish Candle
│  ├─ Close > Upper BB
│  └─ Body % >= Body_Min
├─ Momentum Confirmation
│  ├─ RSI > RSI_Threshold
│  └─ Close > EMA(Period)
└─ Volatility Filter
   └─ ATR >= ATR_Min
```

**Optimized Parameters (12 Total)**:
- `bb_period`, `dev`, `min_w`, `max_w`
- `rsi_thresh`, `ema_period`
- `body_min`, `atr_min`
- `tp`, `sl`

### 2.3 PULLBACK (EMA Trend Following)

#### Entry Logic (BUY)
```plaintext
Conditions (ALL must be true):
├─ Trend Confirmation
│  └─ Fast EMA > Slow EMA
├─ Pullback Detection
│  └─ RSI < RSI_Buy_Threshold
├─ Trend Strength
│  └─ ADX > ADX_Min
└─ Volatility Filter
   └─ ATR >= ATR_Min
```

**Optimized Parameters (13 Total)**:
- `fast_ema`, `slow_ema`
- `rsi_buy`, `rsi_sell`
- `adx_min`, `atr_min`
- `tp`, `sl`

---

## 3. GPU Optimization Engine (Full Revolution v2.1)

### 3.1 Walk-Forward Validation

```
Historical Data (3 months = ~8640 M15 candles)
├─ Split 70/30
│  ├─ Training Set (70%)
│  └─ Test Set (30%)
│
Phase 1: TRAINING (25% DD Limit)
├─ Test 500,000 parameter combinations (Mega Grid)
├─ Each combo runs full simulation on training data
├─ Reject if DD >= 25% or other fitness criteria
├─ Select BEST combo by Ultra-Robust Fitness score
│
Phase 2: VALIDATION (30% DD Limit)
├─ Test ONLY the best combo on test data (unseen)
├─ Reject if DD >= 30%
├─ If passes → Use for live trading (12% DD limit)
└─ If fails → Return to defaults (manual review needed)
```

### 3.2 Ultra-Robust Fitness Function

**Purpose**: Prevent overfitting, reward consistency and optimal volume.

```python
Hard Filters (Instant Rejection):
├─ Drawdown >= 25% (Training)
├─ Trades < 10 (No statistical significance)
└─ Trades > 1000 (Overtrading/Scalping noise)

Soft Metrics:
├─ Net Profit × 3.0
├─ Sharpe Ratio × 100.0 (Reward consistency)
├─ Sortino Ratio × 80.0 (Penalize downside volatility)
├─ MFE Efficiency × 50.0 (Reward perfect entries)
└─ MAE Efficiency × 30.0 (Reward tight stops)

Bonuses:
├─ Volume Bonus: 50-200 trades → ×2.0 Score (Sweet spot)
└─ Target Bonus: 5-25% Daily Return → ×1.2 Score

Penalties:
├─ Win Rate > 80% → ×0.3 (Suspicious/Overfitting)
└─ Win Rate < 35% → ×0.6 (Too poor)
```

### 3.3 Parameter Search Space (40 Parameters)

**Total Combinations**: ~10^25 (Effectively Infinite)

| Strategy | Parameter | Range | Options |
|----------|-----------|-------|---------|
| **Scalper** | RSI Period | 3-21 | 8 |
| (15 Params) | RSI Buy/Sell | 10-50 / 50-90 | 9 x 9 |
| | ATR Min/Max | 1-50 / 10-500 | 9 x 8 |
| | ADX Min | 0-50 | 8 |
| | Hour Start/End | 0-9 / 15-23 | 4 x 4 |
| | TP/SL ATR | 0.5-10.0 | 10 x 8 |
| | Body Min | 0.3-0.9 | 7 |
| **Breakout** | BB Period/Dev | 5-50 / 0.5-3.5 | 8 x 7 |
| (12 Params) | Min/Max Width | 5-100 / 50-1000 | 7 x 7 |
| | RSI/EMA | 40-70 / 50-300 | 7 x 6 |
| | Body/ATR Min | 0.3-0.7 / 1-50 | 3 x 5 |
| | TP/SL ATR | 1.0-15.0 | 7 x 6 |
| **Pullback** | Fast/Slow EMA | 5-100 / 50-300 | 7 x 7 |
| (13 Params) | RSI Buy/Sell | 20-60 / 40-80 | 9 x 9 |
| | ADX/ATR Min | 10-50 / 1-50 | 7 x 6 |
| | TP/SL ATR | 1.0-12.0 | 7 x 7 |

**Sampling Strategy**: Random sampling of **500,000 combinations** per optimization cycle. This provides a dense coverage of the most likely profitable areas of the search space.

---

## 4. Risk Management & Contingencies

### 4.1 Position Sizing

```
Formula:
position_size = (working_capital × risk_per_trade) / (SL_distance × 10)

Example 1 (Conservative):
- Working Capital: $50
- Risk per Trade: 1% = $0.50
- SL Distance: 10 pips
- Position Size = ($50 × 0.01) / (10 × 10) = 0.005 lots

Example 2 (Aggressive):
- Working Capital: $1000
- Risk per Trade: 4% = $40
- SL Distance: 15 pips
- Position Size = ($1000 × 0.04) / (15 × 10) = 0.267 lots
```

### 4.2 Drawdown Contingencies

#### Level 1: Training DD (15%)
**Trigger**: Cumulative loss reaches 15% of initial balance during optimization.

```
Action: Reject parameter combination immediately
Reason: Parameters too risky for our target
Effect: Only conservative params pass to validation
```

#### Level 2: Validation DD (20%)
**Trigger**: Best params from training hit 20% DD on test data.

```
Action: Reject entire optimization run
Reason: Params overfitted to training data
Effect: Return to DEFAULT_PARAMS, flag for manual review
Recommendation: Increase training data period
```

#### Level 3: Live DD (12%)
**Trigger**: Real trading balance drops 12% from peak equity.

```
Action: STOP ALL TRADING IMMEDIATELY
Notification: Console alert + potential email/webhook
Reason: Protect capital from catastrophic loss
Recovery: Manual review of trades, market conditions
         Re-run optimization with fresh data
         Consider reducing risk per trade
```

### 4.3 Daily Stop Mechanisms

#### Profit Goal Reached (+5%)
```
Trigger: daily_profit >= (working_capital × 0.05)
Example: $50 capital → Stop at +$2.50 profit

Action:
├─ Close any open positions at market
├─ Disable new entries for rest of session
├─ Update session stats
└─ Resume next day (or next session start)

Rationale: Lock in gains, prevent giving back profits
```

#### Max Loss Hit (-5%)
```
Trigger: daily_loss <= -(working_capital × 0.05)
Example: $50 capital → Stop at -$2.50 loss

Action:
├─ Close all open positions immediately
├─ Disable trading for rest of day
├─ Log trades for analysis
└─ Alert user of stop

Rationale: Prevent snowballing losses
```

#### Consecutive Losses (3x)
```
Trigger: 3 losing trades in a row

Action:
├─ PAUSE trading for 60 minutes
├─ Do NOT close existing positions
├─ Log market conditions
└─ Resume after cooldown

Rationale: May indicate adverse market shift
```

### 4.4 Connection Contingencies

#### Ping Timeout
```
Condition: No pong received within 40 seconds
Action:
├─ Attempt reconnection immediately
├─ Re-subscribe to ticks
└─ Resume state tracking
```

#### Reconnection Failure
```
Condition: 10 failed reconnect attempts
Action:
├─ Close all open positions (if possible)
├─ Log positions to file
├─ Display manual intervention message
└─ Require user restart

Reason: Prevent trading in blind (no data)
```
├── README.md                # Quick start guide
├── WIKI.md                  # This file
├── LICENSE                  # MIT License
└── .gitignore
```

### 5.2 Data Flow

```
User Input (launcher.py)
    ↓
Configuration → titan_hybrid globals
    ↓
Data Manager → Download/Cache historical data
    ↓
GPU Engine → Optimize 100k combinations
    ↓
Best Parameters → CPU Engine
    ↓
Deriv Client → Live tick stream
    ↓
CPU Engine → Process candles, execute strategies
    ↓
(Future) Trade Execution → Deriv API
```

---

## 6. Configuration Guide

### 6.1 Launcher Settings

**Market**: Choose synthetic (24/7) or forex (session-based)
- Synthetic: R_75, R_100 (high volatility, more signals)
- Forex: EUR/USD, XAU/USD (lower volatility, fewer but higher quality signals)

**Timeframe**: 
- M1: Too noisy, not recommended
- M5: Fast scalping (requires low latency)
- **M15: RECOMMENDED** (balance of signal quality and frequency)
- M30/H1: Swing trading (fewer signals, longer holds)

**Risk Per Trade**:
- 0.5-1%: Conservative (slow growth)
- **2-3%: RECOMMENDED** (balanced)
- 4-5%: Aggressive (higher DD risk)

**Daily Profit Goal**:
- Calculate: `working_capital × 0.05`
- Example: $100 capital → $5 daily goal

**Max Daily Loss**:
- Should match daily goal (symmetric risk)
- Example: $100 capital → $5 max loss

### 6.2 Advanced Settings (titan_hybrid.py)

```python
# Line 40-41: Optimization frequency
OPTIMIZATION_INTERVAL = 100  # Re-optimize every X candles
# Recommendation: 50-200 depending on market speed

# Line 42: Historical data retention
HISTORY_SIZE = 8640  # M15 candles (90 days)
# Recommendation: 4320-12960 (30-180 days)

# Line 45-46: Walk-Forward split
WALK_FORWARD_TRAIN_SIZE = 0.7  # 70% training
WALK_FORWARD_TEST_SIZE = 0.3   # 30% test
# Recommendation: Don't change unless you know what you're doing

# Line 48: Number of parameter combinations
num_samples = 100000  # In _generate_grid()
# Recommendation: 50k (faster) to 200k (more thorough)
```

---

## 7. Troubleshooting

### 7.1 "No valid parameters found in training!"

**Cause**: All 100,000 combinations hit death conditions

**Solutions**:
1. **Increase Training DD**:
   - Edit line 160: Change `0.15f` to `0.20f`
   - Allows slightly riskier params to pass

2. **Reduce Candle Count**:
   - Use less historical data (harder test)
   - Edit line 42: `HISTORY_SIZE = 4320` (60 days instead of 90)

3. **Check Symbol**:
   - R_75/R_100 are VERY volatile
   - Try R_50 or forex pairs first

### 7.2 "Connection closed" / Frequent Disconnects

**Cause**: ISP issues, Deriv API limits, or firewall

**Solutions**:
1. **Check Internet**: Stable connection required
2. **VPN/Proxy**: May interfere with WebSocket
3. **Firewall**: Allow Python through firewall
4. **Multiple Instances**: Deriv limits 6 connections per token

### 7.3 Trades Not Executing

**Cause**: Bot currently in MONITORING mode (no execution yet)

**Status**: Trade execution via Deriv API is planned but NOT implemented.

**Current Behavior**:
- System calculates signals
- Displays "BUY/SELL (Strategy)" messages
- Does NOT place actual trades

### 7.4 Low Win Rate (<45%)

**Possible Causes**:
1. **Overfitting**: Params worked in backtest, fail live
2. **Market Shift**: Conditions changed since optimization
3. **Slippage**: Real execution differs from backtest

**Solutions**:
- Re-run optimization with fresh data
- Reduce risk per trade temporarily
- Check if optimization was on wrong timeframe

### 7.5 GPU Not Detected

**Error**: "No GPU devices found"

**Solutions**:
1. **Install OpenCL**:
   - Intel: https://www.intel.com/content/www/us/en/developer/tools/opencl-sdk/overview.html
   - NVIDIA: Install CUDA toolkit

2. **Check Drivers**: Update GPU drivers

3. **Verify Installation**:
   ```python
   import pyopencl as cl
   print(cl.get_platforms())
   ```

---

## Appendix: Advanced Topics

### A. Kelly Criterion (Future Implementation)

Optimal position sizing formula:
```
Kelly % = (Win_Rate × Avg_Win - (1 - Win_Rate) × Avg_Loss) / Avg_Win

Example:
- Win Rate: 60%
- Avg Win: $10
- Avg Loss: $5
Kelly = (0.6 × 10 - 0.4 × 5) / 10 = 0.4 = 40%

Use HALF Kelly for safety: 20% per trade
```

### B. Correlati Strategic Weighting

Future feature: Dynamically weight strategies based on recent performance.

```
Weights = [Scalper_Score, Breakout_Score, Pullback_Score]
Normalize to sum = 1.0

Allocate working capital proportionally:
- Best performing gets 50%
- Medium gets 30%
- Worst gets 20%
```

---

**End of Wiki** | *Last Updated: 2025-12-01*
