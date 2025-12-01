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
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURATION (Dynamic - set by launcher)
# =============================================================================
# Global variables (will be set by launcher.py)
SELECTED_SYMBOL = "R_75"
SELECTED_TIMEFRAME = "15min"  # pandas resample format
WORKING_CAPITAL = 50.0     # Amount to trade with
ACCOUNT_BALANCE = 50.0     # Full account balance

# Initial "Safe" Parameters (Fallback)
DEFAULT_PARAMS = {
    'scalper': {
        'rsi_period': 10, 'rsi_buy': 30, 'rsi_sell': 70,
        'atr_min': 5, 'atr_max': 200, 'adx_min': 20,
        'hour_start': 0, 'hour_end': 23,
        'tp': 3.0, 'sl': 2.0, 'body_min': 0.5
    },
    'breakout': {
        'bb_period': 20, 'dev': 2.0, 
        'min_w': 10, 'max_w': 500,
        'rsi_thresh': 50, 'ema_period': 100,
        'body_min': 0.5, 'atr_min': 5,
        'tp': 5.0, 'sl': 2.0
    },
    'pullback': {
        'fast': 34, 'slow': 144,
        'rsi_buy': 40, 'rsi_sell': 60,
        'adx_min': 25, 'atr_min': 5,
        'tp': 4.0, 'sl': 2.0
    },
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

// ADX Helper (Simplified for stream processing)
void update_adx(float high, float low, float close, float prev_high, float prev_low, float prev_close, 
                float* tr_smooth, float* dm_p_smooth, float* dm_m_smooth, float* adx_val, int period) {
    
    float tr = fmax(high - low, fmax(fabs(high - prev_close), fabs(low - prev_close)));
    float dm_p = (high - prev_high > prev_low - low) ? fmax(high - prev_high, 0.0f) : 0.0f;
    float dm_m = (prev_low - low > high - prev_high) ? fmax(prev_low - low, 0.0f) : 0.0f;
    
    float alpha = 1.0f / period;
    *tr_smooth = *tr_smooth * (1.0f - alpha) + tr * alpha;
    *dm_p_smooth = *dm_p_smooth * (1.0f - alpha) + dm_p * alpha;
    *dm_m_smooth = *dm_m_smooth * (1.0f - alpha) + dm_m * alpha;
    
    float di_p = (*tr_smooth > 0) ? (*dm_p_smooth / *tr_smooth) * 100.0f : 0.0f;
    float di_m = (*tr_smooth > 0) ? (*dm_m_smooth / *tr_smooth) * 100.0f : 0.0f;
    
    float dx = (di_p + di_m > 0) ? (fabs(di_p - di_m) / (di_p + di_m)) * 100.0f : 0.0f;
    *adx_val = *adx_val * (1.0f - alpha) + dx * alpha;
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
    const float initial_balance,
    const int optimization_phase,  // 0=train(25%), 1=validate(30%), 2=live(12%)
    __global const float* params,  // 40 params per combo
    __global float* results        // [NetProfit, Trades, Wins, MaxDD, TotalMFE, TotalMAE]
) {
    int gid = get_global_id(0);
    int offset = gid * 40; 
    
    // --- UNPACK PARAMS (40 total) ---
    // Scalper (15 params)
    float s_rsi_period = params[offset + 0];
    float s_rsi_buy    = params[offset + 1];
    float s_rsi_sell   = params[offset + 2];
    float s_atr_min    = params[offset + 3];
    float s_atr_max    = params[offset + 4];
    float s_adx_min    = params[offset + 5];
    float s_hour_start = params[offset + 6];
    float s_hour_end   = params[offset + 7];
    float s_tp_atr     = params[offset + 8];
    float s_sl_atr     = params[offset + 9];
    float s_body_min   = params[offset + 10];
    float s_max_spread = params[offset + 11]; // New
    float s_flat_pips  = params[offset + 12]; // New
    
    // Breakout (12 params) - Offset 15
    float b_bb_period  = params[offset + 15];
    float b_bb_dev     = params[offset + 16];
    float b_min_width  = params[offset + 17];
    float b_max_width  = params[offset + 18];
    float b_rsi_thresh = params[offset + 19];
    float b_ema_period = params[offset + 20];
    float b_body_min   = params[offset + 21];
    float b_atr_min    = params[offset + 22];
    float b_tp_atr     = params[offset + 23];
    float b_sl_atr     = params[offset + 24];
    float b_max_spread = params[offset + 25]; // New
    float b_flat_pips  = params[offset + 26]; // New
    
    // Pullback (13 params) - Offset 27
    float p_fast_ema   = params[offset + 27];
    float p_slow_ema   = params[offset + 28];
    float p_rsi_buy    = params[offset + 29];
    float p_rsi_sell   = params[offset + 30];
    float p_adx_min    = params[offset + 31];
    float p_atr_min    = params[offset + 32];
    float p_tp_atr     = params[offset + 33];
    float p_sl_atr     = params[offset + 34];
    float p_max_spread = params[offset + 35]; // New
    float p_flat_pips  = params[offset + 36]; // New
    
    float risk_per_trade = 0.02f; 

    // --- STATE ---
    float balance = initial_balance;
    float max_equity = initial_balance;
    float max_dd = 0.0f;
    int total_trades = 0;
    int total_wins = 0;
    float total_mfe = 0.0f;
    float total_mae = 0.0f;
    
    int pos_type[2] = {0, 0};
    float pos_entry[2] = {0.0f, 0.0f};
    float pos_sl[2] = {0.0f, 0.0f};
    float pos_tp[2] = {0.0f, 0.0f};
    float pos_vol[2] = {0.0f, 0.0f};
    float pos_mfe[2] = {0.0f, 0.0f};
    float pos_mae[2] = {0.0f, 0.0f};
    
    // Indicators State
    float s_rsi_gain = 0.0f, s_rsi_loss = 0.0f, s_rsi = 50.0f, s_rsi_prev = 50.0f;
    
    // BB State
    float bb_buffer[50]; int bb_idx = 0; float bb_sum = 0.0f;
    for(int k=0; k<50; k++) bb_buffer[k] = close[0];
    bb_sum = close[0] * 50; 
    
    // Breakout Indicators
    float b_rsi_gain = 0.0f, b_rsi_loss = 0.0f, b_rsi = 50.0f;
    float b_ema = close[0];
    
    // Pullback Indicators
    float p_ema_fast = close[0], p_ema_slow = close[0];
    float p_rsi_gain = 0.0f, p_rsi_loss = 0.0f, p_rsi = 50.0f;
    
    // ADX State
    float tr_smooth = 0.0f, dm_p_smooth = 0.0f, dm_m_smooth = 0.0f, adx_val = 0.0f;
    
    for (int i = 1; i < num_candles; i++) {
        float c = close[i]; float o = open[i]; float h = high[i]; float l = low[i];
        float prev_c = close[i-1]; float prev_h = high[i-1]; float prev_l = low[i-1];
        float atr_val = atr[i]; float atr_pips = atr_val * 10.0f;
        int h_day = hour[i];
        
        // Update Indicators
        s_rsi_prev = s_rsi;
        s_rsi = get_rsi_next(c, prev_c, s_rsi_gain, s_rsi_loss, (int)s_rsi_period, &s_rsi_gain, &s_rsi_loss);
        
        // BB
        int bb_p = (int)b_bb_period;
        bb_sum -= bb_buffer[bb_idx]; bb_buffer[bb_idx] = c; bb_sum += c; bb_idx = (bb_idx + 1) % 50;
        
        b_rsi = get_rsi_next(c, prev_c, b_rsi_gain, b_rsi_loss, 14, &b_rsi_gain, &b_rsi_loss);
        b_ema = get_ema(b_ema, c, (int)b_ema_period);
        
        p_ema_fast = get_ema(p_ema_fast, c, (int)p_fast_ema);
        p_ema_slow = get_ema(p_ema_slow, c, (int)p_slow_ema);
        p_rsi = get_rsi_next(c, prev_c, p_rsi_gain, p_rsi_loss, 14, &p_rsi_gain, &p_rsi_loss);
        
        update_adx(h, l, c, prev_h, prev_l, prev_c, &tr_smooth, &dm_p_smooth, &dm_m_smooth, &adx_val, 14);
        
        // --- EXITS & MFE/MAE ---
        int active_count = 0;
        for (int k=0; k<2; k++) {
            if (pos_type[k] != 0) {
                float unrealized = 0.0f;
                if (pos_type[k] == 1) unrealized = (h - pos_entry[k]) * 10.0f;
                else unrealized = (pos_entry[k] - l) * 10.0f;
                if (unrealized > pos_mfe[k]) pos_mfe[k] = unrealized;
                
                float drawdown = 0.0f;
                if (pos_type[k] == 1) drawdown = (l - pos_entry[k]) * 10.0f;
                else drawdown = (pos_entry[k] - h) * 10.0f;
                if (drawdown < pos_mae[k]) pos_mae[k] = drawdown;

                float pnl = 0.0f; bool closed = false;
                if (pos_type[k] == 1) {
                    if (l <= pos_sl[k]) { pnl = (pos_sl[k] - pos_entry[k]) * 10.0f * pos_vol[k]; closed = true; }
                    else if (h >= pos_tp[k]) { pnl = (pos_tp[k] - pos_entry[k]) * 10.0f * pos_vol[k]; closed = true; }
                } else {
                    if (h >= pos_sl[k]) { pnl = (pos_entry[k] - pos_sl[k]) * 10.0f * pos_vol[k]; closed = true; }
                    else if (l <= pos_tp[k]) { pnl = (pos_entry[k] - pos_tp[k]) * 10.0f * pos_vol[k]; closed = true; }
                }
                
                if (closed) {
                    balance += pnl; total_trades++; if (pnl > 0) total_wins++; 
                    total_mfe += pos_mfe[k]; total_mae += pos_mae[k];
                    pos_type[k] = 0; pos_mfe[k] = 0; pos_mae[k] = 0;
                    
                    if (balance > max_equity) max_equity = balance;
                    float dd = max_equity - balance;
                    if (dd > max_dd) max_dd = dd;
                    
                    float dd_threshold;
                    if (optimization_phase == 0) dd_threshold = initial_balance * 0.25f;
                    else if (optimization_phase == 1) dd_threshold = initial_balance * 0.30f;
                    else dd_threshold = initial_balance * 0.15f;
                    
                    if (dd >= dd_threshold) { 
                        balance = -initial_balance; i = num_candles; break; 
                    }
                } else active_count++;
            }
        }
        if (balance < 0) break;
        
        // --- ENTRIES ---
        if (active_count < 2 && i > 200) {
            float body_size = fabs(c - o);
            float total_size = h - l;
            float body_pct = (total_size > 0) ? body_size / total_size : 0.0f;
            
            // SCALPER
            bool s_time = (h_day >= (int)s_hour_start && h_day <= (int)s_hour_end);
            bool s_vol = (atr_pips >= s_atr_min && atr_pips <= s_atr_max);
            bool s_flat = (atr_pips >= s_flat_pips); // Flat market filter
            bool s_trend = (adx_val >= s_adx_min);
            bool s_body = (body_pct >= s_body_min);
            
            bool s_buy_sig = (s_time && s_vol && s_flat && s_trend && s_body && s_rsi_prev <= s_rsi_buy && s_rsi > s_rsi_buy);
            bool s_sell_sig = (s_time && s_vol && s_flat && s_trend && s_body && s_rsi_prev >= s_rsi_sell && s_rsi < s_rsi_sell);
            
            // BREAKOUT
            bool b_vol = (atr_pips >= b_atr_min);
            bool b_flat = (atr_pips >= b_flat_pips);
            bool b_body = (body_pct >= b_body_min);
            
            float sma = bb_sum / bb_p; float sum_sq = 0.0f;
            int start_j = (bb_idx - 1 + 50) % 50; 
            for(int j=0; j<bb_p; j++) { 
                int idx = (start_j - j + 50) % 50;
                float d = bb_buffer[idx] - sma; 
                sum_sq += d*d; 
            }
            float std = sqrt(sum_sq / bb_p);
            float upper = sma + b_bb_dev * std; float lower = sma - b_bb_dev * std; float width = (upper - lower) * 10.0f;
            
            bool b_buy_sig = false, b_sell_sig = false;
            if (b_vol && b_flat && b_body && width >= b_min_width && width <= b_max_width) {
                 if (c > upper && b_rsi > b_rsi_thresh && c > b_ema) b_buy_sig = true;
                 else if (c < lower && b_rsi < (100-b_rsi_thresh) && c < b_ema) b_sell_sig = true;
            }
            
            // PULLBACK
            bool p_vol = (atr_pips >= p_atr_min);
            bool p_flat = (atr_pips >= p_flat_pips);
            bool p_trend = (adx_val >= p_adx_min);
            bool uptrend = p_ema_fast > p_ema_slow;
            bool downtrend = p_ema_fast < p_ema_slow;
            
            bool p_buy_sig = (p_vol && p_flat && p_trend && uptrend && p_rsi < p_rsi_buy);
            bool p_sell_sig = (p_vol && p_flat && p_trend && downtrend && p_rsi > p_rsi_sell);
            
            // EXECUTE
            int entry_dir = 0; float sl_m = 0, tp_m = 0;
            if (s_buy_sig) { entry_dir=1; sl_m=s_sl_atr; tp_m=s_tp_atr; }
            else if (s_sell_sig) { entry_dir=-1; sl_m=s_sl_atr; tp_m=s_tp_atr; }
            else if (p_buy_sig) { entry_dir=1; sl_m=p_sl_atr; tp_m=p_tp_atr; }
            else if (p_sell_sig) { entry_dir=-1; sl_m=p_sl_atr; tp_m=p_tp_atr; }
            else if (b_buy_sig) { entry_dir=1; sl_m=b_sl_atr; tp_m=b_tp_atr; }
            else if (b_sell_sig) { entry_dir=-1; sl_m=b_sl_atr; tp_m=b_tp_atr; }
            
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
    
    int res_offset = gid * 6; // Size 6
    results[res_offset + 0] = balance - initial_balance;
    results[res_offset + 1] = (float)total_trades;
    results[res_offset + 2] = (float)total_wins;
    results[res_offset + 3] = max_dd;
    results[res_offset + 4] = total_mfe;
    results[res_offset + 5] = total_mae;
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
            'bb_buffer': [], 'bb_sum': 0.0,
            'tr_smooth': 0.0, 'dm_p_smooth': 0.0, 'dm_m_smooth': 0.0, 'adx': 0.0,
            'atr': 0.0
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
        h = candle['high']
        l = candle['low']
        o = candle['open']
        
        prev_c = prev_candle['close']
        prev_h = prev_candle['high']
        prev_l = prev_candle['low']
        
        # --- UPDATE INDICATORS ---
        
        # 1. ATR (14)
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        alpha_atr = 1.0 / 14.0
        self.indicators['atr'] = self.indicators['atr'] * (1 - alpha_atr) + tr * alpha_atr
        atr_pips = self.indicators['atr'] * 10.0
        
        # 2. ADX (14)
        dm_p = max(h - prev_h, 0) if (h - prev_h) > (prev_l - l) else 0
        dm_m = max(prev_l - l, 0) if (prev_l - l) > (h - prev_h) else 0
        
        self.indicators['tr_smooth'] = self.indicators['tr_smooth'] * (1 - alpha_atr) + tr * alpha_atr
        self.indicators['dm_p_smooth'] = self.indicators['dm_p_smooth'] * (1 - alpha_atr) + dm_p * alpha_atr
        self.indicators['dm_m_smooth'] = self.indicators['dm_m_smooth'] * (1 - alpha_atr) + dm_m * alpha_atr
        
        di_p = (self.indicators['dm_p_smooth'] / self.indicators['tr_smooth']) * 100 if self.indicators['tr_smooth'] > 0 else 0
        di_m = (self.indicators['dm_m_smooth'] / self.indicators['tr_smooth']) * 100 if self.indicators['tr_smooth'] > 0 else 0
        dx = (abs(di_p - di_m) / (di_p + di_m)) * 100 if (di_p + di_m) > 0 else 0
        self.indicators['adx'] = self.indicators['adx'] * (1 - alpha_atr) + dx * alpha_atr
        
        # 3. RSI (Scalper Period)
        p_rsi = int(self.params['scalper']['rsi_period'])
        change = c - prev_c
        gain = max(change, 0)
        loss = max(-change, 0)
        self.indicators['rsi_gain'] = (self.indicators['rsi_gain'] * (p_rsi - 1) + gain) / p_rsi
        self.indicators['rsi_loss'] = (self.indicators['rsi_loss'] * (p_rsi - 1) + loss) / p_rsi
        if self.indicators['rsi_loss'] == 0: rs = 100
        else: rs = self.indicators['rsi_gain'] / self.indicators['rsi_loss']
        self.indicators['rsi'] = 100 - (100 / (1 + rs))
        
        # 4. Bollinger Bands (Breakout Period)
        bb_p = int(self.params['breakout']['bb_period'])
        self.indicators['bb_buffer'].append(c)
        if len(self.indicators['bb_buffer']) > bb_p:
            removed = self.indicators['bb_buffer'].pop(0)
            self.indicators['bb_sum'] -= removed
        self.indicators['bb_sum'] += c
        
        # --- SIGNALS ---
        signal = None
        
        # Common Filters
        current_hour = pd.Timestamp.now().hour # Approximate
        body_size = abs(c - o)
        total_size = h - l
        body_pct = body_size / total_size if total_size > 0 else 0
        
        # SCALPER LOGIC
        s = self.params['scalper']
        s_time = (current_hour >= s['hour_start'] and current_hour <= s['hour_end'])
        s_vol = (atr_pips >= s['atr_min'] and atr_pips <= s['atr_max'])
        s_trend = (self.indicators['adx'] >= s['adx_min'])
        s_body = (body_pct >= s['body_min'])
        
        if s_time and s_vol and s_trend and s_body:
            if self.indicators['rsi'] < s['rsi_buy']:
                signal = "BUY (Scalper)"
            elif self.indicators['rsi'] > s['rsi_sell']:
                signal = "SELL (Scalper)"
        
        # BREAKOUT LOGIC (Simplified for CPU speed)
        if not signal and len(self.indicators['bb_buffer']) >= bb_p:
            b = self.params['breakout']
            sma = self.indicators['bb_sum'] / bb_p
            std = np.std(self.indicators['bb_buffer'])
            upper = sma + b['dev'] * std
            lower = sma - b['dev'] * std
            width = (upper - lower) * 10.0
            
            if width >= b['min_w'] and width <= b['max_w']:
                if c > upper and self.indicators['rsi'] > b['rsi_thresh']:
                    signal = "BUY (Breakout)"
                elif c < lower and self.indicators['rsi'] < (100 - b['rsi_thresh']):
                    signal = "SELL (Breakout)"

        elapsed = (time.perf_counter() - start) * 1000
        return signal, elapsed, self.indicators['rsi']

# =============================================================================
# GPU ENGINE (Background Optimization)
# =============================================================================
class GPUEngine:
    def __init__(self, initial_balance=50.0):
        self.initial_balance = initial_balance  # Store balance for kernel
        self.optimization_phase = 0  # Default to training phase
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
    
    def set_balance(self, new_balance):
        """Update initial balance for optimization"""
        self.initial_balance = new_balance
        print(f"💰 GPU Engine: Balance updated to ${new_balance}")
    
    def set_phase(self, phase):
        """Set optimization phase: 0=train, 1=validate, 2=live"""
        self.optimization_phase = phase
        phase_names = {0: "Training (15% DD)", 1: "Validation (20% DD)", 2: "Live Trading (12% DD)"}
        print(f"🔧 GPU Engine: Phase set to {phase_names.get(phase, 'Unknown')}")

    def _generate_grid(self, center_params=None):
        # MEGA GRID - 500k combinations
        # If center_params is provided, generates grid around it (Refinement)
        # If None, generates Global Grid with WIDE ranges (1-150+)
        import random

    def calculate_ultra_robust_fitness(self, row):
        net = row['NetProfit']
        trades = row['Trades']
        wins = row['Wins']
        dd = row['MaxDD']
        mfe_total = row.get('TotalMFE', 0)
        mae_total = row.get('TotalMAE', 0)
        
        # === HARD FILTERS ===
        dd_threshold = self.initial_balance * 0.25 # 25% training limit
        if dd >= dd_threshold: return -999999
        if trades < 10: return -999999
        if trades > 1000: return -999999
        
        # === METRICS ===
        win_rate = wins / trades if trades > 0 else 0
        loss_count = trades - wins
        gross_profit = net if net > 0 else 0
        gross_loss = abs(net) if net < 0 else 0.01
        
        avg_win = gross_profit / wins if wins > 0 else 0
        avg_loss = gross_loss / loss_count if loss_count > 0 else 0.01
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        avg_trade = net / trades if trades > 0 else 0
        sharpe = avg_trade / max(dd, 1.0)
        
        # Sortino (Downside Risk)
        downside_dev = avg_loss if loss_count > 0 else 1.0
        sortino = avg_trade / max(downside_dev, 0.01)
        
        # Efficiency
        mfe_efficiency = net / max(mfe_total, 0.01) if mfe_total > 0 else 0
        mae_efficiency = 1.0 - (abs(mae_total) / max(dd, 0.01))
        
        # === BONUSES ===
        volume_bonus = 1.0
        if 50 <= trades <= 200: volume_bonus = 2.0
        elif 30 <= trades <= 300: volume_bonus = 1.5
        elif 20 <= trades <= 400: volume_bonus = 1.3
        
        daily_return_pct = (net / self.initial_balance) * 100
        target_bonus = 1.0
        if 10 <= daily_return_pct <= 20: target_bonus = 1.5
        elif 5 <= daily_return_pct <= 25: target_bonus = 1.2
        
        # === PENALTIES ===
        wr_penalty = 1.0
        if win_rate > 0.80: wr_penalty = 0.3
        elif win_rate < 0.35: wr_penalty = 0.6
        
        # === SCORE ===
        raw_score = (net * 3.0) + (sharpe * 100.0) + (sortino * 80.0) + (mfe_efficiency * 50.0) + (mae_efficiency * 30.0)
        final_score = raw_score * volume_bonus * target_bonus * wr_penalty
        
        return final_score

    def optimize(self, history_candles):
        """
        COARSE-TO-FINE OPTIMIZATION (2-STAGE)
        Stage 1: Global Search (Wide Ranges) -> Find rough best area
        Stage 2: Refinement (Local Grid) -> Optimize around best area
        Stage 3: Validation -> Test top candidates on unseen data
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
        
        # === STAGE 1: GLOBAL SEARCH (Wide Ranges) ===
        self.optimization_phase = 0
        print("   🌍 Stage 1: Global Search (Wide Ranges)...")
        
        # Generate Global Grid
        self.grid_params = self._generate_grid(center_params=None)
        
        # Find Single Best from Global
        global_candidates = self._run_optimization(df_train, phase="TRAIN", top_n=1)
        
        if not global_candidates:
            print("   ⚠️ No valid parameters found in Global Search!")
            return DEFAULT_PARAMS
            
        best_global = global_candidates[0]
        print(f"   ✅ Global Best Score: {best_global['score']:.2f}")
        
        # === STAGE 2: REFINEMENT (Local Search) ===
        print("   🎯 Stage 2: Refinement (Local Search)...")
        
        # Generate Local Grid around Global Best
        self.grid_params = self._generate_grid(center_params=best_global['raw'])
        
        # Find Top 10 from Refined Grid
        refined_candidates = self._run_optimization(df_train, phase="TRAIN", top_n=10)
        
        if not refined_candidates:
            print("   ⚠️ No valid parameters found in Refinement!")
            return DEFAULT_PARAMS
            
        print(f"   ✅ Refined Best Score: {refined_candidates[0]['score']:.2f}")
        
        # === STAGE 3: VALIDATION (Test on Unseen Data) ===
        self.optimization_phase = 1
        print("   🔬 Stage 3: Validating candidates on unseen data... (30% DD limit)")
        
        best_validated_params = None
        best_validated_score = -999999
        
        for i, candidate in enumerate(refined_candidates):
            test_result = self._test_single_params(df_test, candidate)
            
            if test_result['fitness'] <= -999000:
                print(f"      ❌ Candidate #{i+1} FAILED validation")
                continue
            
            print(f"      ✅ Candidate #{i+1} PASSED! Train: {candidate['score']:.0f} | Test: {test_result['fitness']:.0f}")
            
            if test_result['fitness'] > best_validated_score:
                best_validated_score = test_result['fitness']
                best_validated_params = candidate
        
        if best_validated_params:
            print(f"   🏆 Selected Best Validated Params! Score: {best_validated_score:.2f}")
            return best_validated_params
        else:
            print(f"   ❌ ALL candidates failed validation. Keeping current parameters.")
            return DEFAULT_PARAMS
    
    def _run_optimization(self, df, phase="TRAIN", top_n=10):
        """Run full GPU optimization and return top N candidates"""
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
                
                # Result size: 6 floats per combo
                res = np.zeros(len(params) * 6, dtype=np.float32)
                b_res = cl.Buffer(ctx, mf.WRITE_ONLY, res.nbytes)
                
                # Use cached kernel if available, else get from program
                device_name = "NVIDIA" if self.nvidia_ctx else "Intel"
                kernel = getattr(self, f"{device_name.lower()}_kernel", None)
                if not kernel:
                    kernel = cl.Kernel(prg, "portfolio_kernel")
                    setattr(self, f"{device_name.lower()}_kernel", kernel)
                
                kernel(queue, (len(params),), None,
                    b_c, b_o, b_h, b_l, b_a, b_hr,
                    np.int32(len(c)), 
                    np.float32(self.initial_balance),
                    np.int32(self.optimization_phase),
                    b_p, b_res)
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
            return []
            
        combined_params = np.vstack(all_params)
        combined_results = np.concatenate(all_results)
        
        # Process Results
        r = combined_results.reshape(len(combined_params), 6)
        df_res = pd.DataFrame(combined_params, columns=[f'P{k}' for k in range(40)])
        df_res['NetProfit'] = r[:, 0]
        df_res['Trades'] = r[:, 1]
        df_res['Wins'] = r[:, 2]
        df_res['MaxDD'] = r[:, 3]
        df_res['TotalMFE'] = r[:, 4]
        df_res['TotalMAE'] = r[:, 5]
        
        df_res['Fitness'] = df_res.apply(self.calculate_ultra_robust_fitness, axis=1)
        df_res.sort_values('Fitness', ascending=False, inplace=True)
        
        # Return TOP N candidates
        candidates = []
        for i in range(min(top_n, len(df_res))):
            best = df_res.iloc[i]
            if best['Fitness'] <= -999000: continue
            
            raw_p = best[[f'P{k}' for k in range(40)]].values.astype(np.float32)
            
            candidates.append({
                'scalper': {
                    'rsi_period': best['P0'], 'rsi_buy': best['P1'], 'rsi_sell': best['P2'],
                    'atr_min': best['P3'], 'atr_max': best['P4'], 'adx_min': best['P5'],
                    'hour_start': best['P6'], 'hour_end': best['P7'],
                    'tp': best['P8'], 'sl': best['P9'], 'body_min': best['P10'],
                    'max_spread': best['P11'], 'flat_pips': best['P12']
                },
                'breakout': {
                    'bb_period': best['P15'], 'dev': best['P16'], 
                    'min_w': best['P17'], 'max_w': best['P18'],
                    'rsi_thresh': best['P19'], 'ema_period': best['P20'],
                    'body_min': best['P21'], 'atr_min': best['P22'],
                    'tp': best['P23'], 'sl': best['P24'],
                    'max_spread': best['P25'], 'flat_pips': best['P26']
                },
                'pullback': {
                    'fast': best['P27'], 'slow': best['P28'],
                    'rsi_buy': best['P29'], 'rsi_sell': best['P30'],
                    'adx_min': best['P31'], 'atr_min': best['P32'],
                    'tp': best['P33'], 'sl': best['P34'],
                    'max_spread': best['P35'], 'flat_pips': best['P36']
                },
                'risk': 0.02,
                'score': best['Fitness'],
                'profit': best['NetProfit'],
                'raw': raw_p
            })
        
        return candidates
    
    def _test_single_params(self, df, params):
        """Test a single parameter set on validation data"""
        # Convert params dict to array format (40 floats)
        p_arr = np.zeros(40, dtype=np.float32)
        
        # Scalper
        s = params['scalper']
        p_arr[0] = s['rsi_period']; p_arr[1] = s['rsi_buy']; p_arr[2] = s['rsi_sell']
        p_arr[3] = s['atr_min']; p_arr[4] = s['atr_max']; p_arr[5] = s['adx_min']
        p_arr[6] = s['hour_start']; p_arr[7] = s['hour_end']
        p_arr[8] = s['tp']; p_arr[9] = s['sl']; p_arr[10] = s['body_min']
        
        # Breakout
        b = params['breakout']
        p_arr[15] = b['bb_period']; p_arr[16] = b['dev']
        p_arr[17] = b['min_w']; p_arr[18] = b['max_w']
        p_arr[19] = b['rsi_thresh']; p_arr[20] = b['ema_period']
        p_arr[21] = b['body_min']; p_arr[22] = b['atr_min']
        p_arr[23] = b['tp']; p_arr[24] = b['sl']
        
        # Pullback
        p = params['pullback']
        p_arr[27] = p['fast']; p_arr[28] = p['slow']
        p_arr[29] = p['rsi_buy']; p_arr[30] = p['rsi_sell']
        p_arr[31] = p['adx_min']; p_arr[32] = p['atr_min']
        p_arr[33] = p['tp']; p_arr[34] = p['sl']
        
        param_array = p_arr.reshape(1, -1)
        
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
        
        res = np.zeros(6, dtype=np.float32)
        b_res = cl.Buffer(ctx, mf.WRITE_ONLY, res.nbytes)
        
        # Use cached kernel if available, else get from program
        device_name = "NVIDIA" if self.nvidia_ctx else "Intel"
        kernel = getattr(self, f"{device_name.lower()}_kernel", None)
        if not kernel:
            kernel = cl.Kernel(prg, "portfolio_kernel")
            setattr(self, f"{device_name.lower()}_kernel", kernel)
        
        kernel(queue, (1,), None,
            b_c, b_o, b_h, b_l, b_a, b_hr,
            np.int32(len(c)), 
            np.float32(self.initial_balance),
            np.int32(self.optimization_phase),
            b_p, b_res)
        queue.finish()
        cl.enqueue_copy(queue, res, b_res)
        
        # Calculate fitness
        result_df = pd.DataFrame({
            'NetProfit': [res[0]],
            'Trades': [res[1]],
            'Wins': [res[2]],
            'MaxDD': [res[3]],
            'TotalMFE': [res[4]],
            'TotalMAE': [res[5]]
        })
        
        fitness = self.calculate_ultra_robust_fitness(result_df.iloc[0])
        
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
    def __init__(self, initial_balance=50.0):
        self.initial_balance = initial_balance
        self.cpu = CPUEngine(DEFAULT_PARAMS)
        self.gpu = GPUEngine(initial_balance=initial_balance)  # Pass balance to GPU
        
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
        df_m1 = manager.get_data(source=DATA_SOURCE, symbol=SELECTED_SYMBOL, auto_update=True)
        
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
    print(f"⏰ Timeframe: {SELECTED_TIMEFRAME}")
    
    # Use working capital from launcher
    working_capital = WORKING_CAPITAL
    print(f"💰 Working Capital: ${working_capital:.2f}")
    print(f"🎯 Risk: {RISK_PER_TRADE*100:.1f}% per trade")
    print(f"🏆 Daily Goal: ${DAILY_PROFIT_GOAL:.2f} | Max Loss: ${MAX_DAILY_LOSS:.2f}")
    print("="*50)
    
    # Initialize trader with working capital
    trader = HybridTrader(initial_balance=working_capital)
    trader.initialize_with_history()  # Pre-flight check

    client = DerivClient(token=API_TOKEN)
    
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
                # User-friendly progress
                progress = len(m1_buffer) + 1
                print(f"\r💵 Price: {price:.2f} | ⏳ Forming M15 Candle: {progress}/15 min", end="")

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
