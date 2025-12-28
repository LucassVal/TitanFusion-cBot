# =============================================================================
#  TITAN FUSION QUANTUM BRAIN v3.0 (ANTIGRAVITY ENGINE)
#  Arquitetura: Híbrida (Python Analysis -> JSON Bridge -> cTrader Execution)
#  Foco: Padrões Institucionais (SMC, Wyckoff, Fluxo) & Multi-Timeframe
# =============================================================================

import json
import time
import requests
import pandas as pd
import numpy as np
import os
import random
from datetime import datetime
from tp_sl_validator import validate_and_cap_targets

# --- CONFIGURAÇÃO ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCWyaHwLI3zeUsKNJlSmiHt3dA4Nz88Hzw")
# Remover URL fixa, vamos usar dinâmica
# GEMINI_URL = ...

# Paths (Titan Fusion Quantum)
DATA_FOLDER = r"C:\Users\Lucas Valério\Documents\TitanFusionAI"
SCAN_INTERVAL = 60 # Seconds between scans (AI Throttle: 1 call per minute)
CONFIDENCE_THRESHOLD = 75 # Only trade if AI has 75%+ confidence

# Signal Duplicate Prevention Cache
# Format: {"SYMBOL": {"direction": "BUY", "timestamp": datetime}}
LAST_SIGNALS = {}

# =============================================================================
# 1. MOTOR DE ANÁLISE TÉCNICA (O "QUANT SCANNER")
# =============================================================================

def detectar_padroes_institucionais(df, tf_name):
    """
    O CORAÇÃO DO SISTEMA: Detecta os 13 Padrões de Elite em um DataFrame.
    Retorna um dicionário com flags (True/False/Direction).
    """
    if df is None or len(df) < 50: return {}
    
    # Prepara dados recentes
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    # prev2 = df.iloc[-3] (Usado se precisar de mais contexto)
    
    # Indicadores Auxiliares
    sma20 = df['Close'].rolling(20).mean().iloc[-1]
    std20 = df['Close'].rolling(20).std().iloc[-1]
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1] if 'Volume' in df else 0
    
    # Topos e Fundos Recentes (últimos 20 candles)
    recent_high = df['High'].iloc[-20:-2].max()
    recent_low = df['Low'].iloc[-20:-2].min()

    # --- TIER S: OS PADRÕES MESTRES (Estrutura) ---

    # 1. LIQUIDITY SWEEP (Turtle Soup)
    # Preço rompeu máxima recente mas fechou abaixo (armadilha de touros)
    sweep_bear = (curr['High'] > recent_high) and (curr['Close'] < recent_high)
    sweep_bull = (curr['Low'] < recent_low) and (curr['Close'] > recent_low)

    # 2. FAIR VALUE GAP (FVG) - Imbalance
    # Gap entre o pavio da vela -1 (curr) e -3 (prev2) não preenchido pela vela -2 (prev)
    vela_1 = df.iloc[-4] # Vela anterior ao movimento
    vela_2 = df.iloc[-3] # Vela do movimento forte
    vela_3 = df.iloc[-2] # Vela seguinte (que pode preencher)
    
    # FVG Bullish: Máxima da vela 1 < Mínima da vela 3
    # FVG Bearish: Mínima da vela 1 > Máxima da vela 3
    fvg_bull = (vela_1['High'] < vela_3['Low']) and (vela_2['Close'] > vela_2['Open'])
    fvg_bear = (vela_1['Low'] > vela_3['High']) and (vela_2['Close'] < vela_2['Open'])

    # 3. CHoCH (Change of Character) - Mudança de Tendência
    # Rompimento confirmado do último pivô. Usamos Donchian simplificado.
    choch_bull = (curr['Close'] > recent_high) and (prev['Close'] <= recent_high)
    choch_bear = (curr['Close'] < recent_low) and (prev['Close'] >= recent_low)

    # 4. WYCKOFF SPRING (Mola)
    # Lateralização estreita seguida de rompimento falso do fundo
    range_height = recent_high - recent_low
    is_ranging = range_height < (curr['Close'] * 0.005) # Range < 0.5%
    wyckoff_spring = is_ranging and sweep_bull

    # --- TIER A: MOMENTUM E FLUXO ---

    # 5. ORDER BLOCK (OB)
    # Última vela contrária antes de um movimento forte
    ob_bull = (prev['Close'] < prev['Open']) and (curr['Close'] > prev['High']) 
    ob_bear = (prev['Close'] > prev['Open']) and (curr['Close'] < prev['Low'])

    # 6. ABSORPTION (Volume)
    # Volume 2x a média mas corpo pequeno (Doji)
    body_size = abs(curr['Close'] - curr['Open'])
    avg_body = abs(df['Close'] - df['Open']).rolling(20).mean().iloc[-1]
    absorption = (curr['Volume'] > 2.0 * avg_vol) and (body_size < 0.5 * avg_body) if avg_vol > 0 else False

    # 7. BREAKOUT (Volatility)
    # Rompimento de Bollinger Superior com Volume
    bb_upper = sma20 + (2 * std20)
    bb_lower = sma20 - (2 * std20)
    breakout_bull = (curr['Close'] > bb_upper) and (curr['Volume'] > 1.5 * avg_vol if avg_vol > 0 else True)
    breakout_bear = (curr['Close'] < bb_lower) and (curr['Volume'] > 1.5 * avg_vol if avg_vol > 0 else True)

    # --- TIER B: GATILHOS CLÁSSICOS ---

    # 8. PULLBACK (Retração)
    # Toque na SMA20 em tendência
    pullback_bull = (curr['Close'] > sma20) and (curr['Low'] <= sma20 * 1.001) and (curr['Close'] > curr['Open'])
    pullback_bear = (curr['Close'] < sma20) and (curr['High'] >= sma20 * 0.999) and (curr['Close'] < curr['Open'])

    # 9. ENGULFING (Engolfo)
    engulfing_bull = (curr['Close'] > curr['Open']) and (prev['Close'] < prev['Open']) and (curr['Close'] > prev['Open']) and (curr['Open'] < prev['Close'])
    engulfing_bear = (curr['Close'] < curr['Open']) and (prev['Close'] > prev['Open']) and (curr['Close'] < prev['Open']) and (curr['Open'] > prev['Close'])

    # 10. MEAN REVERSION (Sobrecomprado/Vendido)
    # Preço longe da média (2.5 desvios padrão)
    if std20 > 0:
        dist_sigma = (curr['Close'] - sma20) / std20
        reversion_short = dist_sigma > 2.5 # Vender
        reversion_long = dist_sigma < -2.5 # Comprar
    else:
        reversion_short = False
        reversion_long = False

    # 11. INSIDE BAR (Consolidation)
    inside_bar = (curr['High'] < prev['High']) and (curr['Low'] > prev['Low'])

    # 12. PINBAR (Hammer/Shooting Star)
    # Pavio condizente com reversão
    upper_shadow = curr['High'] - max(curr['Close'], curr['Open'])
    lower_shadow = min(curr['Close'], curr['Open']) - curr['Low']
    body = abs(curr['Close'] - curr['Open'])
    
    pinbar_bull = (lower_shadow > 2 * body) and (upper_shadow < body)
    pinbar_bear = (upper_shadow > 2 * body) and (lower_shadow < body)

    # 13. THREE SOLDIERS (Momentum Continuation)
    # 3 velas da mesma cor sequenciais
    bull_3 = (curr['Close'] > curr['Open']) and (prev['Close'] > prev['Open']) and (df.iloc[-3]['Close'] > df.iloc[-3]['Open'])
    bear_3 = (curr['Close'] < curr['Open']) and (prev['Close'] < prev['Open']) and (df.iloc[-3]['Close'] < df.iloc[-3]['Open'])

    # Retorna o Relatório Deste Timeframe
    return {
        "TF": tf_name,
        "PRICE": curr['Close'],
        "S_SWEEP": "BULL" if sweep_bull else "BEAR" if sweep_bear else None,
        "S_FVG": "BULL" if fvg_bull else "BEAR" if fvg_bear else None,
        "S_CHOCH": "BULL" if choch_bull else "BEAR" if choch_bear else None,
        "S_WYCKOFF": wyckoff_spring,
        "A_ORDER_BLOCK": "BULL" if ob_bull else "BEAR" if ob_bear else None,
        "A_ABSORPTION": absorption,
        "A_BREAKOUT": "BULL" if breakout_bull else "BEAR" if breakout_bear else None,
        "A_MOMENTUM_3": "BULL" if bull_3 else "BEAR" if bear_3 else None,
        "B_PULLBACK": "BULL" if pullback_bull else "BEAR" if pullback_bear else None,
        "B_ENGULFING": "BULL" if engulfing_bull else "BEAR" if engulfing_bear else None,
        "B_REVERSION": "LONG" if reversion_long else "SHORT" if reversion_short else None,
        "B_INSIDE_BAR": inside_bar,
        "B_PINBAR": "BULL" if pinbar_bull else "BEAR" if pinbar_bear else None
    }

# =============================================================================
# 1.1 AUXILIARY ENGINE: MARKET STRUCTURE (L1+ HEAVY)
# =============================================================================

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=period).mean()

def analyze_market_structure(df):
    """
    Local High-Performance Processing (10+ Indicators).
    Generates a full 'Bio-Scan' of the asset for the AI.
    """
    if df is None or len(df) < 50: return {}
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    vol = df['Volume']
    
    # 1. TREND (Triple Screen EMA)
    ema20 = close.ewm(span=20).mean().iloc[-1]
    ema50 = close.ewm(span=50).mean().iloc[-1]
    ema200 = close.ewm(span=200).mean().iloc[-1]
    
    # MACD (12, 26, 9)
    k = close.ewm(span=12, adjust=False, min_periods=12).mean()
    d = close.ewm(span=26, adjust=False, min_periods=26).mean()
    macd = k - d
    signal = macd.ewm(span=9, adjust=False, min_periods=9).mean()
    macd_val = macd.iloc[-1]
    sig_val = signal.iloc[-1]
    
    trend_score = 0
    if close.iloc[-1] > ema20: trend_score += 1
    if close.iloc[-1] > ema50: trend_score += 1
    if close.iloc[-1] > ema200: trend_score += 2 # Higher weight
    if macd_val > sig_val: trend_score += 1
    
    trend_status = "NEUTRAL"
    if trend_score >= 4: trend_status = "STRONG_BULLISH 🚀"
    elif trend_score <= 1: trend_status = "STRONG_BEARISH 🔻"
    
    # 2. MOMENTUM (RSI + Stoch)
    rsi = calculate_rsi(close).iloc[-1]
    stoch_k = 100 * ((close - low.rolling(14).min()) / (high.rolling(14).max() - low.rolling(14).min()))
    stoch_val = stoch_k.iloc[-1]
    
    # Williams %R
    wr = -100 * ((high.rolling(14).max() - close) / (high.rolling(14).max() - low.rolling(14).min()))
    wr_val = wr.iloc[-1]
    
    momentum = "NEUTRAL"
    if rsi > 70 or stoch_val > 80: momentum = "OVERBOUGHT (Risk of Reversal) ⚠️"
    elif rsi < 30 or stoch_val < 20: momentum = "OVERSOLD (Bounce Likely) ♻️"
    
    # 3. VOLATILITY (Bollinger Squeeze + ATR)
    atr = calculate_atr(df).iloc[-1]
    std = close.rolling(20).std().iloc[-1]
    sma = close.rolling(20).mean().iloc[-1]
    # Width = (Upper - Lower) / SMA
    bb_width = ((sma + 2*std) - (sma - 2*std)) / sma
    
    vol_status = "NORMAL"
    if bb_width < 0.002: vol_status = "SQUEEZE (Pending Explosion) 💣"
    elif bb_width > 0.015: vol_status = "HIGH_VOLATILITY ⚡"
    
    # 4. VOLUME & FLOW (OBV + VWAP Approx)
    # Estimated OBV
    obv_change = np.where(close > close.shift(1), vol, np.where(close < close.shift(1), -vol, 0))
    # Simple slope check
    obv_slope = pd.Series(obv_change).rolling(5).mean().iloc[-1]
    
    # Approx VWAP
    vwap_approx = (close * vol).cumsum() / vol.cumsum()
    vwap_val = vwap_approx.iloc[-1]
    
    flow = "NEUTRAL"
    if obv_slope > 0 and close.iloc[-1] > vwap_val: flow = "INSTITUTIONAL ACCUMULATION 🏦"
    elif obv_slope < 0 and close.iloc[-1] < vwap_val: flow = "INSTITUTIONAL DISTRIBUTION 📉"

    return {
        "trend_desc": trend_status,
        "momentum_desc": momentum,
        "vol_desc": vol_status,
        "flow_desc": flow,
        "indicators": {
            "RSI14": round(rsi, 1),
            "MACD": "Bull" if macd_val > sig_val else "Bear",
            "ATR": round(atr, 5),
            "BB_Width": round(bb_width, 4),
            "Stoch": round(stoch_val, 1),
            "WilliamsR": round(wr_val, 1)
        }
    }

def print_detailed_matrix(matrix, metadata):
    """Prints Full Scan Grid (All Patterns)"""
    print(f"    [L1 DNA]       Digits: {metadata.get('digits')} | Pip: {metadata.get('pip_size')} | MinVol: {metadata.get('volume_min')}")
    print("    [L1 Scan]      Pattern Status (13/13):")
    
    # S=Sweep, F=FVG, C=Choch, W=Wyckoff, OB=OrderBlock, Ab=Absorp, Br=Breakout
    # P=Pullback, E=Engulf, R=Reversion, I=Inside, Pi=Pinbar, 3S=3Soldiers
    
    tfs = ['M5', 'M15', 'M30', 'H1', 'H4']
    for tf in tfs:
        if tf in matrix:
            d = matrix[tf]
            
            # Helper para formatar o status
            def fmt(val):
                if val == "BULL" or val is True: return "🟢"
                if val == "BEAR": return "🔴"
                if val == "LONG": return "🔵"
                if val == "SHORT": return "🟠"
                return "__" # Neutro
                
            line = (
                f"S:{fmt(d.get('S_SWEEP'))} "
                f"F:{fmt(d.get('S_FVG'))} "
                f"C:{fmt(d.get('S_CHOCH'))} "
                f"W:{fmt(d.get('S_WYCKOFF'))} "
                f"OB:{fmt(d.get('A_ORDER_BLOCK'))} "
                f"Ab:{fmt(d.get('A_ABSORPTION'))} "
                f"Br:{fmt(d.get('A_BREAKOUT'))} "
                f"P:{fmt(d.get('B_PULLBACK'))} "
                f"E:{fmt(d.get('B_ENGULFING'))} "
                f"R:{fmt(d.get('B_REVERSION'))} "
                f"I:{fmt(d.get('B_INSIDE_BAR'))} "
                f"Pi:{fmt(d.get('B_PINBAR'))} "
                f"3S:{fmt(d.get('A_MOMENTUM_3'))}"
            )
            print(f"      - {tf:<3}: [{line}]")
    
    # L1+ Structure Log (Show Trend/Momentum/Volatility from H1)
    h1_structure = matrix.get('H1', {}).get('STRUCTURE', {})
    if h1_structure:
        print(f"    [L1+ Structure] Trend: {h1_structure.get('trend_desc', 'N/A')} | "
              f"Momentum: {h1_structure.get('momentum_desc', 'N/A')} | "
              f"Volatility: {h1_structure.get('vol_desc', 'N/A')} | "
              f"Flow: {h1_structure.get('flow_desc', 'N/A')}")

# =============================================================================
# L4 SUPERVISOR - INTELLIGENT ORDER MANAGEMENT
# =============================================================================

# L4 uses TIGHT % limits (minimize loss, secure quick profit)
L4_EMERGENCY_SL_PCT = 0.3  # 0.3% max risk for emergency SL
L4_BREAKEVEN_THRESHOLD_PCT = 0.15  # Move to BE when profit > 0.15%

def is_sl_improvement(current_sl, new_sl, entry, direction):
    """Returns True only if new_sl is better (closer to entry or equal)."""
    if current_sl == 0:
        return True  # Any SL is better than no SL
    
    if direction == "BUY":
        # For BUY: SL should increase (get closer to entry from below)
        return new_sl >= current_sl and new_sl <= entry
    else:
        # For SELL: SL should decrease (get closer to entry from above)
        return new_sl <= current_sl and new_sl >= entry

def calculate_emergency_sl(entry, direction, risk_pct=L4_EMERGENCY_SL_PCT):
    """Calculate emergency SL based on percentage (TIGHT - minimize loss)."""
    if direction == "BUY":
        return entry * (1 - risk_pct / 100)
    else:
        return entry * (1 + risk_pct / 100)

def l4_supervisor(active_positions, data_folder):
    """
    L4 SUPERVISOR: Intelligent position manager.
    - Analyzes each position independently
    - Auto-adjusts SL/TP using TIGHT % limits
    - NEVER closes positions (safety rule)
    """
    if not active_positions:
        print("    [L4 Mgmt]      No open orders.")
        return []
    
    print(f"\n    [L4 ORDER SUPERVISOR] Analyzing {len(active_positions)} positions...")
    commands = []
    
    for pos in active_positions:
        pos_id = pos.get('id', 0)
        symbol = pos.get('symbol', 'UNKNOWN')
        direction = pos.get('type', 'BUY')
        entry = float(pos.get('entry', 0))
        sl = float(pos.get('sl', 0))
        tp = float(pos.get('tp', 0))
        pnl = float(pos.get('pnl', 0))
        
        # Calculate profit % relative to entry
        profit_pct = (pnl / (entry * 100)) * 100 if entry > 0 else 0
        
        # Status indicator
        status = "🟢" if pnl > 0 else "🔴"
        
        print(f"      [{symbol}] Order #{pos_id} | {direction} | PnL: ${pnl:.2f} {status}")
        print(f"        Entry: {entry:.5f} | SL: {sl:.5f} | TP: {tp:.5f}")
        
        # === SMART ALERTS & AUTO-ACTIONS ===
        
        # 1. EMERGENCY: Missing SL (CRITICAL RISK)
        if sl == 0:
            emergency_sl = calculate_emergency_sl(entry, direction)
            print(f"        ⚠️ ALERT: NO SL! Auto-setting emergency SL at {emergency_sl:.5f} ({L4_EMERGENCY_SL_PCT}%)")
            commands.append({
                "position_id": pos_id,
                "action": "SET_SL",
                "value": emergency_sl,
                "reason": f"Emergency SL ({L4_EMERGENCY_SL_PCT}% from entry)"
            })
        
        # 2. BREAKEVEN: Lock profit when threshold reached
        elif pnl > 0 and profit_pct >= L4_BREAKEVEN_THRESHOLD_PCT:
            # Check if SL is not already at or better than entry
            should_move = False
            if direction == "BUY" and sl < entry:
                should_move = True
            elif direction == "SELL" and sl > entry:
                should_move = True
            
            if should_move:
                print(f"        💡 ACTION: Moving SL to breakeven @ {entry:.5f} (profit {profit_pct:.2f}%)")
                commands.append({
                    "position_id": pos_id,
                    "action": "BREAKEVEN",
                    "value": entry,
                    "reason": f"Lock profit at breakeven ({profit_pct:.2f}%)"
                })
        
        # 3. DANGER: Price approaching SL
        elif sl > 0:
            current_price = entry  # Simplified, should get from market data
            sl_distance_pct = abs(current_price - sl) / entry * 100
            if sl_distance_pct < 0.05:  # Within 0.05% of SL
                print(f"        🚨 DANGER: Price {sl_distance_pct:.3f}% from SL!")
    
    # Write commands to JSON for cBot to execute
    if commands:
        cmd_path = os.path.join(data_folder, "position_commands.json")
        with open(cmd_path, "w") as f:
            json.dump(commands, f, indent=2)
        print(f"    [L4] 📤 Sent {len(commands)} commands to cBot")
    
    return commands


# =============================================================================
# 1.1 UTILS: JOURNALING & CLEANUP
# =============================================================================

JOURNAL_FOLDER = os.path.join(DATA_FOLDER, "Journal")
REJECTED_FILE = os.path.join(DATA_FOLDER, "rejected_signals.json")

def log_rejected_signal(symbol, reason, confidence=0, direction="N/A"):
    """
    Log signals that were NOT executed (for validation analysis).
    Tracks: max positions, low confidence, duplicate blocks, etc.
    """
    try:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "direction": direction,
            "confidence": confidence,
            "reason": reason
        }
        
        # Read existing, append, write
        existing = []
        if os.path.exists(REJECTED_FILE):
            with open(REJECTED_FILE, "r") as f:
                existing = json.load(f)
        
        existing.append(entry)
        
        # Keep only last 200 entries
        if len(existing) > 200:
            existing = existing[-200:]
        
        with open(REJECTED_FILE, "w") as f:
            json.dump(existing, f, indent=2)
            
    except Exception as e:
        print(f"  [WARN] Could not log rejected signal: {e}")

def log_to_journal(signal_data, symbol):
    """Salva um resumo do sinal no Jornal (Histórico Permanente)"""
    if not os.path.exists(JOURNAL_FOLDER): os.makedirs(JOURNAL_FOLDER)
    
    today = datetime.now().strftime("%Y-%m-%d")
    journal_file = os.path.join(JOURNAL_FOLDER, f"trading_journal_{today}.txt")
    
    entry_line = (
        f"[{datetime.now().strftime('%H:%M:%S')}] {symbol} | "
        f"{signal_data.get('signal')} | {signal_data.get('best_strategy')} | "
        f"Conf: {signal_data.get('confidence')}% | "
        f"Entry: {signal_data.get('entry')} | TP: {signal_data.get('target1')}\n"
    )
    
    try:
        with open(journal_file, "a", encoding='utf-8') as f:
            f.write(entry_line)
    except Exception as e:
        print(f"⚠️ Error saving Journal: {e}")

def cleanup_old_files():
    """Cleans up old temp files (.tmp) to keep folder clean"""
    try:
        current_time = time.time()
        for root, dirs, files in os.walk(DATA_FOLDER):
            for file in files:
                if file.endswith(".tmp"):
                    file_path = os.path.join(root, file)
                    if (current_time - os.path.getmtime(file_path)) > 3600: # 1 Hora
                        os.remove(file_path)
    except Exception:
        pass

# =============================================================================
# 2. CARREGAMENTO DE DADOS (cTrader Bridge)
# =============================================================================

def detect_active_symbols():
    """Detecta pastas de símbolos em Documents/TitanFusionAI"""
    if not os.path.exists(DATA_FOLDER): return []
    active = []
    for item in os.listdir(DATA_FOLDER):
        path = os.path.join(DATA_FOLDER, item)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "symbol_config.json")):
            active.append(item)
    return active

def load_market_data_from_ctrader(symbol):
    """
    Lê o JSON exportado pelo cBot e reconstrói DataFrames para M5, M15, M30, H1, H4.
    """
    config_path = os.path.join(DATA_FOLDER, symbol, "symbol_config.json")
    if not os.path.exists(config_path): return None

    try:
        # Tenta ler (com retry simples para lock de arquivo)
        for _ in range(3):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                break
            except:
                time.sleep(0.1)
        else:
            return None

        # Helper para converter lista de candles em DataFrame
        def candles_to_df(candle_list):
            if not candle_list: return pd.DataFrame()
            df = pd.DataFrame(candle_list)
            # Mapear colunas do cBot para nomes padrão (se necessário)
            # O cBot exporta: open, high, low, close, volume (minúscula)
            # Vamos capitalizar para o Engine
            df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
            return df

        data_dict = {}
        data_dict['M5'] = candles_to_df(data.get('m5', []))
        data_dict['M15'] = candles_to_df(data.get('m15', []))
        data_dict['M30'] = candles_to_df(data.get('m30', []))
        data_dict['H1'] = candles_to_df(data.get('h1', []))
        data_dict['H4'] = candles_to_df(data.get('h4', [])) # Key H4 agora disponível

        # Preço atual para referência
        current_price = data.get('current_price', 0.0)
        
        # Sentiment Data (Broker Real Volume)
        sentiment = data.get('sentiment', {
            'buy_percent': 50.0, 'sell_percent': 50.0, 'bias': 'NEUTRAL'
        })
        
        # Portfolio Data (Awareness)
        active_pos = data.get('active_positions', [])
        
        # Metadata (Asset DNA)
        metadata = data.get('symbol_metadata', {})

        return data_dict, current_price, sentiment, active_pos, metadata

    except Exception as e:
        print(f"❌ Error reading data from {symbol}: {e}")
        return None, 0.0

# =============================================================================
# 3. A INTELIGÊNCIA (Gemini Flash 2.0 - Antigravity)
# =============================================================================

def detect_sentiment_divergence(sentiment, price_data):
    """Detecta divergências entre sentimento da multidão vs preço (Reversal Signs)"""
    # Simplificado para não depender de histórico complexo por enquanto, 
    # foca no snapshot atual vs bias
    
    buy_pct = sentiment.get('buy_percent', 50)
    # price_trend = ... (seria ideal ter trend, mas vamos pelo extremo)
    
    divergence_msg = ""
    
    # Crowd Heavily Buying (>75%) but Price is at Resistance/Falling? -> SELL Signal
    if buy_pct > 75:
        divergence_msg = "⚠️ CROWD EXTREME BUYING (>75%) -> Look for SHORT opportunities (Contrarian)."
    
    # Crowd Heavily Selling (<25%) but Price at Support? -> BUY Signal
    elif buy_pct < 25:
        divergence_msg = "⚠️ CROWD EXTREME SELLING (<25%) -> Look for LONG opportunities (Contrarian)."
        
    return divergence_msg

def consultar_gemini_antigravity(matrix_padroes, current_price, symbol, sentiment):
    """
    Envia a Matrix de Padrões para o Gemini decidir a estratégia.
    """
    report_txt = json.dumps(matrix_padroes, indent=2, default=str)
    
    # Detectar Divergência/Alerta
    sentiment_alert = detect_sentiment_divergence(sentiment, None)
    
    # CONTEXTO ESTRUTURAL (PRE-DIGERIDO PELO PYTHON)
    # Pega a estrutura do H1 (Timeframe âncora)
    structure_h1 = matrix_padroes.get('H1', {}).get('STRUCTURE', {})
    
    # LOG CAMADA 2
    if sentiment_alert:
        print(f"    [L2 Sentiment] 🚨 DIVERGENCE: {sentiment_alert}")
    else:
        print(f"    [L2 Sentiment] Neutral (Buy {sentiment['buy_percent']}% | Sell {sentiment['sell_percent']}%)")
    
    prompt = f"""
ROLE: You are the ANTIGRAVITY ENGINE v3.0, an elite quantitative trading system. 
Your goal is to identify HIGH PROBABILITY trades based on Institutional Patterns & Sentiment Analysis.

>>> INPUT DATA <<<
Symbol: {symbol}
Current Price: {current_price}
Market Sentiment (Broker): BUY {sentiment['buy_percent']}% | SELL {sentiment['sell_percent']}% ({sentiment['bias']})
SENTIMENT ALERT: {sentiment_alert}

>>> MARKET STRUCTURE (L1+ HEAVY ANALYSIS - 10 INDICES) <<<
Trend: {structure_h1.get('trend_desc', 'N/A')}
Momentum: {structure_h1.get('momentum_desc', 'N/A')}
Volatility: {structure_h1.get('vol_desc', 'N/A')}
Flow: {structure_h1.get('flow_desc', 'N/A')}
Key Metrics: {structure_h1.get('indicators', {})}

Active Patterns (Multi-Timeframe):
{report_txt}

>>> TRADING MODES & INDICATOR WEIGHTING (DYNAMIC) <<<
1. FAST SCALP (M5):
   - FOCUS: Stochastics, Williams%R, Bollinger Squeeze.
   - IGNORE: Triple EMA (Trend takes too long to form).
   - GOAL: Quick captures (<15 min).

2. MOMENTUM (H1):
   - FOCUS: MACD, OBV, Flow Score, Triple EMA.
   - IGNORE: RSI (RSI > 70 is GOOD in momentum).
   - GOAL: Ride the wave.

3. SWING (H4):
   - FOCUS: Structure (CHoCH), Volume Profile, Fundamental Bias.
   - GOAL: Major moves.

>>> CRITICAL RULES (Smart Filtering) <<<
1. **Context is King:** Do NOT demand 10/10 indicators green.
   - If Trend = STRONG_BULLISH, *ignore* "Overbought" oscillators. BUY dips.
   - If Volatility = SQUEEZE, expect a Breakout (ignore mean reversion).
2. **Sentiment Rule:**
   - If Crowd Buy > 75% -> Blocks BUYs (unless Scalp sell).
   - If Crowd Buy < 25% -> Blocks SELLs (unless Scalp buy).
3. **Quality > Quantity:** Better 1 perfect trade than 5 risky ones.
4. RISK MANAGEMENT (These are HARD LIMITS): 
   - FAST SCALP: Max SL 0.15% | TP 0.25%
   - SCALP: Max SL 0.30% | TP 0.50%
   - MOMENTUM: Max SL 0.8% | TP 1.5%
   - SWING: Max SL 1.5% | TP 3.0%

>>> DECISION OUTPUT FORMAT (JSON ONLY) <<<
{{
  "action": "APPROVE" or "WAIT",
  "strategy": "FAST_SCALP" / "SCALP" / "MOMENTUM" / "SWING",
  "direction": "BUY" or "SELL",
  "confidence": 0-100 (Threshold: 75),
  "entry": {current_price},
  "sl": (technical stop level),
  "tp1": (target level),
  "reason": "Concise technical reason"
}}
    """

    # Prepare prompt payload
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }

    # Lista de Modelos para tentar (Fallback System)
    models_to_try = [
        "gemini-2.0-flash-exp",    # 🏆 WINNER (Confirmed via Debug)
        "gemini-3-flash-preview",  # Experimental (User Request)
        "gemini-1.5-flash-latest", 
        "gemini-pro"
    ]
    
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        
        # PERSISTENCE LAYER: 3 Retries per Model
        for attempt in range(1, 4):
            try:
                # print(f"    [L3 AI] Connecting to {model} (Attempt {attempt}/3)...")
                response = requests.post(url, json=payload, timeout=25) # Aumentei timeout
                
                if response.status_code == 200:
                    # SUCESSO REAL!
                    txt = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                    txt = txt.replace("```json", "").replace("```", "").strip()
                    # print(f"    [L3 AI] ✅ Connected to {model}!")
                    return json.loads(txt)
                
                elif response.status_code == 404:
                    # Modelo incorreto, não adianta tentar de novo
                    print(f"    [L3 Debug] ⚠️ Model {model} not found (404). Skipping.")
                    break # Sai do retry loop, vai pro proximo modelo
                
                elif response.status_code == 429:
                    # Rate Limit, esperar e tentar de novo
                    print(f"    [L3 Debug] ⏳ Rate Limit ({model}). Retrying in 2s...")
                    time.sleep(2)
                    continue
                
                else:
                    # Erro genérico
                    print(f"    [L3 Debug] ❌ Error {response.status_code} on {model}: {response.text[:100]}")
                    # Tenta de novo se for 500/503, senão break? Vamos tentar.
                    time.sleep(1)
                    continue

            except Exception as e:
                # Erro de Conexão (Timeout, DNS, SSL)
                print(f"    [L3 Debug] 🔌 Connection Failed ({model}): {str(e)[:100]}")
                time.sleep(1)
                continue
            
    # Se chegou aqui, falhou TUDO (4 modelos x 3 tentativas = 12 failures)
    print(f"    [L3 Decision]  ❌ FATAL: AI Connection Lost. Checked {len(models_to_try)} models.")
    return None

# =============================================================================
# 4. PONTE COM CTRADER (JSON Bridge)
# =============================================================================

def escrever_sinal(decisao, symbol):
    global LAST_SIGNALS
    
    # Validar Confiança
    action = decisao.get('action', 'WAIT')
    conf = decisao.get('confidence', 0)
    strat = decisao.get('strategy', 'N/A')
    reason = decisao.get('reason', '')
    direction = decisao.get('direction', 'WAIT')
    
    if action != 'APPROVE' or conf < CONFIDENCE_THRESHOLD:
        print(f"    [L3 Decision]  ⛔ {action} ({strat}) | Conf: {conf}%")
        print(f"                   Reason: {reason}")
        return
    
    # --- DUPLICATE SIGNAL PREVENTION (SMART) ---
    # Only block if: (1) Same direction was sent recently AND (2) we're at max positions
    # This allows new signals if there's room for more positions
    COOLDOWN_MINUTES = 3  # Reduced from 5 to 3 minutes
    if symbol in LAST_SIGNALS:
        last = LAST_SIGNALS[symbol]
        elapsed = (datetime.now() - last['timestamp']).total_seconds() / 60
        # Only block if VERY recent (< 3 min) to avoid signal spam
        # If positions are still below max, we might want new entries
        if last['direction'] == direction and elapsed < COOLDOWN_MINUTES:
            print(f"    [L3 Decision]  ⏸️ DUPLICATE BLOCKED ({direction} already sent {elapsed:.1f} min ago)")
            log_rejected_signal(symbol, "DUPLICATE_RECENT", conf, direction)
            return
    
    # Update cache
    LAST_SIGNALS[symbol] = {'direction': direction, 'timestamp': datetime.now()}

    # --- CAMADA DE SEGURANÇA (RISK GUARD) ---
    # Impõe os limites matemáticos rígidos, independente da "opinião" da IA
    sl_raw = float(decisao.get('sl', 0))
    tp_raw = float(decisao.get('tp1', 0))
    entry_raw = float(decisao.get('entry', 0))
    strat_raw = decisao.get('strategy', 'SCALP')

    sl_safe, tp_safe, warnings = validate_and_cap_targets(
        strategy_name=strat_raw,
        sl_val=sl_raw,
        tp_val=tp_raw,
        entry_price=entry_raw,
        symbol=symbol
    )

    # Define Signal Validity based on Strategy Timeframe
    validity_min = 15 # Default
    timeframe = "M15"  # Default
    if "FAST" in strat_raw: 
        validity_min = 10
        timeframe = "M5"
    elif "SCALP" in strat_raw: 
        validity_min = 30
        timeframe = "M15"
    elif "MOMENTUM" in strat_raw: 
        validity_min = 60
        timeframe = "H1"
    elif "SWING" in strat_raw: 
        validity_min = 240 # 4 Hours
        timeframe = "H4"

    # Calculate Risk/Reward Ratio
    risk = abs(entry_raw - sl_safe)
    reward = abs(tp_safe - entry_raw)
    rr_ratio = reward / risk if risk > 0 else 0

    # Preparar Sinal Final
    sinal_final = {
        "status": "APPROVED",
        "signal_id": f"ANTIGRAVITY_{int(time.time())}",
        "best_strategy": f"{strat_raw} ({decisao.get('reason','Revisão IA')[:30]}...)",
        "signal": decisao['direction'], # BUY/SELL
        "confidence": decisao['confidence'],
        "timeframe": timeframe,
        "entry": entry_raw,
        "stop": sl_safe,       # Valor seguro
        "target1": tp_safe,    # Valor seguro
        "rr_ratio": round(rr_ratio, 2),
        "valid_for_minutes": validity_min,
        "valid_until": (datetime.now() + pd.Timedelta(minutes=validity_min)).strftime("%H:%M:%S"),
        "timestamp": datetime.now().isoformat()
    }
    
    if warnings:
        for w in warnings: print(f"  {w}")
        
    # LOG NO JORNAL (PERSISTÊNCIA)
    log_to_journal(sinal_final, symbol)

    # Escrita na pasta do Símbolo
    output_path = os.path.join(DATA_FOLDER, symbol, "predictions.json")
    temp = output_path + ".tmp"
    
    try:
        with open(temp, "w") as f:
            json.dump(sinal_final, f, indent=4)
        os.replace(temp, output_path)
        
        # Enhanced Signal Log (Telegram-Ready Format)
        print(f"\n  🚀 SIGNAL [{symbol}] {timeframe}")
        print(f"     📍 {strat_raw} {decisao['direction']} | Conf: {decisao['confidence']}%")
        print(f"     Entry: {entry_raw:.5f} | SL: {sl_safe:.5f} | TP: {tp_safe:.5f}")
        print(f"     ⏱️ Valid: {validity_min} min (until {sinal_final['valid_until']}) | R:R {rr_ratio:.1f}:1")
        print(f"     🆔 {sinal_final['signal_id']}")
    except Exception as e:
        print(f"❌ Error writing signal: {e}")

# =============================================================================
# MAIN LOOP
# =============================================================================

if __name__ == "__main__":
    if not os.path.exists(DATA_FOLDER): os.makedirs(DATA_FOLDER)
    print(f"🌌 TITAN FUSION - ANTIGRAVITY ENGINE V3.0 (ACTIVE)")
    print(f"📂 Data Bridge: {DATA_FOLDER}")
    print(f"🤖 AI: Gemini 2.0 Flash (Risk Guard Active)")
    
    while True:
        try:
            active_symbols = detect_active_symbols()
            if not active_symbols:
                print(f"[WAITING] No symbols detected in {DATA_FOLDER}...")
                time.sleep(5)
                continue
            
            print(f"\n⚡ Scan Cycle: {len(active_symbols)} assets found")
            
            for symbol in active_symbols:
                # 0. Manutenção (Cleanup)
                if random.random() < 0.05: cleanup_old_files()

                # 1. Obter Dados (cTrader)
                start_time = time.time()
                # Status Flags (L1-L4)
                ok_l1 = False # Technical
                ok_l2 = False # Sentiment
                ok_l3 = False # AI Brain
                ok_l4 = False # Order Mgmt
                
                data_dict, price, sentiment, active_pos, metadata = load_market_data_from_ctrader(symbol)
                
                # --- PORTFOLIO CHECK (OVEREXPOSURE GUARD) ---
                if len(active_pos) >= 3:
                     # Log rejected signal for validation tracking
                     log_rejected_signal(symbol, "MAX_POSITIONS", 0, "BLOCKED")
                     print(f"  [{symbol}] Max Positions ({len(active_pos)}) reached. Skipping AI.")
                     print(f"  [INTEGRITY] 🟡 Partial Cycle (Portfolio Full) | {time.time()-start_time:.2f}s")
                     continue
                
                if data_dict:
                    print(f"\n  🔍 ANALYZING {symbol}:")
                    # 2. Escanear Padrões
                    matrix_analise = {}
                    for tf, df in data_dict.items():
                        if not df.empty:
                            patterns = detectar_padroes_institucionais(df, tf)
                            # Injeta Análise Estrutural no Objeto
                            patterns['STRUCTURE'] = analyze_market_structure(df)
                            matrix_analise[tf] = patterns
                    
                    # LOG L1: Imprime TODOS os TFs detalhados e DNA
                    print_detailed_matrix(matrix_analise, metadata)
                    ok_l1 = True
                        
                    # 3. Inteligência Artificial
                    # (L2 Log is inside the function)
                    if sentiment: ok_l2 = True
                    decisao = consultar_gemini_antigravity(matrix_analise, price, symbol, sentiment)
                    
                    
                    # L4 SUPERVISOR: Intelligent Order Management
                    l4_supervisor(active_pos, DATA_FOLDER)
                    ok_l4 = True
                    
                    # 4. Execução (com Validação)
                    if decisao:
                        ok_l3 = True
                        escrever_sinal(decisao, symbol)
                    else:
                        print(f"    [L3 Decision]  ❌ FAILED (No AI Response/API Error)")
                    
                    # FINAL: INTEGRIDADE DO CICLO (SUPERVISOR)
                    elapsed = time.time() - start_time
                    if ok_l1 and ok_l2 and ok_l3 and ok_l4:
                        print(f"  [INTEGRITY] ✅ CYCLE VALIDATED (L1,L2,L3,L4 OK) | Latency: {elapsed:.2f}s")
                    else:
                        print(f"  [INTEGRITY] ⚠️ FAILED : L1:{ok_l1} L2:{ok_l2} L3:{ok_l3} L4:{ok_l4}")
            
            time.sleep(SCAN_INTERVAL)

        except KeyboardInterrupt:
            print("\n🛑 System stopped by user.")
            break
        except Exception as e:
            print(f"⚠️ Main loop error: {e}")
            time.sleep(10)
    
    # ========================================
    # ON-EXIT: Generate Validation Report
    # ========================================
    print("\n" + "=" * 50)
    print("  📊 GENERATING SESSION VALIDATION REPORT...")
    print("=" * 50)
    
    try:
        from signal_validator import main as run_validator
        run_validator()
    except ImportError:
        print("  ⚠️ Signal validator not found. Skipping report.")
    except Exception as e:
        print(f"  ⚠️ Validation error: {e}")
    
    print("\n✅ Session ended. Reports saved to TitanFusionAI/Reports/")
