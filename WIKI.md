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

### 1.1 Core Trading Loop (OpenCL Kernel)

The system runs a **portfolio simulation** for each parameter combination:

```c
for each candle (i = 1 to num_candles):
    1. Update Indicators:
       - RSI (multiple periods)
       - Bollinger Bands
       - EMAs (Fast + Slow)
    
    2. Check Exits (Existing Positions):
       - Hit Stop Loss? → Close with loss
       - Hit Take Profit? → Close with profit
       - Update Balance, Drawdown, Win Count
    
    3. Check Drawdown:
       - If DD >= Threshold → KILL this parameter combo
       - Threshold varies by phase (15%/20%/12%)
    
    4. Check Entries (If slots available):
       - Evaluate Scalper signals
       - Evaluate Pullback signals
       - Evaluate Breakout signals
       - Take FIRST valid signal (priority order)
    
    5. Record Results:
       - Net Profit, Total Trades, Wins, Max DD
```

### 1.2 Indicator Calculations

#### RSI (Relative Strength Index)
```c
// Wilder's Smoothed RSI
avg_gain = (prev_avg_gain × (period-1) + current_gain) / period
avg_loss = (prev_avg_loss × (period-1) + current_loss) / period

RS = avg_gain / avg_loss
RSI = 100 - (100 / (1 + RS))
```

**Scalper**: Uses custom RSI period (5-14)  
**Breakout**: Uses fixed RSI(14) for momentum  
**Pullback**: Uses fixed RSI(14) for retracement

#### Bollinger Bands
```c
Middle Band = SMA(close, period)
Standard Deviation = sqrt(sum((close - SMA)²) / period)
Upper Band = SMA + (deviation × std)
Lower Band = SMA - (deviation × std)
Band Width = (Upper - Lower) × 10  // In pips
```

**Used by Breakout strategy** to detect squeeze.

#### EMA (Exponential Moving Average)
```c
multiplier = 2 / (period + 1)
EMA = (close × multiplier) + (prev_EMA × (1 - multiplier))
```

**Breakout**: EMA(100) for trend filter  
**Pullback**: Fast EMA (20-50) + Slow EMA (100-200)

#### ATR (Average True Range)
```c
True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))
ATR = Exponential average of True Range over 14 periods
```

**Used by ALL strategies** for:
- Stop Loss placement
- Take Profit placement
- Volatility filtering

---

## 2. Trading Strategies Explained

### 2.1 SCALPER (RSI Mean Reversion)

#### Entry Logic (BUY)
```plaintext
Conditions (ALL must be true):
├─ RSI Crossover
│  ├─ Previous RSI <= Oversold Threshold (e.g., 30)
│  └─ Current RSI > Oversold Threshold
├─ Time Filter
│  └─ Hour >= 7 AND Hour < 20 (UTC)
├─ Volatility Filter
│  ├─ ATR >= 2.5 pips
│  └─ ATR <= 500 pips
└─ Position Limit
   └─ Active Positions < 2
```

**Optimized Parameters**:
- `s_p1`: RSI Period (5-14)
- `s_p2`: Oversold Level (20-40)
- `s_p3`: Overbought Level (60-80)
- `s_p4`: TP ATR Multiplier (1.5-5.0)
- `s_p5`: SL ATR Multiplier (1.0-3.0)

#### Exit Logic
```plaintext
Take Profit:
├─ For BUY: Price >= Entry + (ATR × TP_Mult × 0.10)
└─ For SELL: Price <= Entry - (ATR × TP_Mult × 0.10)

Stop Loss:
├─ For BUY: Price <= Entry - (ATR × SL_Mult × 0.10)
└─ For SELL: Price >= Entry + (ATR × SL_Mult × 0.10)
```

#### When It Works Best
✅ **Ideal Conditions**:
- Range-bound markets
- High volatility synthetic indices (R_75, R_100)
- Oscillating price action

❌ **Poor Conditions**:
- Strong trends (gets whipsawed)
- Low volatility (too few signals)
- News events (extreme spikes)

---

### 2.2 BREAKOUT (Bollinger Squeeze + Momentum)

#### Entry Logic (BUY)
```plaintext
Conditions (ALL must be true):
├─ Bollinger Squeeze
│  ├─ Band Width = (Upper BB - Lower BB) × 10
│  └─ Width <= Max Width Threshold (e.g., 500 pips)
├─ Strong Bullish Candle
│  ├─ Close > Upper Bollinger Band
│  ├─ Candle Body >= 50% of Total Range
│  └─ Close > Open (bullish candle)
├─ Momentum Confirmation
│  ├─ RSI(14) > 55
│  └─ Close > EMA(100)
├─ Time Filter (same as Scalper)
└─ Volatility Filter (same as Scalper)
```

**Code Snippet (from kernel)**:
```c
float sma = bb_sum / bb_period;
float std = sqrt(variance);
float upper = sma + (deviation × std);
float lower = sma - (deviation × std);
float width = (upper - lower) × 10.0f;

if (width <= max_width) {  // Squeeze detected
    float body = abs(close - open);
    float total = high - low;
    
    if (body/total >= 0.5f) {  // Strong candle
        if (close > upper && rsi > 55 && close > ema) {
            // BUY signal confirmed
        }
    }
}
```

#### Exit Logic
Same as Scalper, but:
- **Wider TP**: Default 5.0× ATR (vs 3.0× for Scalper)
- **Same SL**: 2.0× ATR

#### When It Works Best
✅ **Ideal Conditions**:
- Consolidation followed by breakout
- News events / economic calendar
- Strong momentum

❌ **Poor Conditions**:
- Ranging markets (false breakouts)
- Low volume periods
- Choppy price action

---

### 2.3 PULLBACK (EMA Trend Following)

#### Entry Logic (BUY)
```plaintext
Conditions (ALL must be true):
├─ Trend Confirmation
│  └─ Fast EMA (e.g., 34) > Slow EMA (e.g., 144)
├─ Pullback Detection
│  └─ RSI(14) < RSI Trigger (e.g., 40)
├─ Time Filter (same as others)
└─ Volatility Filter (same as others)
```

**Why This Works**:
- Trend provides directional bias
- RSI pullback = temporary retracement
- Entry on "dip" in uptrend = better risk/reward

#### Exit Logic
Same as Scalper, but:
- **Moderate TP**: Default 4.0× ATR
- **Same SL**: 2.0× ATR

#### When It Works Best
✅ **Ideal Conditions**:
- Strong trending markets
- Forex pairs with clear directionality
- Post-breakout continuation

❌ **Poor Conditions**:
- Sideways/ranging markets
- Trend reversals
- Choppy EMAs (many crossovers)

---

## 3. GPU Optimization Engine

### 3.1 Walk-Forward Validation

```
Historical Data (3 months = ~6048 M15 candles)
├─ Split 70/30
│  ├─ Training Set (70% = ~4234 candles)
│  └─ Test Set (30% = ~1814 candles)
│
Phase 1: TRAINING (15% DD Limit)
├─ Test 100,000 parameter combinations
├─ Each combo runs full simulation on training data
├─ Reject if DD >= 15% or other fitness criteria
├─ Select BEST combo by fitness score
│
Phase 2: VALIDATION (20% DD Limit)
├─ Test ONLY the best combo on test data (unseen)
├─ Reject if DD >= 20%
├─ If passes → Use for live trading
└─ If fails → Return to defaults (manual review needed)
```

### 3.2 Fitness Function

**Purpose**: Prevent overfitting, reward consistency.

```python
Hard Filters (Instant Rejection):
├─ Drawdown >= 10.0 → Score = -999999
├─ Trades < 20 → Score = -999999 (no statistical significance)
└─ Trades > 500 → Score = -999999 (overtrading/overfitting)

Soft Metrics:
├─ Net Profit × 3.0 (weight: highest)
├─ Sharpe Ratio × 50.0 (profit / drawdown consistency)
├─ Win Rate × 30.0 (prefer 50-65%)
└─ Profit Factor × 10.0 (gross profit / gross loss)

Penalties:
├─ Win Rate > 75% → ×0.5 (too good = overfitting)
├─ Win Rate < 40% → ×0.6 (too poor)
├─ Profit Factor > 5.0 → ×0.4 (unrealistic)
└─ Profit Factor < 1.2 → ×0.7 (unprofitable)

Bonus:
├─ Daily Return 4-6% → ×1.5 (aligned with 5% goal)
└─ Daily Return 3-7% → ×1.2
```

### 3.3 Parameter Search Space

**Total Combinations**: ~53 BILLION

| Strategy | Parameter | Range | Options | Combinations |
|----------|-----------|-------|---------|--------------|
| **Scalper** | RSI Period | 5-14 | 6 | |
| | Oversold | 20-40 | 5 | |
| | Overbought | 60-80 | 5 | |
| | TP Mult | 1.5-5.0 | 6 | |
| | SL Mult | 1.0-3.0 | 5 | **4,500** |
| **Breakout** | BB Period | 10-30 | 5 | |
| | BB Dev | 1.5-2.5 | 5 | |
| | Max Width | 200-1000 | 5 | |
| | TP Mult | 2.0-10.0 | 5 | |
| | SL Mult | 1.0-3.0 | 5 | **3,125** |
| **Pullback** | Fast EMA | 20-50 | 6 | |
| | Slow EMA | 100-200 | 5 | |
| | RSI Trigger | 30-50 | 5 | |
| | TP Mult | 2.0-6.0 | 5 | |
| | SL Mult | 1.0-3.0 | 5 | **3,750** |

**Sampling Strategy**: Random sampling of 100,000 combinations to make computation feasible (~2-3 minutes).

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

---

## 5. System Components

### 5.1 File Structure
```
TitanFusion-cBot/
├── Titan pro/
│   ├── launcher.py          # User interface & configuration
│   ├── titan_hybrid.py      # Core trading engine (GPU + CPU)
│   ├── deriv_client.py      # WebSocket API client
│   ├── deriv_downloader.py  # Historical data fetcher
│   ├── dukascopy_downloader.py  # Forex data fetcher
│   ├── data_manager.py      # Data caching & updates
│   └── dashboard.html       # Web-based monitoring UI
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
