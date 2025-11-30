import time
import threading
import queue
import numpy as np
import pandas as pd
import pandas_ta as ta
import pyopencl as cl
import os
import sys
import itertools
import asyncio

# =============================================================================
# CONFIGURATION (Dynamic - set by launcher)
# =============================================================================
# Global variables (will be set by launcher.py)
SELECTED_SYMBOL = "R_75"
SELECTED_TIMEFRAME = "15min"  # pandas resample format
SELECTED_TF_MINUTES = 15
DATA_SOURCE = "dukascopy"  # 'dukascopy' or 'deriv'

# Initial "Safe" Parameters (Fallback)
DEFAULT_PARAMS = {
    'scalper': {'rsi_period': 10, 'os': 30, 'ob': 70, 'tp': 3.0, 'sl': 2.0},
    'breakout': {'bb_period': 20, 'dev': 2.0, 'max_w': 500, 'tp': 5.0, 'sl': 2.0},
    'pullback': {'fast': 34, 'slow': 144, 'trig': 40, 'tp': 4.0, 'sl': 2.0},
    'risk': 0.02
}

# Optimization Settings
OPTIMIZATION_INTERVAL = 100 # Re-optimize every 100 candles (timeframe-agnostic)
HISTORY_SIZE = 8640 # Keep last 8640 candles (~3 months for M15)
DOWNLOAD_CANDLES = 129600 # Download 129,600 M1 candles (90 days)

# Walk-Forward Settings
WALK_FORWARD_TRAIN_SIZE = 0.7  # 70% for training
WALK_FORWARD_TEST_SIZE = 0.3   # 30% for validation

# =============================================================================
# REAL GPU KERNEL (From titan_portfolio.py)
# =============================================================================
KERNEL_CODE = """
// --- HELPER FUNCTIONS ---
float get_ema(float prev_ema, float close, int period) {
    float alpha = 2.0f / (period + 1.0f);
    return (close - prev_ema) * alpha + prev_ema;
}

float get_rsi_next(float close, float prev_close, float avg_gain, float avg_loss, int period, float* out_gain, float* out_loss) {
    float change = close - prev_close;
    float gain = (change > 0) ? change : 0.0f;
    float loss = (change < 0) ? -change : 0.0f;
    
    *out_gain = (avg_gain * (period - 1) + gain) / period;
    *out_loss = (avg_loss * (period - 1) + loss) / period;
    
    if (*out_loss == 0.0f) return 100.0f;
    float rs = *out_gain / *out_loss;
    return 100.0f - (100.0f / (1.0f + rs));
}

// --- MAIN KERNEL ---
__kernel void portfolio_kernel(
    __global const float* close,
    __global const float* open,
    __global const float* high,
    __global const float* low,
    __global const float* atr,
    __global const int* hour,
    const int num_candles,
    __global const float* params,   // [S_P1..P5, B_P1..P5, P_P1..P5]
    __global float* results         // [NetProfit, Trades, Wins, MaxDD]
) {
    int gid = get_global_id(0);
    int offset = gid * 15; 
    
    // --- PARAMS ---
    float s_p1 = params[offset + 0]; float s_p2 = params[offset + 1]; float s_p3 = params[offset + 2]; float s_p4 = params[offset + 3]; float s_p5 = params[offset + 4];
    float b_p1 = params[offset + 5]; float b_p2 = params[offset + 6]; float b_p3 = params[offset + 7]; float b_p4 = params[offset + 8]; float b_p5 = params[offset + 9];
    float p_p1 = params[offset + 10]; float p_p2 = params[offset + 11]; float p_p3 = params[offset + 12]; float p_p4 = params[offset + 13]; float p_p5 = params[offset + 14];
    
    float risk_per_trade = 0.02f; 

    // --- STATE ---
    float balance = 50.0f;
    float max_equity = 50.0f;
    float max_dd = 0.0f;
    int total_trades = 0;
    int total_wins = 0;
    
    int pos_type[2] = {0, 0};
    float pos_entry[2] = {0.0f, 0.0f};
    float pos_sl[2] = {0.0f, 0.0f};
    float pos_tp[2] = {0.0f, 0.0f};
    float pos_vol[2] = {0.0f, 0.0f};
    
    // Indicators
    float s_rsi_gain = 0.0f; float s_rsi_loss = 0.0f; float s_rsi = 50.0f; float s_rsi_prev = 50.0f;
    float bb_buffer[30]; int bb_idx = 0; float bb_sum = 0.0f;
    for(int k=0; k<30; k++) bb_buffer[k] = close[0];
    bb_sum = close[0] * 30;
    float b_rsi_gain = 0.0f; float b_rsi_loss = 0.0f; float b_rsi = 50.0f; float b_ema = close[0];
    float p_ema_fast = close[0]; float p_ema_slow = close[0]; float p_rsi_gain = 0.0f; float p_rsi_loss = 0.0f; float p_rsi = 50.0f;
    
    for (int i = 1; i < num_candles; i++) {
        float c = close[i]; float o = open[i]; float h = high[i]; float l = low[i];
        float prev_c = close[i-1]; float atr_val = atr[i]; float atr_pips = atr_val * 10.0f;
        int h_day = hour[i];
        
        // Update Indicators
        s_rsi_prev = s_rsi;
        s_rsi = get_rsi_next(c, prev_c, s_rsi_gain, s_rsi_loss, (int)s_p1, &s_rsi_gain, &s_rsi_loss);
        
        int bb_p = (int)b_p1;
        bb_sum -= bb_buffer[bb_idx]; bb_buffer[bb_idx] = c; bb_sum += c; bb_idx = (bb_idx + 1) % bb_p;
        b_rsi = get_rsi_next(c, prev_c, b_rsi_gain, b_rsi_loss, 14, &b_rsi_gain, &b_rsi_loss);
        b_ema = get_ema(b_ema, c, 100);
        
        p_ema_fast = get_ema(p_ema_fast, c, (int)p_p1);
        p_ema_slow = get_ema(p_ema_slow, c, (int)p_p2);
        p_rsi = get_rsi_next(c, prev_c, p_rsi_gain, p_rsi_loss, 14, &p_rsi_gain, &p_rsi_loss);
        
        // Exits
        int active_count = 0;
        for (int k=0; k<2; k++) {
            if (pos_type[k] != 0) {
                float pnl = 0.0f; bool closed = false;
                if (pos_type[k] == 1) {
                    if (l <= pos_sl[k]) { pnl = (pos_sl[k] - pos_entry[k]) * 10.0f * pos_vol[k]; closed = true; }
                    else if (h >= pos_tp[k]) { pnl = (pos_tp[k] - pos_entry[k]) * 10.0f * pos_vol[k]; closed = true; }
                } else {
                    if (h >= pos_sl[k]) { pnl = (pos_entry[k] - pos_sl[k]) * 10.0f * pos_vol[k]; closed = true; }
                    else if (l <= pos_tp[k]) { pnl = (pos_entry[k] - pos_tp[k]) * 10.0f * pos_vol[k]; closed = true; }
                }
                if (closed) {
                    balance += pnl; total_trades++; if (pnl > 0) total_wins++; pos_type[k] = 0;
                    if (balance > max_equity) max_equity = balance;
                    float dd = max_equity - balance;
                    if (dd > max_dd) max_dd = dd;
                    if (dd >= 10.0f) { balance = -50.0f; i = num_candles; break; }
                } else active_count++;
            }
        }
        if (balance == -50.0f) break;
        
        // Entries
        bool time_ok = (h_day >= 7 && h_day < 20);
        bool vol_ok = (atr_pips >= 2.5f && atr_pips <= 500.0f);
        
        if (active_count < 2 && i > 200 && time_ok && vol_ok) {
            bool s_buy = (s_rsi_prev <= s_p2 && s_rsi > s_p2);
            bool s_sell = (s_rsi_prev >= s_p3 && s_rsi < s_p3);
            
            bool b_buy = false, b_sell = false;
            float sma = bb_sum / bb_p; float sum_sq = 0.0f;
            for(int j=0; j<bb_p; j++) { float d = close[i-j] - sma; sum_sq += d*d; }
            float std = sqrt(sum_sq / bb_p);
            float upper = sma + b_p2 * std; float lower = sma - b_p2 * std; float width = (upper - lower) * 10.0f;
            if (width <= b_p3) {
                 float body = fabs(c - o); float total = h - l;
                 if (total > 0 && (body/total) >= 0.5f) {
                     if (c > upper && b_rsi > 55 && c > b_ema) b_buy = true;
                     else if (c < lower && b_rsi < 45 && c < b_ema) b_sell = true;
                 }
            }
            
            bool p_buy = false, p_sell = false;
            bool uptrend = p_ema_fast > p_ema_slow; bool downtrend = p_ema_fast < p_ema_slow;
            if (uptrend && p_rsi < p_p3) p_buy = true;
            else if (downtrend && p_rsi > (100.0f - p_p3)) p_sell = true;
            
            int entry_dir = 0; float sl_m = 0, tp_m = 0;
            if (s_buy) { entry_dir=1; sl_m=s_p5; tp_m=s_p4; }
            else if (s_sell) { entry_dir=-1; sl_m=s_p5; tp_m=s_p4; }
            else if (p_buy) { entry_dir=1; sl_m=p_p5; tp_m=p_p4; }
            else if (p_sell) { entry_dir=-1; sl_m=p_p5; tp_m=p_p4; }
            else if (b_buy) { entry_dir=1; sl_m=b_p5; tp_m=b_p4; }
            else if (b_sell) { entry_dir=-1; sl_m=b_p5; tp_m=b_p4; }
            
            if (entry_dir != 0) {
                int slot = (pos_type[0] == 0) ? 0 : 1;
                pos_type[slot] = entry_dir; pos_entry[slot] = c;
                float sl_dist = atr_pips * sl_m * 0.10f; float tp_dist = atr_pips * tp_m * 0.10f;
                if (entry_dir == 1) { pos_sl[slot] = c - sl_dist; pos_tp[slot] = c + tp_dist; }
                else { pos_sl[slot] = c + sl_dist; pos_tp[slot] = c - tp_dist; }
                pos_vol[slot] = (balance * risk_per_trade) / (sl_dist * 10.0f);
                if (pos_vol[slot] < 0.01f) pos_vol[slot] = 0.01f;
            }
        }
    }
    
    int res_offset = gid * 4;
    results[res_offset + 0] = balance - 50.0f;
    results[res_offset + 1] = (float)total_trades;
    results[res_offset + 2] = (float)total_wins;
    results[res_offset + 3] = max_dd;
}
"""

# =============================================================================
# CPU ENGINE (Live Execution)
# =============================================================================
class CPUEngine:
    def __init__(self, params):
        self.params = params
        self.indicators = {
            'rsi': 50.0, 'rsi_gain': 0.0, 'rsi_loss': 0.0,
            'ema_fast': 0.0, 'ema_slow': 0.0,
            'bb_buffer': [], 'bb_sum': 0.0
        }
        print("⚡ CPU Engine Initialized")

    def update_params(self, new_params):
        print(f"⚡ CPU: Updating parameters...")
        self.params = new_params
        print(f"   New Scalper RSI: {self.params['scalper']['rsi_period']}")

    def on_candle(self, candle, prev_candle):
        """
        CRITICAL PATH: Must execute in < 1ms
        """
        start = time.perf_counter()
        c = candle['close']
        
        # --- SCALPER INDICATORS ---
        p = int(self.params['scalper']['rsi_period'])
        change = c - prev_candle['close']
        gain = max(change, 0)
        loss = max(-change, 0)
        
        self.indicators['rsi_gain'] = (self.indicators['rsi_gain'] * (p - 1) + gain) / p
        self.indicators['rsi_loss'] = (self.indicators['rsi_loss'] * (p - 1) + loss) / p
        
        if self.indicators['rsi_loss'] == 0: rs = 100
        else: rs = self.indicators['rsi_gain'] / self.indicators['rsi_loss']
        self.indicators['rsi'] = 100 - (100 / (1 + rs))
        
        # --- SIGNALS ---
        signal = None
        if self.indicators['rsi'] < self.params['scalper']['os']:
            signal = "BUY (Scalper)"
        elif self.indicators['rsi'] > self.params['scalper']['ob']:
            signal = "SELL (Scalper)"
            
        elapsed = (time.perf_counter() - start) * 1000
        return signal, elapsed, self.indicators['rsi']

# =============================================================================
# GPU ENGINE (Background Optimization)
# =============================================================================
class GPUEngine:
    def __init__(self):
        try:
            # Detect BOTH GPUs
            self.intel_device = None
            self.nvidia_device = None
            
            for platform in cl.get_platforms():
                if 'Intel' in platform.name and not self.intel_device:
                    self.intel_device = platform.get_devices(device_type=cl.device_type.GPU)[0]
                    print(f"🧠 Found: {self.intel_device.name}")
                if 'NVIDIA' in platform.name and not self.nvidia_device:
                    self.nvidia_device = platform.get_devices(device_type=cl.device_type.GPU)[0]
                    print(f"🧠 Found: {self.nvidia_device.name}")
            
            if not self.intel_device or not self.nvidia_device:
                print("⚠️ Warning: Not all GPUs detected. Using available GPU(s).")
            
            # Create contexts for both
            self.intel_ctx = cl.Context([self.intel_device]) if self.intel_device else None
            self.nvidia_ctx = cl.Context([self.nvidia_device]) if self.nvidia_device else None
            
            # Build kernels for both
            if self.intel_ctx:
                self.intel_queue = cl.CommandQueue(self.intel_ctx)
                self.intel_prg = cl.Program(self.intel_ctx, KERNEL_CODE).build()
                
            if self.nvidia_ctx:
                self.nvidia_queue = cl.CommandQueue(self.nvidia_ctx)
                self.nvidia_prg = cl.Program(self.nvidia_ctx, KERNEL_CODE).build()
            
            print("🧠 GPU Engine Initialized (Dual GPU Mode)")
            
            # Pre-generate Grid
            self.grid_params = self._generate_grid()
            print(f"🧠 GPU: Loaded {len(self.grid_params)} parameter combinations")
            
        except Exception as e:
            print(f"❌ GPU Init Error: {e}")
            self.intel_ctx = None
            self.nvidia_ctx = None

    def _generate_grid(self):
        # FULL FACTORIAL GRID - Each strategy gets INDEPENDENT parameters
        # Using Random Sampling to make it feasible
        
        import random
        random.seed(42)
        
        # Define parameter ranges for EACH strategy
        # Scalper ranges
        s_rsi_period = [5, 7, 9, 10, 12, 14]
        s_oversold = [20, 25, 30, 35, 40]
        s_overbought = [60, 65, 70, 75, 80]
        s_tp_atr = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
        s_sl_atr = [1.0, 1.5, 2.0, 2.5, 3.0]
        
        # Breakout ranges
        b_bb_period = [10, 15, 20, 25, 30]
        b_deviation = [1.5, 1.8, 2.0, 2.2, 2.5]
        b_max_width = [200, 400, 600, 800, 1000]
        b_tp_atr = [2.0, 4.0, 6.0, 8.0, 10.0]
        b_sl_atr = [1.0, 1.5, 2.0, 2.5, 3.0]
        
        # Pullback ranges
        p_fast_ema = [20, 25, 30, 34, 40, 50]
        p_slow_ema = [100, 120, 144, 180, 200]
        p_rsi_trig = [30, 35, 40, 45, 50]
        p_tp_atr = [2.0, 3.0, 4.0, 5.0, 6.0]
        p_sl_atr = [1.0, 1.5, 2.0, 2.5, 3.0]
        
        # Generate random combinations where EACH strategy varies independently
        num_samples = 100000  # 100k combinations for maximum coverage (with robust fitness anti-overfitting)
        
        combos = []
        for _ in range(num_samples):
            # Each combo has INDEPENDENT parameters for all 3 strategies
            combo = [
                # Scalper (5 params)
                random.choice(s_rsi_period),
                random.choice(s_oversold),
                random.choice(s_overbought),
                random.choice(s_tp_atr),
                random.choice(s_sl_atr),
                # Breakout (5 params)
                random.choice(b_bb_period),
                random.choice(b_deviation),
                random.choice(b_max_width),
                random.choice(b_tp_atr),
                random.choice(b_sl_atr),
                # Pullback (5 params)
                random.choice(p_fast_ema),
                random.choice(p_slow_ema),
                random.choice(p_rsi_trig),
                random.choice(p_tp_atr),
                random.choice(p_sl_atr)
            ]
            combos.append(combo)
        
        print(f"🧠 Generated {len(combos)} INDEPENDENT combinations (Full Factorial Random Sampling)")
        print(f"   Scalper: 6×5×5×6×5 = 4,500 possible configs")
        print(f"   Breakout: 5×5×5×5×5 = 3,125 possible configs")
        print(f"   Pullback: 6×5×5×5×5 = 3,750 possible configs")
        print(f"   Total search space: ~53 BILLION combinations")
        print(f"   Sampling: {len(combos)} random combinations from this space")
        
        return np.array(combos, dtype=np.float32)

    def calculate_robust_fitness(self, row):
        """
        ULTRA-ROBUST FITNESS FUNCTION
        - Multiple anti-overfitting measures
        - Penalizes statistical anomalies
        - Rewards consistency over flash performance
        """
        net = row['NetProfit']
        trades = row['Trades']
        wins = row['Wins']
        dd = row['MaxDD']
        
        # === HARD FILTERS (Instant Rejection) ===
        if dd >= 10.0:
            return -999999  # Death condition
        if trades < 20:
            return -999999  # Too few trades = no statistical significance
        if trades > 500:
            return -999999  # Too many trades = overtrading (overfitting signal)
        
        # === CALCULATE METRICS ===
        win_rate = wins / trades if trades > 0 else 0
        loss_count = trades - wins
        avg_win = net / wins if wins > 0 else 0
        avg_loss = abs(net) / loss_count if loss_count > 0 and net < 0 else 0.01
        
        # Profit Factor
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Sharpe-like Ratio (reward/risk)
        sharpe = net / dd if dd > 0 else 0
        
        # === ANTI-OVERFITTING PENALTIES ===
        
        # 1. Win Rate Penalty (too high = overfitting)
        if win_rate > 0.75:
            wr_penalty = 0.5  # 75%+ win rate is suspicious
        elif win_rate < 0.40:
            wr_penalty = 0.6  # Too low is bad
        else:
            wr_penalty = 1.0  # Sweet spot: 40-75%
        
        # 2. Profit Factor Penalty (too high = curve fitting)
        if profit_factor > 5.0:
            pf_penalty = 0.4  # PF > 5 is unrealistic
        elif profit_factor < 1.2:
            pf_penalty = 0.7  # Too low edge
        else:
            pf_penalty = 1.0  # Realistic: 1.2-5.0
        
        # 3. Trade Count Penalty (prefer moderate activity)
        if trades < 30:
            tc_penalty = 0.7  # Low sample
        elif trades > 300:
            tc_penalty = 0.6  # Overtrading
        elif 50 <= trades <= 150:
            tc_penalty = 1.2  # BONUS for sweet spot
        else:
            tc_penalty = 1.0
        
        # 4. Drawdown Severity Penalty
        dd_ratio = dd / 10.0  # Normalize to 0-1 (0 = no DD, 1 = death)
        dd_penalty = 1.0 - (dd_ratio * 0.5)  # Max 50% penalty
        
        # === COMPOSITE SCORE ===
        # Base score components
        profit_score = net * 2.0           # Weight: 2x
        sharpe_score = sharpe * 50.0       # Weight: high (consistency)
        wr_score = win_rate * 30.0         # Weight: moderate
        pf_score = profit_factor * 10.0    # Weight: moderate
        
        # Raw score
        raw_score = profit_score + sharpe_score + wr_score + pf_score
        
        # Apply penalties (multiplicative)
        final_score = raw_score * wr_penalty * pf_penalty * tc_penalty * dd_penalty
        
        return final_score

    def optimize(self, history_candles):
        """
        WALK-FORWARD OPTIMIZATION WITH VALIDATION
        - Split data: 70% train, 30% test
        - Find best on train set
        - Validate on test set (unseen data)
        - Only update if passes validation
        """
        if not self.intel_ctx and not self.nvidia_ctx: 
            return DEFAULT_PARAMS
        
        # Convert candles to arrays
        df = pd.DataFrame(history_candles)
        df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14).fillna(0)
        df['Hour'] = df['time'].dt.hour
        
        # === WALK-FORWARD SPLIT ===
        total_len = len(df)
        train_size = int(total_len * WALK_FORWARD_TRAIN_SIZE)
        
        df_train = df.iloc[:train_size]
        df_test = df.iloc[train_size:]
        
        print(f"   📊 Walk-Forward: Train={len(df_train)} candles | Test={len(df_test)} candles")
        
        # === PHASE 1: TRAIN (Find Best) ===
        print("   🧠 Phase 1: Training on historical data...")
        best_params, best_score = self._run_optimization(df_train, phase="TRAIN")
        
        if best_score <= -999000:
            print("   ⚠️ No valid parameters found in training!")
            return DEFAULT_PARAMS
        
        print(f"   ✅ Training Best Score: {best_score:.2f}")
        
        # === PHASE 2: TEST (Validate) ===
        print("   🔬 Phase 2: Validating on unseen data...")
        
        # Run ONLY the best params on test set
        test_result = self._test_single_params(df_test, best_params)
        
        if test_result['fitness'] <= -999000:
            print(f"   ❌ Validation FAILED! Best params hit death condition in test.")
            print(f"      → Keeping current parameters (no update)")
            return DEFAULT_PARAMS
        
        # Check if test performance is reasonable (not >50% worse than train)
        performance_ratio = test_result['fitness'] / best_score if best_score > 0 else 0
        
        if performance_ratio < 0.5:
            print(f"   ⚠️ Validation score dropped {(1-performance_ratio)*100:.1f}% from training")
            print(f"      Train: {best_score:.2f} | Test: {test_result['fitness']:.2f}")
            print(f"      → Possible overfitting detected. Keeping current parameters.")
            return DEFAULT_PARAMS
        
        print(f"   ✅ Validation PASSED! Test Score: {test_result['fitness']:.2f}")
        print(f"      Performance ratio: {performance_ratio*100:.1f}%")
        
        return best_params
    
    def _run_optimization(self, df, phase="TRAIN"):
        """Run full GPU optimization on dataset"""
        c = df['close'].values.astype(np.float32)
        o = df['open'].values.astype(np.float32)
        h = df['high'].values.astype(np.float32)
        l = df['low'].values.astype(np.float32)
        a = df['ATR'].values.astype(np.float32)
        hr = df['Hour'].values.astype(np.int32)
        
        # Split workload 50/50
        total_combos = len(self.grid_params)
        split_point = total_combos // 2
        
        intel_params = self.grid_params[:split_point]
        nvidia_params = self.grid_params[split_point:]
        
        print(f"      Intel GPU: {len(intel_params)} combos | NVIDIA GPU: {len(nvidia_params)} combos")
        
        # Results storage
        intel_results = None
        nvidia_results = None
        
        # Worker function for each GPU
        def gpu_worker(ctx, queue, prg, params, device_name):
            nonlocal intel_results, nvidia_results
            try:
                mf = cl.mem_flags
                b_c = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=c)
                b_o = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=o)
                b_h = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=h)
                b_l = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=l)
                b_a = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=a)
                b_hr = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=hr)
                b_p = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=params)
                
                res = np.zeros(len(params) * 4, dtype=np.float32)
                b_res = cl.Buffer(ctx, mf.WRITE_ONLY, res.nbytes)
                
                prg.portfolio_kernel(queue, (len(params),), None,
                    b_c, b_o, b_h, b_l, b_a, b_hr,
                    np.int32(len(c)), b_p, b_res)
                queue.finish()
                cl.enqueue_copy(queue, res, b_res)
                
                if 'Intel' in device_name:
                    intel_results = (params, res)
                else:
                    nvidia_results = (params, res)
                    
            except Exception as e:
                print(f"Error on {device_name}: {e}")
        
        # Run both GPUs in parallel
        import threading
        threads = []
        
        if self.intel_ctx:
            t = threading.Thread(target=gpu_worker, args=(self.intel_ctx, self.intel_queue, self.intel_prg, intel_params, "Intel"))
            threads.append(t)
            t.start()
            
        if self.nvidia_ctx:
            t = threading.Thread(target=gpu_worker, args=(self.nvidia_ctx, self.nvidia_queue, self.nvidia_prg, nvidia_params, "NVIDIA"))
            threads.append(t)
            t.start()
        
        # Wait for both to finish
        for t in threads:
            t.join()
        
        # Combine results
        all_params = []
        all_results = []
        
        if intel_results:
            all_params.append(intel_results[0])
            all_results.append(intel_results[1])
            
        if nvidia_results:
            all_params.append(nvidia_results[0])
            all_results.append(nvidia_results[1])
        
        if not all_params:
            return DEFAULT_PARAMS, -999999
            
        combined_params = np.vstack(all_params)
        combined_results = np.concatenate(all_results)
        
        # Process Results
        r = combined_results.reshape(len(combined_params), 4)
        df_res = pd.DataFrame(combined_params, columns=[f'P{k}' for k in range(15)])
        df_res['NetProfit'] = r[:, 0]
        df_res['Trades'] = r[:, 1]
        df_res['Wins'] = r[:, 2]
        df_res['MaxDD'] = r[:, 3]
        
        df_res['Fitness'] = df_res.apply(self.calculate_robust_fitness, axis=1)
        df_res.sort_values('Fitness', ascending=False, inplace=True)
        
        best = df_res.iloc[0]
        
        best_params = {
            'scalper': {'rsi_period': best['P0'], 'os': best['P1'], 'ob': best['P2'], 'tp': best['P3'], 'sl': best['P4']},
            'breakout': {'bb_period': best['P5'], 'dev': best['P6'], 'max_w': best['P7'], 'tp': best['P8'], 'sl': best['P9']},
            'pullback': {'fast': best['P10'], 'slow': best['P11'], 'trig': best['P12'], 'tp': best['P13'], 'sl': best['P14']},
            'risk': 0.02,
            'score': best['Fitness'],
            'profit': best['NetProfit']
        }
        
        return best_params, best['Fitness']
    
    def _test_single_params(self, df, params):
        """Test a single parameter set on validation data"""
        # Convert params dict to array format
        param_array = np.array([
            params['scalper']['rsi_period'], params['scalper']['os'], params['scalper']['ob'],
            params['scalper']['tp'], params['scalper']['sl'],
            params['breakout']['bb_period'], params['breakout']['dev'], params['breakout']['max_w'],
            params['breakout']['tp'], params['breakout']['sl'],
            params['pullback']['fast'], params['pullback']['slow'], params['pullback']['trig'],
            params['pullback']['tp'], params['pullback']['sl']
        ], dtype=np.float32).reshape(1, -1)
        
        # Run on GPU (use NVIDIA for speed)
        c = df['close'].values.astype(np.float32)
        o = df['open'].values.astype(np.float32)
        h = df['high'].values.astype(np.float32)
        l = df['low'].values.astype(np.float32)
        a = df['ATR'].values.astype(np.float32)
        hr = df['Hour'].values.astype(np.int32)
        
        ctx = self.nvidia_ctx if self.nvidia_ctx else self.intel_ctx
        queue = self.nvidia_queue if self.nvidia_ctx else self.intel_queue
        prg = self.nvidia_prg if self.nvidia_ctx else self.intel_prg
        
        mf = cl.mem_flags
        b_c = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=c)
        b_o = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=o)
        b_h = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=h)
        b_l = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=l)
        b_a = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=a)
        b_hr = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=hr)
        b_p = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=param_array)
        
        res = np.zeros(4, dtype=np.float32)
        b_res = cl.Buffer(ctx, mf.WRITE_ONLY, res.nbytes)
        
        prg.portfolio_kernel(queue, (1,), None,
            b_c, b_o, b_h, b_l, b_a, b_hr,
            np.int32(len(c)), b_p, b_res)
        queue.finish()
        cl.enqueue_copy(queue, res, b_res)
        
        # Calculate fitness
        result_df = pd.DataFrame({
            'NetProfit': [res[0]],
            'Trades': [res[1]],
            'Wins': [res[2]],
            'MaxDD': [res[3]]
        })
        
        fitness = self.calculate_robust_fitness(result_df.iloc[0])
        
        return {
            'fitness': fitness,
            'profit': res[0],
            'trades': res[1],
            'wins': res[2],
            'dd': res[3]
        }

# =============================================================================
# HYBRID SYSTEM (The Orchestrator)
# =============================================================================
class HybridTrader:
    def __init__(self):
        self.cpu = CPUEngine(DEFAULT_PARAMS)
        self.gpu = GPUEngine()
        
        self.history =[]
        self.optimization_queue = queue.Queue()
        self.is_running = True
        
        # Weekly optimization tracking
        self.last_full_optimization = None
        self.candle_count = 0
        
        # Start Background Thread
        self.bg_thread = threading.Thread(target=self.background_loop, daemon=True)
        self.bg_thread.start()
        
    def initialize_with_history(self):
        """
        Downloads 6 months of history and runs initial optimization ("Pre-Flight Check")
        Uses Data Manager with auto-update (7-day freshness check)
        """
        print("\n🚀 System Initialization: Loading Historical Data...")
        
        from data_manager import DataManager
        manager = DataManager()
        
        # Get data (auto-updates if >7 days old)
        df_m1 = manager.get_data(source=DATA_SOURCE, auto_update=True)
        
        if df_m1 is None or df_m1.empty:
            print("❌ Failed to load data!")
            return
        
        # Aggregate to selected timeframe
        print(f"🔄 Aggregating M1 → {SELECTED_TIMEFRAME}...")
        
        df_m1.set_index('time', inplace=True)
        
        df_tf = df_m1.resample(SELECTED_TIMEFRAME).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).dropna().reset_index()
        
        # Keep last N candles
        self.history = df_tf.tail(HISTORY_SIZE).to_dict('records')
        print(f"✅ Loaded {len(self.history)} {SELECTED_TIMEFRAME} candles for calibration")
        
        # Initial Optimization
        print("🧠 Running Pre-Flight Optimization...")
        best_params = self.gpu.optimize(self.history)
        self.cpu.update_params(best_params)
        print(f"✅ System Calibrated! Score: {best_params.get('score', 0):.2f}")
        
        # Schedule weekly re-calibration
        self.last_full_optimization = datetime.now()
        print(f"📅 Next full re-optimization: {(self.last_full_optimization + timedelta(days=7)).strftime('%Y-%m-%d')}")
        
    def on_new_data(self, candle):
        # 1. LIVE EXECUTION (CPU)
        prev = self.history[-1] if self.history else candle 
        signal, latency, rsi = self.cpu.on_candle(candle, prev)
        
        print(f"Tick: {candle['time']} | RSI: {rsi:.1f} | Latency: {latency:.3f}ms | Signal: {signal if signal else '-'}")
        
        # 2. DATA MANAGEMENT
        self.history.append(candle)
        if len(self.history) > HISTORY_SIZE:
            self.history.pop(0)
        
        self.candle_count += 1
            
        # 3. TRIGGER OPTIMIZATION (Regular - every 100 candles)
        if len(self.history) % OPTIMIZATION_INTERVAL == 0:
            print("   [Triggering GPU Optimization...]")
            self.optimization_queue.put(list(self.history))
        
        # 4. WEEKLY DATA UPDATE & FULL RE-OPTIMIZATION
        if self.last_full_optimization:
            days_since_last = (datetime.now() - self.last_full_optimization).days
            
            if days_since_last >= 7:
                print("\n" + "="*70)
                print("📅 WEEKLY RE-CALIBRATION TRIGGERED (7 days elapsed)")
                print("="*70)
                
                from data_manager import DataManager
                manager = DataManager()
                
                # Force update data
                print("📥 Updating data source...")
                if DATA_SOURCE == 'dukascopy':
                    manager.update_dukascopy(force=True)
                else:
                    manager.update_deriv()
                
                # Reload and re-optimize
                print("🔄 Re-initializing with fresh data...")
                self.initialize_with_history()
                
                print("✅ Weekly re-calibration complete!")
                print("="*70 + "\n")
            
    def background_loop(self):
        while self.is_running:
            try:
                data = self.optimization_queue.get(timeout=1.0)
                print("\n🧠 GPU: Starting Background Optimization...")
                start = time.time()
                
                best_result = self.gpu.optimize(data)
                
                duration = time.time() - start
                print(f"🧠 GPU: Optimization Complete in {duration:.2f}s | Best Score: {best_result['score']:.2f}")
                
                if best_result['score'] > -9000: # Valid result
                    self.cpu.update_params(best_result)
                    print("   [System Updated with New Parameters]\n")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"GPU Error: {e}")

# =============================================================================
# LIVE TRADING LOOP (Deriv API)
# =============================================================================
def run_live_trading():
    from deriv_client import DerivClient
    
    print("="*50)
    print("TITAN PRO - LIVE HYBRID TRADING (DERIV API)")
    print("="*50)
    print("⏰ Timeframe: M15")
    print("💰 Balance: $50")
    print("🎯 Risk: 2% per trade")
    print("="*50)
    
    trader = HybridTrader()
    trader.initialize_with_history() # Pre-flight check
    
    client = DerivClient()
    
    # M1 -> M15 Aggregator State
    m1_buffer = []
    current_m1 = None
    last_minute = -1
    
    def on_tick(tick):
        nonlocal current_m1, last_minute, m1_buffer
        
        price = tick['quote']
        epoch = tick['epoch']
        timestamp = pd.to_datetime(epoch, unit='s')
        minute = timestamp.minute
        
        # Build M1 Candles
        if minute != last_minute:
            if current_m1:
                current_m1['close'] = price
                m1_buffer.append(current_m1)
                
                # Every 15 M1 candles = 1 M15 candle
                if len(m1_buffer) >= 15:
                    # Aggregate to M15
                    m15_candle = {
                        'time': m1_buffer[0]['time'],
                        'open': m1_buffer[0]['open'],
                        'high': max(c['high'] for c in m1_buffer),
                        'low': min(c['low'] for c in m1_buffer),
                        'close': m1_buffer[-1]['close'],
                        'epoch': m1_buffer[-1]['epoch']
                    }
                    
                    # Feed M15 to engine
                    trader.on_new_data(m15_candle)
                    print(f"\n🕯️ M15 Candle: {m15_candle['time']} | O:{m15_candle['open']:.2f} H:{m15_candle['high']:.2f} L:{m15_candle['low']:.2f} C:{m15_candle['close']:.2f}")
                    
                    # Clear buffer
                    m1_buffer = []
            
            current_m1 = {
                'time': timestamp, 'open': price, 'high': price, 'low': price, 'close': price, 'epoch': epoch
            }
            last_minute = minute
            
        else:
            if current_m1:
                current_m1['high'] = max(current_m1['high'], price)
                current_m1['low'] = min(current_m1['low'], price)
                current_m1['close'] = price
                print(f"\rPrice: {price:.2f} | M1 Buffer: {len(m1_buffer)}/15", end="")

    if client.start(on_tick):
        print("✅ System Live! Waiting for ticks...")
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
    else:
        print("❌ Failed to start Deriv Client")

if __name__ == "__main__":
    run_live_trading()
