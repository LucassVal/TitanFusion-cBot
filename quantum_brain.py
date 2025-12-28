# Gold Emperor QUANTUM - Enhanced with Win/Loss Tracking
# Atomic writes + Signal expiration + Performance history

import json
import time
import requests
from datetime import datetime, timedelta
import os
import random
from symbol_metadata_cache import load_or_create_metadata, get_gemini_context_string
from tp_sl_validator import validate_and_cap_targets

# =============================================================================
# CONFIGURACAO
# =============================================================================
# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# Pasta onde o cTrader Bot exporta os dados
DATA_FOLDER = r"C:\Users\Lucas Valério\Documents\TitanFusionAI"
OUTPUT_FILE = os.path.join(DATA_FOLDER, "predictions.json")
SYMBOL_CONFIG = os.path.join(DATA_FOLDER, "symbol_config.json")
HISTORY_FILE = os.path.join(DATA_FOLDER, "signal_history.json")

UPDATE_INTERVAL = 60  # Segundos
MIN_CONFIDENCE = 70   # Minimo para aprovar
SIGNAL_TIMEOUT_MIN = 120  # Expiracao de sinal em minutos

# =============================================================================
# FUNCOES AUXILIARES
# =============================================================================
def ensure_folder():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

def detect_active_symbols():
    """
    Detecta símbolos ativos escaneando subpastas em GoldEmperorAI/
    Retorna lista de símbolos que têm symbol_config.json válido
    
    COMPATIBILIDADE: Suporta formato antigo (arquivo na raiz) e novo (subfolders)
    """
    if not os.path.exists(DATA_FOLDER):
        return []
    
    active_symbols = []
    
    try:
        # NOVO: Checar subfolders (multi-symbol)
        # print(f"DEBUG: Escaneando {DATA_FOLDER}")
        for item in os.listdir(DATA_FOLDER):
            symbol_path = os.path.join(DATA_FOLDER, item)
            if os.path.isdir(symbol_path):
                config_file = os.path.join(symbol_path, "symbol_config.json")
                if os.path.exists(config_file):
                    # Checkagem de tempo (FILTRO ANTI-FANTASMA)
                    try:
                        mod_time = os.path.getmtime(config_file)
                        age_min = (time.time() - mod_time) / 60
                        
                        if age_min < 30: 
                             active_symbols.append(item)
                    except:
                        pass
        
        # FALLBACK REMOVIDO: O XRPUSD Zumbi vinha daqui.
        # Agora só confiamos nas pastas com timestamps recentes.

        # FALLBACK: Formato antigo (symbol_config.json na raiz)
        if not active_symbols:
            legacy_config = os.path.join(DATA_FOLDER, "symbol_config.json")
            if os.path.exists(legacy_config):
                # Ler símbolo do arquivo
                try:
                    with open(legacy_config, 'r') as f:
                        data = json.load(f)
                        symbol = data.get('symbol', data.get('symbol_ctrader', 'UNKNOWN'))
                        if symbol and symbol != 'UNKNOWN':
                            active_symbols.append(symbol)
                except:
                    pass
                    
    except Exception as e:
        print(f"[ERRO] Falha ao detectar símbolos: {e}")
    
    return active_symbols

def get_symbol_folder(symbol):
    """Retorna pasta específica do símbolo"""
    folder = os.path.join(DATA_FOLDER, symbol)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def atomic_write(filepath, data):
    """Escrita atomica: cria .tmp e renomeia para evitar leitura parcial"""
    temp_file = filepath + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, filepath)
        return True
    except Exception as e:
        print(f"  Erro escrita atomica: {e}")
        return False

# Carrega dados reais do cTrader
def load_ctrader_data(symbol=None):
    """Carrega dados exportados pelo cBot do símbolo específico
    COMPATIBILIDADE: Suporta formato subfolder e flat"""
    if not symbol:
        # Fallback: tenta detectar símbolo único
        symbols = detect_active_symbols()
        if len(symbols) == 1:
            symbol = symbols[0]
        else:
            return None
    
    try:
        # NOVO: Tentar carregar de subfolder
        symbol_folder = os.path.join(DATA_FOLDER, symbol)
        config_file = os.path.join(symbol_folder, "symbol_config.json")
        
        # FALLBACK 2: candles.json na raiz
        if not os.path.exists(config_file):
            config_file = os.path.join(DATA_FOLDER, "candles.json")
            
        if not os.path.exists(config_file):
            return None
            
        with open(config_file, 'r') as f:
            data = json.load(f)
            # Verificar se é o simbolo certo
            file_symbol = data.get('symbol', data.get('symbol_ctrader', 'UNKNOWN'))
            
            # DEBUG
            # print(f"DEBUG LOAD {symbol}: FileSymbol={file_symbol} Path={config_file}")
            # print(f"KEYS: {list(data.keys())[:10]}")  # Primeiras 10 chaves
            
            if file_symbol != symbol and symbol_folder != DATA_FOLDER:
                # Permite correspondencia parcial se for o unico arquivo na pasta (ex: FETUSD vs FET)
                if symbol in file_symbol or file_symbol in symbol:
                    pass
                else:
                    print(f"  [AVISO] {symbol}: JSON tem símbolo incorreto '{file_symbol}'")
                    return None 
                
            data['symbol'] = file_symbol
            return data
    except Exception as e:
        print(f"  [ERRO] Load CTRADER {symbol}: {e}")
        return None

def load_signal_history(symbol):
    """Carrega historico de sinais do símbolo específico
    Cada símbolo TEM seu próprio histórico isolado"""
    try:
        # Carregar APENAS do subfolder do símbolo
        symbol_folder = os.path.join(DATA_FOLDER, symbol)
        history_file = os.path.join(symbol_folder, "signal_history.json")
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return json.load(f)
    except:
        pass
    
    # Se não existir, retorna histórico vazio (não buscar de outro lugar!)
    return {"signals": [], "stats": {"total": 0, "wins": 0, "losses": 0, "pending": 0, "expired": 0}}

# FIX Issue #5: Implementar storage de histórico de sentimento
def load_sentiment_history(symbol):
    """Carrega histórico de sentimento do símbolo (últimos 20 valores)"""
    try:
        symbol_folder = os.path.join(DATA_FOLDER, symbol)
        history_file = os.path.join(symbol_folder, "sentiment_history.json")
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return json.load(f)
    except:
        pass
    
    return {"buy_percent_history": [], "price_history": []}

def save_sentiment_history(symbol, buy_percent, price):
    """Salva valor atual de sentimento no histórico (máximo 20 valores)"""
    try:
        history = load_sentiment_history(symbol)
        
        history["buy_percent_history"].append(buy_percent)
        history["price_history"].append(price)
        
        # Manter apenas últimos 20
        if len(history["buy_percent_history"]) > 20:
            history["buy_percent_history"] = history["buy_percent_history"][-20:]
            history["price_history"] = history["price_history"][-20:]
        
        symbol_folder = os.path.join(DATA_FOLDER, symbol)
        os.makedirs(symbol_folder, exist_ok=True)
        history_file = os.path.join(symbol_folder, "sentiment_history.json")
        
        atomic_write(history_file, history) # Corrected: pass history_file and history
    except Exception as e:
        print(f"  [WARN] Erro salvando histórico de sentimento: {e}")

def save_signal_history(history, symbol):
    """Salva historico de sinais do símbolo específico"""
    symbol_folder = get_symbol_folder(symbol)
    history_file = os.path.join(symbol_folder, "signal_history.json")
    return atomic_write(history_file, history)

def check_signal_results(history, current_price):
    """Verifica sinais pendentes e atualiza win/loss"""
    updated = False
    
    for signal in history.get("signals", []):
        if signal.get("status") != "PENDING":
            continue
        
        entry = signal.get("entry", 0)
        tp1 = signal.get("tp1", 0)
        sl = signal.get("sl", 0)
        direction = signal.get("direction", "")
        created_at = signal.get("created_at", "")
        expires_at = signal.get("expires_at", "")
        
        # Verificar expiracao
        try:
            exp_time = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
            if datetime.now() > exp_time:
                signal["status"] = "EXPIRED"
                signal["result_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                history["stats"]["expired"] = history["stats"].get("expired", 0) + 1
                history["stats"]["pending"] = max(0, history["stats"].get("pending", 0) - 1)
                updated = True
                print(f"  EXPIRADO: {signal['signal_id']}")
                continue
        except:
            pass
        
        # Verificar Win/Loss baseado no preco atual
        if direction == "BUY":
            if current_price >= tp1:
                signal["status"] = "WIN"
                signal["result_price"] = current_price
                signal["result_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                signal["pips_result"] = round((tp1 - entry) * 10, 1)
                history["stats"]["wins"] = history["stats"].get("wins", 0) + 1
                history["stats"]["pending"] = max(0, history["stats"].get("pending", 0) - 1)
                updated = True
                print(f"  WIN! {signal['signal_id']} +{signal['pips_result']} pips")
            elif current_price <= sl:
                signal["status"] = "LOSS"
                signal["result_price"] = current_price
                signal["result_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                signal["pips_result"] = round((sl - entry) * 10, 1)
                history["stats"]["losses"] = history["stats"].get("losses", 0) + 1
                history["stats"]["pending"] = max(0, history["stats"].get("pending", 0) - 1)
                updated = True
                print(f"  LOSS: {signal['signal_id']} {signal['pips_result']} pips")
        
        elif direction == "SELL":
            if current_price <= tp1:
                signal["status"] = "WIN"
                signal["result_price"] = current_price
                signal["result_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                signal["pips_result"] = round((entry - tp1) * 10, 1)
                history["stats"]["wins"] = history["stats"].get("wins", 0) + 1
                history["stats"]["pending"] = max(0, history["stats"].get("pending", 0) - 1)
                updated = True
                print(f"  WIN! {signal['signal_id']} +{signal['pips_result']} pips")
            elif current_price >= sl:
                signal["status"] = "LOSS"
                signal["result_price"] = current_price
                signal["result_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                signal["pips_result"] = round((entry - sl) * 10, 1)
                history["stats"]["losses"] = history["stats"].get("losses", 0) + 1
                history["stats"]["pending"] = max(0, history["stats"].get("pending", 0) - 1)
                updated = True
                print(f"  LOSS: {signal['signal_id']} {signal['pips_result']} pips")
    
    return updated

# =============================================================================
# CAMADA 1: DADOS REAIS - Deriv API (Preferencial) + Yahoo Finance (Fallback)
# =============================================================================
import websocket
import ssl

# Deriv API Config
DERIV_APP_ID = "1089"  # App ID publico para testes
DERIV_WS_URL = f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}"

def get_deriv_symbol(symbol):
    """Converte simbolo cTrader para Deriv"""
    mappings = {
        "XAUUSD": "frxXAUUSD",
        "EURUSD": "frxEURUSD",
        "GBPUSD": "frxGBPUSD",
        "USDJPY": "frxUSDJPY",
        "BTCUSD": "cryBTCUSD",
        "ETHUSD": "cryETHUSD",
        "XRPUSD": "cryXRPUSD",
        "LTCUSD": "cryLTCUSD",
        "SOLUSD": "SOLUSD",  # Pode nao existir na Deriv
    }
    for key, val in mappings.items():
        if key in symbol.upper():
            return val
    return symbol

def fetch_deriv_candles(symbol, granularity=900, count=50):
    """
    Busca candles reais da Deriv API
    granularity: 60=1min, 300=5min, 900=15min, 3600=1h, 14400=4h, 86400=1d
    """
    if DERIV_APP_ID is None: return None
    
    deriv_symbol = get_deriv_symbol(symbol)
    print(f"   Buscando {count} candles de {deriv_symbol} (granularity={granularity}s)...")
    
    try:
        import json
        ws = websocket.create_connection(
            DERIV_WS_URL,
            sslopt={"cert_reqs": ssl.CERT_NONE}
        )
        
        # Request candles
        request = {
            "ticks_history": deriv_symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "granularity": granularity,
            "style": "candles"
        }
        
        ws.send(json.dumps(request))
        response = json.loads(ws.recv())
        ws.close()
        
        if "error" in response:
            print(f"   ! Deriv erro: {response['error'].get('message', 'Unknown')}")
            return None
        
        candles = response.get("candles", [])
        if not candles:
            print(f"   ! Sem candles para {deriv_symbol}")
            return None
        
        print(f"   [DERIV] {len(candles)} candles recebidos!")
        
        # Converter para DataFrame
        import pandas as pd
        df = pd.DataFrame(candles)
        df['epoch'] = pd.to_datetime(df['epoch'], unit='s')
        df.set_index('epoch', inplace=True)
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
        
        return df
        
    except Exception as e:
        print(f"   ! Deriv conexao falhou: {e}")
        return None

def fetch_deriv_multi_tf(symbol):
    """Busca dados de multiplos timeframes da Deriv - FAIL FAST se simbolo invalido"""
    data = {}
    symbol_invalid = False
    
    # M1=60, M5=300, M15=900, M30=1800, H1=3600, H4=14400
    timeframes = {
        "M1": 60,
        "M5": 300,
        "M15": 900,
        "M30": 1800,
        "H1": 3600,
        "H4": 14400
    }
    
    for tf_name, granularity in timeframes.items():
        # FAIL FAST: se simbolo ja foi marcado como invalido, pular
        if symbol_invalid:
            break
            
        df = fetch_deriv_candles(symbol, granularity=granularity, count=100)
        if df is not None:
            data[tf_name] = df
        else:
            # Verificar se erro foi "symbol invalid" - se sim, parar de tentar
            symbol_invalid = True
            print(f"   -> Simbolo nao existe na Deriv, pulando para Yahoo...")
            break
    
    return data if data else None

# Yahoo Finance como fallback
try:
    import yfinance as yf
    import pandas as pd
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("! yfinance nao instalado. Execute: pip install yfinance")

def get_yahoo_ticker(symbol):
    """Converte simbolo cTrader para Yahoo Finance"""
    mappings = {
        "XAUUSD": "GC=F",      # Gold Futures
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X", 
        "USDJPY": "JPY=X",
        "BTCUSD": "BTC-USD",
        "ETHUSD": "ETH-USD",
        "XRPUSD": "XRP-USD",
        "LTCUSD": "LTC-USD",
        "SOLUSD": "SOL-USD",
    }
    # Tentar match direto ou parcial
    for key, val in mappings.items():
        if key in symbol.upper():
            return val
    # Se nao encontrar, tentar formato padrao
    if len(symbol) == 6:
        return f"{symbol[:3]}{symbol[3:]}=X"
    return symbol

def fetch_real_data(symbol):
    """Baixa dados reais do Yahoo Finance"""
    if not YFINANCE_AVAILABLE:
        return None
    
    yahoo_ticker = get_yahoo_ticker(symbol)
    print(f"   Baixando dados reais: {yahoo_ticker}...")
    
    try:
        # Baixa 5 dias de dados em 15min
        df = yf.download(yahoo_ticker, period="5d", interval="15m", progress=False)
        if df.empty:
            print(f"   ! Sem dados para {yahoo_ticker}")
            return None
        
        # FIX DEFINITIVO: yfinance retorna MultiIndex como ('Close', 'SOL-USD')
        # Precisa extrair apenas o primeiro nivel
        if isinstance(df.columns, pd.MultiIndex):
            # Pegar apenas o primeiro nivel (nomes das colunas)
            df.columns = [col[0] for col in df.columns]
        
        # Garantir nomes corretos (capitalizado)
        df.columns = [str(c).strip().title() for c in df.columns]
        
        # Verificar colunas obrigatorias
        required = ['Open', 'High', 'Low', 'Close']
        missing = [c for c in required if c not in df.columns]
        if missing:
            print(f"   ! Colunas faltando: {missing} (tem: {list(df.columns)})")
            return None
        
        print(f"   Colunas OK: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"   ! Erro download Yahoo: {e}")
        return None

def analyze_trend_real(df, window=20):
    """Analisa tendencia com dados reais"""
    if df is None or len(df) < window:
        return "NEUTRO", 0, 0
    
    try:
        sma = df['Close'].rolling(window=window).mean()
        last_close = float(df['Close'].iloc[-1])
        last_sma = float(sma.iloc[-1])
        
        # Forca baseada na distancia da media
        diff = ((last_close - last_sma) / last_sma) * 100
        strength = min(abs(diff) * 300, 100)  # Sensibilidade
        
        if diff > 0.1:
            trend = "ALTA"
        elif diff < -0.1:
            trend = "BAIXA"
        else:
            trend = "LATERAL"
        
        return trend, strength, last_sma
    except:
        return "NEUTRO", 0, 0

def analyze_structure(prices):
    """Fallback para dados simulados"""
    if len(prices) < 5:
        return "N/A", 0
    
    first_half = sum(prices[:len(prices)//2]) / (len(prices)//2)
    second_half = sum(prices[len(prices)//2:]) / (len(prices)//2)
    
    diff_percent = ((second_half - first_half) / first_half) * 100
    strength = abs(diff_percent) * 20
    
    if diff_percent > 0.2:
        return "ALTA", min(strength, 100)
    elif diff_percent < -0.2:
        return "BAIXA", min(strength, 100)
    else:
        return "LATERAL", 30

def gerar_dados_tecnicos(symbol, real_price=0, retry=False):
    """
    CAMADA 1: Coleta dados reais multi-TF
    CADEIA: 1) Deriv → 2) Yahoo → 3) cTrader file → 4) Retry 1x → 5) Simulado
    """
    
    # =========== OPCAO 1: DADOS DO CTRADER (Local JSON) ===========
    print("   [1/4] Tentando dados do cTrader (Local)...")
    ctrader_data = _load_ctrader_candles(symbol)
    if ctrader_data:
        result = _process_ctrader_candles(ctrader_data, symbol, real_price)
        if result:
            return result
            
    # =========== OPCAO 2: YAHOO FINANCE ===========
    print("   [2/4] Tentando Yahoo Finance...")
    df_m15 = fetch_real_data(symbol)
    
    if df_m15 is not None and not df_m15.empty:
        yahoo_result = _process_yahoo_data(df_m15, symbol, real_price)
        if yahoo_result:
            return yahoo_result
            
    # =========== OPCAO 3: DERIV API ===========
    print("   [3/4] Tentando Deriv API...")
    deriv_data = fetch_deriv_multi_tf(symbol)
    
    if deriv_data and len(deriv_data) >= 2:
        result = _process_multi_tf_data(deriv_data, symbol, real_price, "DERIV_API")
        if result:
            return result
    
    # =========== OPCAO 4: RETRY 1X ===========
    if not retry:
        print("   [4/4] Retry unico...")
        import time
        time.sleep(2)
        return gerar_dados_tecnicos(symbol, real_price, retry=True)
    
    # =========== FALLBACK: SIMULADO ===========
    print("   [SIMULADO] Usando dados gerados")
    return _generate_simulated_data(symbol, real_price)

def _load_ctrader_candles(symbol):
    """Tenta carregar candles salvos pelo cTrader (Multi-Symbol Support)"""
    # NOVO: Tentar carregar de subfolder específico do símbolo
    symbol_folder = os.path.join(DATA_FOLDER, symbol)
    config_file = os.path.join(symbol_folder, "symbol_config.json")
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                data = json.load(f)
                file_symbol = data.get("symbol", "")
                if file_symbol.upper() == symbol.upper():
                    print(f"   [CTRADER] Dados do indicador!")
                    return data
    except Exception as e:
        pass
    
    # FALLBACK: Formato legado (candles.json na raiz)
    candles_file = os.path.join(DATA_FOLDER, "candles.json")
    try:
        if os.path.exists(candles_file):
            with open(candles_file, 'r') as f:
                data = json.load(f)
                if data.get("symbol", "").upper() == symbol.upper():
                    print(f"   [CTRADER-LEGACY] Dados da raiz!")
                    return data
    except:
       pass
    return None

def _process_ctrader_candles(data, symbol, real_price):
    """Processa candles do cTrader"""
    try:
        current_price = real_price if real_price > 0 else data.get("current_price", 0)
        
        tf_results = {}
        for tf in ["m15", "m30", "h1", "h4"]:
            candles = data.get(tf, [])
            if candles:
                closes = [c.get("close", 0) for c in candles]
                if len(closes) >= 5:
                    structure, strength = analyze_structure(closes)
                    sma = sum(closes) / len(closes)
                    tf_results[tf.upper()] = {
                        "structure": structure,
                        "strength": strength,
                        "vs_sma": "ACIMA" if closes[-1] > sma else "ABAIXO",
                        "sma": sma
                    }
        
        if len(tf_results) >= 2:
            print("   [CTRADER] Dados do indicador!")
            t_m15 = tf_results.get("M15", {}).get("structure", "NEUTRO")
            t_m30 = tf_results.get("M30", {}).get("structure", "NEUTRO")
            t_h1 = tf_results.get("H1", {}).get("structure", "NEUTRO")
            t_h4 = tf_results.get("H4", {}).get("structure", "NEUTRO")
            
            structures = [t_m15, t_m30, t_h1, t_h4]
            bullish = structures.count("ALTA")
            bearish = structures.count("BAIXA")
            
            pivot = current_price
            return {
                "symbol": symbol,
                "price": current_price,
                "data_source": "CTRADER",
                "sugestao": "COMPRA" if bullish >= 3 else "VENDA" if bearish >= 3 else "NEUTRO",
                "bullish_tfs": bullish,
                "bearish_tfs": bearish,
                "open_positions": data.get("active_positions", []), # Lista de posicoes abertas (para Portfolio)
                "h4": tf_results.get("H4", {"structure": "NEUTRO", "strength": 0, "vs_sma": "N/A"}),
                "h2": tf_results.get("H4", {"structure": "NEUTRO", "strength": 0, "vs_sma": "N/A"}),
                "h1": tf_results.get("H1", {"structure": "NEUTRO", "strength": 0, "vs_sma": "N/A"}),
                "m30": tf_results.get("M30", {"structure": "NEUTRO", "strength": 0, "vs_sma": "N/A"}),
                "m15": tf_results.get("M15", {"structure": "NEUTRO", "strength": 0, "vs_sma": "N/A"}),
                "pivots": {
                    "pivot": round(pivot, 2),
                    "r1": round(pivot * 1.01, 2),
                    "r2": round(pivot * 1.02, 2),
                    "s1": round(pivot * 0.99, 2),
                    "s2": round(pivot * 0.98, 2)
                }
            }
    except Exception as e:
        print(f"   ! Erro cTrader: {e}")
    return None

def _process_multi_tf_data(deriv_data, symbol, real_price, source):
    """Processa dados multi-TF do Deriv"""
    try:
        df_m1 = deriv_data.get("M1")
        df_m5 = deriv_data.get("M5")
        df_m15 = deriv_data.get("M15")
        df_m30 = deriv_data.get("M30")
        df_h1 = deriv_data.get("H1")
        df_h4 = deriv_data.get("H4")
        
        current_price = real_price if real_price > 0 else float(df_m15['Close'].iloc[-1]) if df_m15 is not None else 0
        
        t_m1, s_m1, sma_m1 = analyze_trend_real(df_m1) if df_m1 is not None else ("NEUTRO", 0, 0)
        t_m5, s_m5, sma_m5 = analyze_trend_real(df_m5) if df_m5 is not None else ("NEUTRO", 0, 0)
        t_m15, s_m15, sma_m15 = analyze_trend_real(df_m15) if df_m15 is not None else ("NEUTRO", 0, 0)
        t_m30, s_m30, sma_m30 = analyze_trend_real(df_m30) if df_m30 is not None else ("NEUTRO", 0, 0)
        t_h1, s_h1, sma_h1 = analyze_trend_real(df_h1) if df_h1 is not None else ("NEUTRO", 0, 0)
        t_h4, s_h4, sma_h4 = analyze_trend_real(df_h4) if df_h4 is not None else ("NEUTRO", 0, 0)
        
        structures = [t_m1, t_m5, t_m15, t_m30, t_h1, t_h4]
        bullish = structures.count("ALTA")
        bearish = structures.count("BAIXA")
        
        # EXTRACT LAST 8 CANDLES FOR AI (PRICE ACTION)
        def get_raw_candles(df, n=8):
            if df is None or df.empty: return []
            try:
                # Pegar ultimos n
                subset = df.tail(n)
                candles_list = []
                for _, row in subset.iterrows():
                    # Formato compacto: O/H/L/C
                    c_str = f"(O:{row['Open']:.2f} H:{row['High']:.2f} L:{row['Low']:.2f} C:{row['Close']:.2f})"
                    candles_list.append(c_str)
                return candles_list
            except:
                return []

        raw_m1 = get_raw_candles(df_m1)
        raw_m5 = get_raw_candles(df_m5)
        raw_m15 = get_raw_candles(df_m15)
        raw_m30 = get_raw_candles(df_m30)
        raw_h1 = get_raw_candles(df_h1)
        raw_h4 = get_raw_candles(df_h4)
        
        if df_h4 is not None and len(df_h4) > 0:
            last_high = float(df_h4['High'].max())
            last_low = float(df_h4['Low'].min())
            pivot = (last_high + last_low + current_price) / 3
            r1 = (2 * pivot) - last_low
            r2 = pivot + (last_high - last_low)
            s1 = (2 * pivot) - last_high
            s2 = pivot - (last_high - last_low)
        else:
            pivot = current_price
            r1, r2, s1, s2 = pivot * 1.01, pivot * 1.02, pivot * 0.99, pivot * 0.98
        
        print(f"   [{source}] Dados reais!")
        return {
            "symbol": symbol,
            "price": current_price,
            "data_source": source,
            "sugestao": "COMPRA" if bullish >= 3 else "VENDA" if bearish >= 3 else "NEUTRO",
            "bullish_tfs": bullish,
            "bearish_tfs": bearish,
            "h4": {"structure": t_h4, "strength": s_h4, "vs_sma": "ACIMA" if current_price > sma_h4 else "ABAIXO"},
            "h2": {"structure": t_h4, "strength": s_h4, "vs_sma": "(=H4)"},
            "h1": {"structure": t_h1, "strength": s_h1, "vs_sma": "ACIMA" if current_price > sma_h1 else "ABAIXO"},
            "m30": {"structure": t_m30, "strength": s_m30, "vs_sma": "ACIMA" if current_price > sma_m30 else "ABAIXO"},
            "m15": {"structure": t_m15, "strength": s_m15, "vs_sma": "ACIMA" if current_price > sma_m15 else "ABAIXO"},
            "m5": {"structure": t_m5, "strength": s_m5, "vs_sma": "ACIMA" if current_price > sma_m5 else "ABAIXO"},
            "m1": {"structure": t_m1, "strength": s_m1, "vs_sma": "ACIMA" if current_price > sma_m1 else "ABAIXO"},
            "pivots": {"pivot": round(pivot, 2), "r1": round(r1, 2), "r2": round(r2, 2), "s1": round(s1, 2), "s2": round(s2, 2)},
            "raw_candles": {
                "m1": raw_m1,
                "m5": raw_m5,
                "m15": raw_m15,
                "m30": raw_m30,
                "h1": raw_h1,
                "h4": raw_h4
            }
        }
    except Exception as e:
        print(f"   ! Erro {source}: {e}")
    return None

def _process_yahoo_data(df_m15, symbol, real_price):
    """Processa dados do Yahoo Finance"""
    try:
        df_h1 = df_m15.resample('1h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
        df_h4 = df_m15.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
        df_m30 = df_m15.resample('30min').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
        
        current_price = float(df_m15['Close'].iloc[-1])
        
        t_m15, s_m15, sma_m15 = analyze_trend_real(df_m15)
        t_m30, s_m30, sma_m30 = analyze_trend_real(df_m30)
        t_h1, s_h1, sma_h1 = analyze_trend_real(df_h1)
        t_h4, s_h4, sma_h4 = analyze_trend_real(df_h4)
        
        structures = [t_m15, t_m30, t_h1, t_h4]
        bullish = structures.count("ALTA")
        bearish = structures.count("BAIXA")
        
        last_high = float(df_h4['High'].max())
        last_low = float(df_h4['Low'].min())
        pivot = (last_high + last_low + current_price) / 3
        r1 = (2 * pivot) - last_low
        r2 = pivot + (last_high - last_low)
        s1 = (2 * pivot) - last_high
        s2 = pivot - (last_high - last_low)
        
        print("   [YAHOO] Dados reais!")
        return {
            "symbol": symbol,
            "price": current_price,
            "data_source": "YAHOO",
            "sugestao": "COMPRA" if bullish >= 3 else "VENDA" if bearish >= 3 else "NEUTRO",
            "bullish_tfs": bullish,
            "bearish_tfs": bearish,
            "h4": {"structure": t_h4, "strength": s_h4, "vs_sma": "ACIMA" if current_price > sma_h4 else "ABAIXO"},
            "h2": {"structure": t_h4, "strength": s_h4, "vs_sma": "(=H4)"},
            "h1": {"structure": t_h1, "strength": s_h1, "vs_sma": "ACIMA" if current_price > sma_h1 else "ABAIXO"},
            "m30": {"structure": t_m30, "strength": s_m30, "vs_sma": "ACIMA" if current_price > sma_m30 else "ABAIXO"},
            "m15": {"structure": t_m15, "strength": s_m15, "vs_sma": "ACIMA" if current_price > sma_m15 else "ABAIXO"},
            "pivots": {"pivot": round(pivot, 2), "r1": round(r1, 2), "r2": round(r2, 2), "s1": round(s1, 2), "s2": round(s2, 2)}
        }
    except Exception as e:
        print(f"   ! Erro Yahoo: {e}")
    return None

def _generate_simulated_data(symbol, real_price):
    """Gera dados simulados como ultimo recurso"""
    base_price = real_price if real_price > 0 else 2620.0 + random.uniform(-30, 30)
    
    tf_data = {}
    for tf_name in ["H4", "H2", "H1", "M30", "M15"]:
        candles = []
        p = base_price
        for i in range(20):
            change = random.uniform(-2, 2)
            candles.append({"close": p + change})
            p += change
        
        closes = [c["close"] for c in candles]
        sma20 = sum(closes) / len(closes)
        structure, strength = analyze_structure(closes)
        
        tf_data[tf_name] = {"structure": structure, "strength": strength, "vs_sma": "ACIMA" if closes[-1] > sma20 else "ABAIXO"}
    
    bullish = sum(1 for tf in tf_data.values() if tf["structure"] == "ALTA")
    bearish = sum(1 for tf in tf_data.values() if tf["structure"] == "BAIXA")
    
    return {
        "symbol": symbol,
        "price": base_price,
        "data_source": "SIMULATED",
        "sugestao": "COMPRA" if bullish >= 3 else "VENDA" if bearish >= 3 else "NEUTRO",
        "bullish_tfs": bullish,
        "bearish_tfs": bearish,
        "h4": tf_data["H4"], "h2": tf_data["H2"], "h1": tf_data["H1"], "m30": tf_data["M30"], "m15": tf_data["M15"],
        "pivots": {"pivot": round(base_price, 2), "r1": round(base_price * 1.01, 2), "r2": round(base_price * 1.02, 2), "s1": round(base_price * 0.99, 2), "s2": round(base_price * 0.98, 2)}
    }

def gerar_dados_macro():
    """
    Dados Macro REAIS - VIX (medo) e DXY (dolar)
    """
    try:
        if YFINANCE_AVAILABLE:
            print("   Buscando VIX e DXY reais...")
            
            # VIX - Indice do Medo
            vix_data = yf.Ticker("^VIX").history(period="2d")
            vix = float(vix_data['Close'].iloc[-1]) if not vix_data.empty else 15
            vix_prev = float(vix_data['Close'].iloc[-2]) if len(vix_data) > 1 else vix
            
            # DXY - Indice Dolar
            dxy_data = yf.Ticker("DX-Y.NYB").history(period="2d")
            dxy = float(dxy_data['Close'].iloc[-1]) if not dxy_data.empty else 100
            dxy_prev = float(dxy_data['Close'].iloc[-2]) if len(dxy_data) > 1 else dxy
            
            # Determinar sentimento baseado no VIX
            if vix > 25:
                sentimento = "Risk-Off EXTREMO"
            elif vix > 20:
                sentimento = "Risk-Off"
            elif vix < 12:
                sentimento = "Risk-On FORTE"
            else:
                sentimento = "Risk-On"
            
            # Tendencia do DXY
            dxy_change = ((dxy - dxy_prev) / dxy_prev) * 100
            if dxy_change > 0.2:
                dxy_trend = "ALTA"
            elif dxy_change < -0.2:
                dxy_trend = "BAIXA"
            else:
                dxy_trend = "LATERAL"
            
            # Liquidez baseada no horario e VIX
            from datetime import datetime
            hora = datetime.now().hour
            if 9 <= hora <= 11 or 14 <= hora <= 16:  # Horarios de alta liquidez
                liquidez = "Alta" if vix < 20 else "Normal"
            elif 0 <= hora <= 6:  # Asia
                liquidez = "Baixa"
            else:
                liquidez = "Normal"
            
            print(f"   [MACRO REAL] VIX={vix:.1f} | DXY={dxy:.1f} | {sentimento}")
            
            return {
                "sentimento": sentimento,
                "fator": f"VIX {vix:.1f} | DXY {dxy:.1f}",
                "dxy": dxy_trend,
                "liquidez": liquidez,
                "vix": vix,
                "dxy_value": dxy
            }
    except Exception as e:
        print(f"   ! Erro macro: {e}")
    
    # Fallback simulado
    print("   [MACRO SIMULADO]")
    return {
        "sentimento": random.choice(["Risk-On", "Risk-Off", "Neutro"]),
        "fator": "Dados simulados",
        "dxy": random.choice(["ALTA", "BAIXA", "LATERAL"]),
        "liquidez": random.choice(["Normal", "Baixa", "Alta"])
    }

# =============================================================================
# CAMADA 2: GEMINI - Analise Multi-Estrategia
# =============================================================================

def get_asset_pip_info(symbol, price):
    """
    Calcula SL/TP em PERCENTUAL - 4 Estratégias por Horizonte
    """
    # 4 ESTRATEGIAS OTIMIZADAS
    strategies = {
        "fast_scalp": {
            "name": "FAST SCALP",
            "tfs": ["M1", "M5"],
            "duration": "1-5 min",
            "sl_pct": 0.15,
            "tp_pct": 0.25,
            "rr": "1:1.7"
        },
        "scalp": {
            "name": "SCALP",
            "tfs": ["M5", "M15"],
            "duration": "5-15 min",
            "sl_pct": 0.3,
            "tp_pct": 0.5,
            "rr": "1:1.7"
        },
        "intraday": {
            "name": "INTRADAY",
            "tfs": ["M30", "H1"],
            "duration": "1-4 horas",
            "sl_pct": 0.8,
            "tp_pct": 1.5,
            "rr": "1:1.9"
        },
        "swing": {
            "name": "SWING",
            "tfs": ["M30", "H1"],
            "duration": "30-60 min",
            "sl_pct": 1.5,
            "tp_pct": 3.0,
            "rr": "1:2"
        }
    }
    
    # Ajuste para CRYPTO (Volatilidade maior)
    is_crypto = "BTC" in symbol or "ETH" in symbol or "XRP" in symbol or "LTC" in symbol or "SOL" in symbol or "NEO" in symbol or "ADA" in symbol or "FET" in symbol
    multiplier = 1.5 if is_crypto else 1.0  # Reduzido de 2.0 para 1.5 para segurança

    # Calcular valores absolutos para cada estrategia
    result = {"strategies": {}}
    for key, strat in strategies.items():
        # Aplicar multiplicador em Crypto
        sl_pct_adj = strat["sl_pct"] * multiplier
        tp_pct_adj = strat["tp_pct"] * multiplier
        
        # GARANTIA DE STOP MINIMO (Evita rejeição do broker)
        MIN_SL_PCT = 0.2
        if sl_pct_adj < MIN_SL_PCT:
            sl_pct_adj = MIN_SL_PCT
            
        # TRAVA DE SEGURANÇA MAXIMA (Anti-Alucinação)
        MAX_SL_PCT = 5.0   # Max 5% de Stop
        MAX_TP_PCT = 12.0  # Max 12% de Alvo
        
        if sl_pct_adj > MAX_SL_PCT: sl_pct_adj = MAX_SL_PCT
        if tp_pct_adj > MAX_TP_PCT: tp_pct_adj = MAX_TP_PCT
        
        result["strategies"][key] = {
            "name": strat["name"],
            "tfs": strat["tfs"],
            "duration": strat["duration"],
            "sl_pct": sl_pct_adj,
            "tp_pct": tp_pct_adj,
            "rr": strat["rr"],
            "sl_value": round(price * sl_pct_adj / 100, 5), # 5 decimais para XRP
            "tp_value": round(price * tp_pct_adj / 100, 5),
        }
    
    # 5 PADROES DE ENTRADA
    result["patterns"] = {
        "pullback": {
            "name": "PULLBACK",
            "desc": "Continuacao de tendencia - preco recua ate zona de valor (SMA/Suporte) e rejeita",
            "logic": "Preco > SMA20 E Low tocou SMA20 E Fechou Verde",
            "rr": "1:2",
            "risk": "MEDIO"
        },
        "breakout": {
            "name": "BREAKOUT",
            "desc": "Explosao de momentum - rompe resistencia com volume",
            "logic": "Bollinger estreito E rompe banda E Volume > 2x media",
            "rr": "1:5",
            "risk": "ALTO"
        },
        "liquidity_sweep": {
            "name": "LIQUIDITY SWEEP",
            "desc": "Fakeout/Turtle Soup - rompe topo para stopar varejo e volta",
            "logic": "High > High 20 candles MAS Close < High anterior",
            "rr": "1:3",
            "risk": "MEDIO-ALTO"
        },
        "mean_reversion": {
            "name": "MEAN REVERSION",
            "desc": "Retorno a media - preco esticou 3 desvios da VWAP ou RSI > 80",
            "logic": "Preco a 3 StdDev da VWAP OU RSI extremo",
            "rr": "1:2",
            "risk": "ALTO"
        },
        "absorption": {
            "name": "ABSORPTION",
            "desc": "Absorcao de fluxo - muito volume mas preco nao anda (muro de liquidez)",
            "logic": "Volume muito alto MAS corpo do candle pequeno (Doji)",
            "rr": "1:3",
            "risk": "MEDIO"
        }
    }
    
    return result

def validar_com_gemini(macro, tecnico, stats={}):
    symbol = tecnico['symbol']
    price = tecnico['price']
    
    # Obter estrategias e padrões
    strat_info = get_asset_pip_info(symbol, price)
    strats = strat_info["strategies"]
    patterns = strat_info["patterns"]
    
    fast = strats["fast_scalp"]
    scalp = strats["scalp"]
    intraday = strats["intraday"]
    swing = strats["swing"]
    
    # Formatar stats para o prompt
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    total = stats.get("total", 0)
    win_rate = (wins / total * 100) if total > 0 else 0
    
    # Formatar posicoes ativas
    positions = tecnico.get('active_positions', [])  # FIX Issue #1
    pos_text = "NENHUMA"
    
    if positions:
        pos_lines = []
        for p in positions:
            pid = p.get('id', 0)
            direction = p.get('type', 'N/A')
            entry = p.get('entry', 0)
            curr_price = tecnico.get('current_price', 0)  # FIX Issue #2
            pnl = p.get('pnl', 0)
            
            # Safe Parsing para evitar NoneType Error
            sl_raw = p.get('sl')
            tp_raw = p.get('tp')
            sl = float(sl_raw) if sl_raw is not None else 0.0
            tp = float(tp_raw) if tp_raw is not None else 0.0
            
            strategy = p.get('strategy', 'UNKNOWN').upper()
            
            pos_lines.append(f"  - [ID:{pid}] {direction} @ ${entry:.4f} (Atual: ${curr_price:.4f}) | PnL: ${pnl:.2f}")
            pos_lines.append(f"    Target: SL=${sl:.4f} / TP=${tp:.4f} | Strat: {strategy}")
        pos_text = "\n".join(pos_lines)

    # --- CALCULO DE PADROES DE VELAS (MICRO) ---
    def calc_patterns(candles_list):
        if not candles_list or len(candles_list) < 3: return "Nenhum"
        try:
            df = pd.DataFrame(candles_list)
            if len(df) < 2: return "Nenhum"
            c1 = df.iloc[-1]
            c2 = df.iloc[-2]
            
            body1 = abs(c1['close'] - c1['open'])
            range1 = c1['high'] - c1['low']
            
            pats = []
            if range1 > 0 and body1 <= range1 * 0.1: pats.append("DOJI")
            
            lower_wick = min(c1['close'], c1['open']) - c1['low']
            upper_wick = c1['high'] - max(c1['close'], c1['open'])
            if lower_wick > 2 * body1 and upper_wick < body1: pats.append("HAMMER")
            if upper_wick > 2 * body1 and lower_wick < body1: pats.append("SHOOTING STAR")
            
            if c1['close'] > c1['open'] and c2['close'] < c2['open']:
                if c1['close'] > c2['open'] and c1['open'] < c2['close']: pats.append("BULLISH ENGULFING")
            elif c1['close'] < c1['open'] and c2['close'] > c2['open']:
                if c1['close'] < c2['open'] and c1['open'] > c2['close']: pats.append("BEARISH ENGULFING")
            
            return ", ".join(pats) if pats else "Sem padrão claro"
        except:
            return "Erro Pat"

    # FIX Issue #3: cBot exporta candles diretamente, não em raw_candles
    pat_h4 = calc_patterns(tecnico.get('h4', []))
    pat_h1 = calc_patterns(tecnico.get('h1', []))
    pat_m5 = calc_patterns(tecnico.get('m5', []))
    
    # --- DETECÇÃO DE DIVERGÊNCIA DE SENTIMENTO ---
    def detect_sentiment_divergence(sentiment_current, price_current, sentiment_history, price_history):
        """
        Detecta divergências entre sentimento (crowd) e preço.
        Divergência = Sinal FORTE de reversão.
        """
        if not sentiment_history or len(sentiment_history) < 10:
            return {"divergence": False}
        
        if not price_history or len(price_history) < 10:
            return {"divergence": False}
        
        # Pegar últimos 10 valores para comparação
        recent_sent = sentiment_history[-10:]
        recent_price = price_history[-10:]
        
        # Bullish Divergence: Preço cai MAS sentimento sobe
        price_at_low = price_current < min(recent_price)
        sentiment_rising = sentiment_current > max(recent_sent) - 5  # Margem de 5%
        
        if price_at_low and sentiment_rising:
            return {
                "divergence": True,
                "type": "BULLISH",
                "strength": 85,
                "message": f"🟢 DIVERGÊNCIA BULLISH: Preço em LOW ({price_current:.2f}) mas Sentimento RISING ({sentiment_current:.1f}%) → Reversão UP provável"
            }
        
        # Bearish Divergence: Preço sobe MAS sentimento cai
        price_at_high = price_current > max(recent_price)
        sentiment_falling = sentiment_current < min(recent_sent) + 5  # Margem de 5%
        
        if price_at_high and sentiment_falling:
            return {
                "divergence": True,
                "type": "BEARISH",
                "strength": 85,
                "message": f"🔴 DIVERGÊNCIA BEARISH: Preço em HIGH ({price_current:.2f}) mas Sentimento FALLING ({sentiment_current:.1f}%) → Reversão DOWN provável"
            }
        
        return {"divergence": False}
    
    # --- CALCULO DE INDICADORES MATEMATICOS ---
    def calc_ind(candles_list):
        if not candles_list or len(candles_list) < 20: return "Dados insuficientes"
        try:
            df = pd.DataFrame(candles_list)
            close = df['close']
            
            # RSI 14
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_val = rsi.iloc[-1]
            
            # EMA 200 (Tendencia Longa)
            ema200 = close.ewm(span=200).mean().iloc[-1]
            ema20 = close.ewm(span=20).mean().iloc[-1] # Tendencia Curta
            
            # Estado RSI
            if rsi_val > 70:
                rsi_state = "SOBRECOMPRA"
            elif rsi_val < 30:
                rsi_state = "SOBREVENDA"
            else:
                rsi_state = "NEUTRO"
            
            # Estado Trend
            trend = "ALTA" if close.iloc[-1] > ema200 else "BAIXA"
            momento = "ALTA" if close.iloc[-1] > ema20 else "BAIXA"
            
            # FIX Issue #8: Correlacao RSI+Sentiment (usar variavel global)
            correlation_suffix = ""
            if rsi_val > 70 and sentiment_buy > 75:
                correlation_suffix = " ⚠️ CROWD+RSI OVERBOUGHT!"
            elif rsi_val < 30 and sentiment_buy < 25:
                correlation_suffix = " ⚠️ CROWD+RSI OVERSOLD!"
            
            return f"RSI={rsi_val:.1f} ({rsi_state}) | EMA200={trend} | Momento={momento}{correlation_suffix}"
        except:
            return "Erro Calc"

    # --- PROCESSAR SENTIMENTO DE MERCADO (ANTES de calc_ind para usar na correlação) ---
    sentiment_data = tecnico.get('sentiment', {})
    sentiment_buy = sentiment_data.get('buy_percent', 50.0)
    sentiment_sell = sentiment_data.get('sell_percent', 50.0)
    sentiment_bias = sentiment_data.get('bias', 'NEUTRAL')
    sentiment_extreme = sentiment_data.get('is_extreme', False)
    sentiment_available = sentiment_data.get('available', False)
    
    # Calcular para todos os TFs (agora c/ acesso a sentiment_buy)
    ind_h4 = calc_ind(tecnico.get('h4', []))
    ind_h1 = calc_ind(tecnico.get('h1', []))
    ind_m30 = calc_ind(tecnico.get('m30', []))
    ind_m15 = calc_ind(tecnico.get('m15', []))
    ind_m5 = calc_ind(tecnico.get('m5', []))
    
    # Emojis para crowd behavior
    def get_crowd_emoji(pct):
        if pct >= 80: return "🔥🔥🔥"
        if pct >= 70: return "🔥🔥"
        if pct >= 60: return "🔥"
        if pct >= 40: return ""
        if pct >= 30: return "❄️"
        if pct >= 20: return "❄️❄️"
        return "❄️❄️❄️"
    
    emoji_buy = get_crowd_emoji(sentiment_buy)
    emoji_sell = get_crowd_emoji(sentiment_sell)
    
    # FIX Issue #5: Carregar histórico e detectar divergências
    sent_history = load_sentiment_history(symbol)
    buy_history = sent_history.get("buy_percent_history", [])
    price_history = sent_history.get("price_history", [])
    current_price = tecnico.get('current_price', 0)
    
    divergence_info = {"divergence": False}
    if len(buy_history) >= 10 and len(price_history) >= 10:
        divergence_info = detect_sentiment_divergence(
            sentiment_buy, current_price, buy_history, price_history
        )
    
    # Salvar sentimento atual no histórico
    if sentiment_available and current_price > 0:
        save_sentiment_history(symbol, sentiment_buy, current_price)
    
    divergence_alert = ""
    
    if divergence_info.get("divergence"):
        div_type = divergence_info.get("type")
        div_msg = divergence_info.get("message")
        divergence_alert = f"\n⚠️ {div_msg}\n"
    
    # Preparar texto de sentimento
    if sentiment_available:
        extreme_text = "⚠️ ZONA EXTREMA!" if sentiment_extreme else ""
        sentiment_text = f"""Buy Pressure: {sentiment_buy:.1f}% {emoji_buy}
Sell Pressure: {sentiment_sell:.1f}% {emoji_sell}
Status: {sentiment_bias} {extreme_text}
{divergence_alert}
REGRA CONTRÁRIA:
- Se BuyPercent > 70-80% (Crowd comprando forte) → AGUARDAR REVERSÃO para VENDER
- Se BuyPercent < 20-30% (Crowd vendendo forte) → AGUARDAR REVERSÃO para COMPRAR
- DIVERGÊNCIA detectada = SINAL PRIORITÁRIO (sobrepõe outros fatores)"""
    else:
        # FIX Issue #4: Warning explícito quando dados não disponíveis
        sentiment_text = """⚠️ [DADOS DE SENTIMENTO INDISPONÍVEIS]
O broker não fornece dados de Sentiment para este símbolo.
ATENÇÃO: Valores de 50%/50% são FALLBACK, NÃO refletem realidade do mercado.
Análise contrária DESABILITADA para esta decisão."""

    prompt = f"""Voce e um Trader Institucional Quantitativo. Analise o ativo {symbol} usando a matriz TEMPO x PADRAO.

=== PERFORMANCE RECENTE (LEARNING) ===
Total Trades: {total} | Wins: {wins} | Losses: {losses} | Win Rate: {win_rate:.1f}%

=== REGRA DE OURO: CONVERGENCIA HIBRIDA ===
Para CADA decisao (Nova Ordem ou Manter Posicao), EXIGIMOS convergencia total:
1. VIÉS MACRO (H4 + Sentimento Global) precisa apoiar a direcao.
2. SENTIMENTO DE MERCADO (Crowd Behavior) precisa ser considerado (análise contrária).
3. PADRÃO TÉCNICO (M5/M15/M30) precisa confirmar o timing.
4. INDICADORES (RSI/EMA) não podem estar contra (Ex: Comprar em Sobrecompra).

SE HOUVER DIVERGÊNCIA: WAIT ou TIGHTEN_SL.

=== PORTFOLIO ATUAL (EXPOSURE) ===
{pos_text}

=== SENTIMENTO DE MERCADO (BROKER DATA - REAL) ===
{sentiment_text}

=== INDICADORES TÉCNICOS (MATEMÁTICOS) ===
H4 : {ind_h4}
H1 : {ind_h1}
M30: {ind_m30}
M15: {ind_m15}
M5 : {ind_m5}

=== PADRÕES DE VELAS (MICRO) ===
H4 : {pat_h4}
H1 : {pat_h1}
M5 : {pat_m5}

=== REVISAO DE POSICOES ABERTAS ===
IMPORTANTE: Para CADA posicao aberta acima, analise se precisa de AJUSTES DE SL/TP:
1. A posicao ainda esta alinhada com as tendencias multi-TF (H4/H1/M30/M15/M5)?
2. A volatilidade atual justifica um SL mais curto/longo?
3. O preco se moveu significativamente desde a entrada?

ACOES PERMITIDAS:
- "KEEP" - Posicao ainda valida, manter SL/TP
- "TIGHTEN_SL" - Mercado contra a posicao, apertar SL para proteger
- "MOVE_TP_CLOSER" - Mercado instavel, garantir lucro parcial

CRITICO: NUNCA sugira "CLOSE_NOW". O bot NAO fecha posições, apenas ajusta SL/TP.
Se a posição está muito ruim, use TIGHTEN_SL para SL bem próximo (deixe o mercado fechar).

IMPORTANTE: Se ja temos muitas posicoes SELL, evite sugerir novos SELL a menos que o bias seja FORTEMENTE bearish.
Se temos posicoes no lado oposto da tendencia, considere sugerir "TIGHTEN_SL" ou "CLOSE_NOW".

=== CONTEXTO ===
Preco: ${price:.2f} | Sentimento: {macro['sentimento']} | Liquidez: {macro['liquidez']}
Pivots: S2={tecnico['pivots']['s2']:.2f} S1={tecnico['pivots']['s1']:.2f} P={tecnico['pivots']['pivot']:.2f} R1={tecnico['pivots']['r1']:.2f} R2={tecnico['pivots']['r2']:.2f}

=== TIMEFRAMES ===
H4: {tecnico['h4']['structure']} ({tecnico['h4']['strength']:.0f}%) | H1: {tecnico['h1']['structure']} ({tecnico['h1']['strength']:.0f}%)
M30: {tecnico['m30']['structure']} ({tecnico['m30']['strength']:.0f}%) | M15: {tecnico['m15']['structure']} ({tecnico['m15']['strength']:.0f}%)
M5: {tecnico.get('m5', {}).get('structure', 'N/A')} ({tecnico.get('m5', {}).get('strength', 0):.0f}%)

=== PRICE ACTION (ULTIMOS 8 CANDLES) ===
H4: {tecnico.get('raw_candles', {}).get('h4', [])}
H1: {tecnico.get('raw_candles', {}).get('h1', [])}
M30: {tecnico.get('raw_candles', {}).get('m30', [])}
M15: {tecnico.get('raw_candles', {}).get('m15', [])}
M5: {tecnico.get('raw_candles', {}).get('m5', [])}

=== 4 ESTRATEGIAS POR TEMPO ===
1. FAST_SCALP ({fast['duration']}) - TFs: M1+M5 | SL:{fast['sl_pct']}%=${fast['sl_value']:.2f} | TP:{fast['tp_pct']}%=${fast['tp_value']:.2f}
2. SCALP ({scalp['duration']}) - TFs: M15+M30 | SL:{scalp['sl_pct']}%=${scalp['sl_value']:.2f} | TP:{scalp['tp_pct']}%=${scalp['tp_value']:.2f}
3. INTRADAY ({intraday['duration']}) - TFs: M30+H1 | SL:{intraday['sl_pct']}%=${intraday['sl_value']:.2f} | TP:{intraday['tp_pct']}%=${intraday['tp_value']:.2f}
4. SWING ({swing['duration']}) - TFs: H1+H4 | SL:{swing['sl_pct']}%=${swing['sl_value']:.2f} | TP:{swing['tp_pct']}%=${swing['tp_value']:.2f}

=== 5 PADROES DE ENTRADA ===
1. PULLBACK - {patterns['pullback']['desc']} (RR {patterns['pullback']['rr']}, Risco {patterns['pullback']['risk']})
2. BREAKOUT - {patterns['breakout']['desc']} (RR {patterns['breakout']['rr']}, Risco {patterns['breakout']['risk']})
3. LIQUIDITY_SWEEP - {patterns['liquidity_sweep']['desc']} (RR {patterns['liquidity_sweep']['rr']}, Risco {patterns['liquidity_sweep']['risk']})
4. MEAN_REVERSION - {patterns['mean_reversion']['desc']} (RR {patterns['mean_reversion']['rr']}, Risco {patterns['mean_reversion']['risk']})
5. ABSORPTION - {patterns['absorption']['desc']} (RR {patterns['absorption']['rr']}, Risco {patterns['absorption']['risk']})

=== TAREFA ===
1. Avalie cada ESTRATEGIA (4) com direcao e confianca
2. Identifique qual PADRAO de entrada esta presente (se algum)
3. Combine a melhor estrategia + padrao para a oportunidade

RESPONDA EM JSON (SEM MARKDOWN ou ```json):
(NAO USE "..." PARA RESUMIR. PREENCHA TODOS OS CAMPOS.)
{{
    "analysis_summary": "resumo tecnico",
    "market_bias": "BULLISH/BEARISH/NEUTRAL",
    "strategies": {{
        "fast_scalp": {{"direction": "BUY/SELL/WAIT", "confidence": 0-100}},
        "scalp": {{"direction": "BUY/SELL/WAIT", "confidence": 0-100}},
        "intraday": {{"direction": "BUY/SELL/WAIT", "confidence": 0-100}},
        "swing": {{"direction": "BUY/SELL/WAIT", "confidence": 0-100}}
    }},
    "patterns_detected": {{
        "pullback": {{"active": true/false, "direction": "BUY/SELL"}},
        "breakout": {{"active": true/false, "direction": "BUY/SELL"}},
        "liquidity_sweep": {{"active": true/false, "direction": "BUY/SELL"}},
        "mean_reversion": {{"active": true/false, "direction": "BUY/SELL"}},
        "absorption": {{"active": true/false, "direction": "BUY/SELL"}}
    }},
    "position_reviews": [
        {{"position_id": use_exact_ID_from_brackets_above, "action": "KEEP/TIGHTEN_SL/CLOSE_NOW/MOVE_TP_CLOSER", "reason": "explicacao"}}
    ],
    "best_opportunity": {{
        "strategy": "fast_scalp/scalp/intraday/swing",
        "pattern": "pullback/breakout/liquidity_sweep/mean_reversion/absorption/none",
        "direction": "BUY/SELL",
        "confidence": 0-100,
        "entry": {price:.2f},
        "sl": valor,
        "tp1": valor,
        "tp2": valor,
        "breakeven_at": preco,
        "trailing_start": preco,
        "duration_min": minutos,
        "duration_max": minutos,
        "projection_lines": [
            {{"price": tp1, "label": "TP1", "color": "green"}},
            {{"price": tp2, "label": "TP2", "color": "lime"}},
            {{\"price\": sl, \"label\": \"SL\", \"color\": \"red\"}}
        ]
    }},
    "risk_warning": "avisos"
}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3}
    }

    try:
        print("  Consultando Gemini AI...")
        response = requests.post(GEMINI_URL, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"  ERRO Gemini: {response.status_code}")
            return None
        
        result = response.json()
        ai_text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # Log
        print("\n" + "="*60)
        print("  GEMINI RESPONSE:")
        print("="*60)
        print(ai_text[:800] + "..." if len(ai_text) > 800 else ai_text)
        print("="*60 + "\n")
        
        json_start = ai_text.find("{")
        json_end = ai_text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            parsed = json.loads(ai_text[json_start:json_end])
            parsed["full_response"] = ai_text
            
            # --- SANITY CHECK & AUTO-CORRECTION (PERCENTUAL) ---
            # Respeita limites conservadores definidos em tp_sl_validator.py
            try:
                best_op = parsed.get("best_opportunity", {})
                action = best_op.get("action", "").upper() # Or direction logic
                strategy = best_op.get("strategy", "scalp")
                
                # Check if direction exists (sometimes it's directly in strategy or pattern?)
                # The prompt asks for 'direction' in best_opportunity
                
                sl_ai = float(best_op.get("sl", 0))
                tp1_ai = float(best_op.get("tp1", 0))
                price_now = float(tecnico.get('current_price', 0)) # Use current_price from tecnico
                
                if price_now > 0 and (sl_ai > 0 or tp1_ai > 0):
                    # CHAMAR VALIDATOR
                    sl_corr, tp_corr, warnings = validate_and_cap_targets(
                        strategy_name=strategy,
                        sl_val=sl_ai,
                        tp_val=tp1_ai,
                        entry_price=price_now,
                        symbol=symbol
                    )
                    
                    # Atualizar valores se corrigidos
                    parsed["best_opportunity"]["sl"] = sl_corr
                    parsed["best_opportunity"]["tp1"] = tp_corr
                    
                    # Adicionar warnings ao log de risco
                    if warnings:
                        warn_msg = " | ".join(warnings)
                        parsed["risk_warning"] = parsed.get("risk_warning", "") + "\n" + warn_msg
                        print(f"  [RISK GUARD] {warn_msg}")
                        

                
            
            # --- SANITY CHECK PARA REVIEW DE POSIÇÕES ---
            # Protege ordens abertas contra movimentos bruscos de SL/TP
            
            # --- SANITY CHECK PARA REVIEW DE POSIÇÕES ---
                # --- SANITY CHECK PARA REVIEW DE POSIÇÕES ---
                # Protege ordens abertas contra movimentos bruscos de SL/TP
                MAX_SL_PCT = 5.0
                MAX_TP_PCT = 12.0
                
                if "position_reviews" in parsed and isinstance(parsed["position_reviews"], list):
                    # Criar mapa de posicoes por ID para lookup rapido
                    positions_map = {}
                    for pos in tecnico.get('open_positions', []):
                        positions_map[pos.get('id')] = pos
                    
                    for review in parsed["position_reviews"]:
                        try:
                            # Ignorar review se for CLOSE_NOW (isso é outro fluxo)
                            if review.get("action") == "CLOSE_NOW": continue
                            
                            # CRITICO: Descobrir a DIREÇÃO REAL da posição
                            pos_id = review.get("position_id")
                            original_pos = positions_map.get(pos_id)
                            
                            if not original_pos:
                                print(f"  [WARN] Review para posição {pos_id} não encontrada. Ignorando.")
                                continue
                            
                            pos_direction = original_pos.get('type', '').upper() # "BUY" ou "SELL"
                            
                            sl_rev = float(review.get("new_sl", 0))
                            tp_rev = float(review.get("new_tp", 0))
                            
                            # VALIDAÇÃO DE DIREÇÃO (Anti-Crash)
                            if sl_rev > 0:
                                # Buy: SL deve ser < price_now
                                # Sell: SL deve ser > price_now
                                if pos_direction == "BUY" and sl_rev >= price_now:
                                    print(f"  [SAFETY-REV] SL INVÁLIDO para BUY: {sl_rev} >= {price_now}. Corrigindo.")
                                    sl_rev = round(price_now * 0.98, 5)  # 2% abaixo
                                    review["new_sl"] = sl_rev
                                elif pos_direction == "SELL" and sl_rev <= price_now:
                                    print(f"  [SAFETY-REV] SL INVÁLIDO para SELL: {sl_rev} <= {price_now}. Corrigindo.")
                                    sl_rev = round(price_now * 1.02, 5)  # 2% acima
                                    review["new_sl"] = sl_rev
                                
                                # Verificar distância
                                dist_sl = abs(price_now - sl_rev) / price_now * 100
                                if dist_sl > MAX_SL_PCT:
                                    print(f"  [SAFETY-REV] SL Review agressivo ({dist_sl:.1f}%). Limitando a {MAX_SL_PCT}%.")
                                    if pos_direction == "BUY":
                                        review["new_sl"] = round(price_now * (1 - MAX_SL_PCT/100), 5)
                                    else:
                                        review["new_sl"] = round(price_now * (1 + MAX_SL_PCT/100), 5)

                            if tp_rev > 0:
                                # Validação de TP
                                if pos_direction == "BUY" and tp_rev <= price_now:
                                    print(f"  [SAFETY-REV] TP INVÁLIDO para BUY: {tp_rev} <= {price_now}. Corrigindo.")
                                    tp_rev = round(price_now * 1.05, 5)  # 5% acima
                                    review["new_tp"] = tp_rev
                                elif pos_direction == "SELL" and tp_rev >= price_now:
                                    print(f"  [SAFETY-REV] TP INVÁLIDO para SELL: {tp_rev} >= {price_now}. Corrigindo.")
                                    tp_rev = round(price_now * 0.95, 5)  # 5% abaixo
                                    review["new_tp"] = tp_rev
                                
                                dist_tp = abs(price_now - tp_rev) / price_now * 100
                                if dist_tp > MAX_TP_PCT:
                                    print(f"  [SAFETY-REV] TP Review agressivo ({dist_tp:.1f}%). Limitando a {MAX_TP_PCT}%.")
                                    if pos_direction == "BUY":
                                        review["new_tp"] = round(price_now * (1 + MAX_TP_PCT/100), 5)
                                    else:
                                        review["new_tp"] = round(price_now * (1 - MAX_TP_PCT/100), 5)
                                        
                        except Exception as e:
                            print(f"  [WARN] Falha validação review: {e}")

            except Exception as e:
                print(f"  [WARN] Falha no Sanity Check: {e}")
            # ----------------------------------------------
            
            return parsed
        else:
            print("  JSON invalido")
            return None
            
    except Exception as e:
        print(f"  Erro: {e}")
        return None

# =============================================================================
# VALIDAR SINAIS VIRTUAIS (Blocked Trades)
# =============================================================================
def validate_virtual_signals(history, current_price):
    """
    Valida sinais bloqueados retroativamente:
    - Se preço atingiu TP virtual → WIN
    - Se preço atingiu SL virtual → LOSS
    """
    updated = False
    
    for array_name in ["blocked_portfolio", "blocked_daily_limit"]:
        if array_name not in history:
            continue
            
        for signal in history[array_name]:
            # Já validado?
            if signal.get("virtual_result"):
                continue
            
            # Expirado?
            try:
                expires = datetime.strptime(signal["expires_at"], "%Y-%m-%d %H:%M:%S")
                if datetime.now() > expires:
                    signal["virtual_result"] = "EXPIRED"
                    signal["virtual_pnl"] = 0
                    updated = True
                    continue
            except:
                pass
            
           # Verificar se TP ou SL seria atingido
            direction = signal.get("direction", "").upper()
            entry = signal.get("entry", 0)
            tp = signal.get("tp1", 0)
            sl = signal.get("sl", 0)
            
            if entry == 0 or tp == 0 or sl == 0:
                continue
            
            # SELL
            if direction == "SELL":
                if current_price <= tp:  # TP hit
                    signal["virtual_result"] = "WIN"
                    signal["virtual_pnl"] = abs((entry - tp) / entry * 100)  # % gain
                    updated = True
                elif current_price >= sl:  # SL hit
                    signal["virtual_result"] = "LOSS"
                    signal["virtual_pnl"] = -abs((sl - entry) / entry * 100)  # % loss
                    updated = True
            
            # BUY
            elif direction == "BUY":
                if current_price >= tp:  # TP hit
                    signal["virtual_result"] = "WIN"
                    signal["virtual_pnl"] = abs((tp - entry) / entry * 100)
                    updated = True
                elif current_price <= sl:  # SL hit
                    signal["virtual_result"] = "LOSS"
                    signal["virtual_pnl"] = -abs((entry - sl) / entry * 100)
                    updated = True
    
    return updated

# =============================================================================
# EXPORTAR STATS VIRTUAIS PARA CBOT
# =============================================================================
def export_virtual_stats(history, symbol):
    """Exporta stats comparativas para o dashboard do cBot"""
    try:
        symbol_folder = get_symbol_folder(symbol)
        # Stats executadas (atual)
        executed_total = history["stats"].get("total", 0)
        executed_wins = history["stats"].get("wins", 0)
        executed_losses = history["stats"].get("losses", 0)
        executed_win_rate = (executed_wins / executed_total * 100) if executed_total > 0 else 0
        
        # Stats virtuais (bloqueadas)
        virtual_wins = 0
        virtual_losses = 0
        virtual_total = 0
        missed_profit = 0.0
        
        for array_name in ["blocked_portfolio", "blocked_daily_limit"]:
            for signal in history.get(array_name, []):
                result = signal.get("virtual_result")
                if result == "WIN":
                    virtual_wins += 1
                    virtual_total += 1
                    missed_profit += signal.get("virtual_pnl", 0)
                elif result == "LOSS":
                    virtual_losses += 1
                    virtual_total += 1
        
        virtual_win_rate = (virtual_wins / virtual_total * 100) if virtual_total > 0 else 0
        
        # Export
        stats = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "executed": {
                "total": executed_total,
                "wins": executed_wins,
                "losses": executed_losses,
                "win_rate": round(executed_win_rate, 1)
            },
            "virtual": {
                "total": virtual_total,
                "wins": virtual_wins,
                "losses": virtual_losses,
                "win_rate": round(virtual_win_rate, 1)
            },
            "blocked_count": history["stats"].get("blocked_count", 0),
            "missed_profit_pct": round(missed_profit, 2)
        }
        
        stats_file = os.path.join(symbol_folder, "virtual_stats.json")
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
            
    except Exception as e:
        print(f"  [ERROR] Falha ao exportar virtual stats: {e}")

# =============================================================================
# SALVAR SUGESTOES DE REVISAO DE POSICOES
# =============================================================================
def save_position_reviews(reviews, symbol):
    """Salva sugestões do Gemini para o cBot executar"""
    if not reviews:
        return
    
    try:
        symbol_folder = get_symbol_folder(symbol)
        review_file = os.path.join(symbol_folder, "position_reviews.json")
        
        # CRITICO: Converter position_id de string para int
        converted_reviews = []
        for review in reviews:
            converted = review.copy()
            # Gemini retorna position_id como string, cBot precisa de int
            pid = converted.get("position_id")
            if pid:
                try:
                    converted["position_id"] = int(str(pid).replace(",", "").replace(".", ""))
                except (ValueError, AttributeError):
                    print(f"  [WARN] Nao foi possivel converter position_id: {pid}")
                    continue
            converted_reviews.append(converted)
        
        data = {
            "symbol": symbol,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reviews": converted_reviews
        }
        with open(review_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  [REVIEWS] {len(converted_reviews)} sugestões exportadas para cBot")
    except Exception as e:
        print(f"  [ERROR] Falha ao exportar revisões: {e}")

# =============================================================================
# SALVAR SINAL + HISTORICO (Executed + Virtual Blocked)
# =============================================================================
def salvar_sinal(tecnico, decisao, history, blocked_reason=None):
    strategies = decisao.get("strategies", {})
    best = decisao.get("best_opportunity", {})
    
    high_conf_strategies = []
    for name, data in strategies.items():
        if data.get("confidence", 0) >= MIN_CONFIDENCE:
            high_conf_strategies.append({
                "name": name.upper(),
                "direction": data.get("direction", "WAIT"),
                "confidence": data.get("confidence", 0),
                "reason": data.get("reason", "")
            })
    
    high_conf_strategies.sort(key=lambda x: x["confidence"], reverse=True)
    has_opportunity = len(high_conf_strategies) > 0 and best.get("confidence", 0) >= MIN_CONFIDENCE
    
    now = datetime.now()
    expires = now + timedelta(minutes=best.get("duration_max", SIGNAL_TIMEOUT_MIN))
    signal_id = f"{tecnico['symbol']}_{now.strftime('%H%M%S')}"
    
    sinal = {
        "status": "APPROVED" if has_opportunity else "ANALYZING",
        "signal_id": signal_id,
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": expires.strftime("%Y-%m-%d %H:%M:%S"),
        "timeout_min": best.get("duration_max", SIGNAL_TIMEOUT_MIN),
        
        "gemini_summary": decisao.get("analysis_summary", ""),
        "gemini_opinion": decisao.get("gemini_opinion", ""),
        "risk_warning": decisao.get("risk_warning", ""),
        
        "all_strategies": {
            "scalp": strategies.get("scalp", {}),
            "swing": strategies.get("swing", {}),
            "position": strategies.get("position", {}),
            "breakout": strategies.get("breakout", {}),
            "reversal": strategies.get("reversal", {})
        },
        
        "high_confidence_count": len(high_conf_strategies),
        "high_confidence_strategies": high_conf_strategies,
        
        "best_strategy": best.get("strategy", "NONE"),
        "signal": best.get("direction", "WAIT"),
        "confidence": best.get("confidence", 0),
        "price": tecnico["price"],
        "entry": best.get("entry", 0),
        "stop": best.get("sl", 0),
        "target1": best.get("tp1", 0),
        "target2": best.get("tp2", 0),
        "breakeven_trigger": best.get("breakeven_at", 0),
        "trailing_start": best.get("trailing_start", 0),
        "duration_min": best.get("duration_min", 30),
        "duration_max": best.get("duration_max", 180),
        
        "pivots": tecnico.get("pivots", {}),
        "projection_lines": best.get("projection_lines", []),
        
        "multi_tf": {
            "h4": f"{tecnico['h4']['structure']} ({tecnico['h4']['strength']:.0f}%)",
            "h2": f"{tecnico['h2']['structure']} ({tecnico['h2']['strength']:.0f}%)",
            "h1": f"{tecnico['h1']['structure']} ({tecnico['h1']['strength']:.0f}%)",
            "m30": f"{tecnico['m30']['structure']} ({tecnico['m30']['strength']:.0f}%)",
            "m15": f"{tecnico['m15']['structure']} ({tecnico['m15']['strength']:.0f}%)"
        },
        
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "valid_until": expires.strftime("%Y-%m-%d %H:%M:%S"),
        "full_gemini_log": decisao.get("full_response", "")[:2000],
        
        # Stats do historico
        "history_stats": history.get("stats", {})
    }
    
    # NOVO: Inicializar arrays de virtual trades se não existem
    if "blocked_portfolio" not in history:
        history["blocked_portfolio"] = []
    if "blocked_daily_limit" not in history:
        history["blocked_daily_limit"] = []
    
    # Adicionar ao historico - EXECUTADO ou BLOQUEADO
    if has_opportunity:
        history_entry = {
            "signal_id": signal_id,
            "symbol": tecnico["symbol"],
            "direction": best.get("direction", ""),
            "strategy": best.get("strategy", ""),
            "confidence": best.get("confidence", 0),
            "entry": best.get("entry", 0),
            "sl": best.get("sl", 0),
            "tp1": best.get("tp1", 0),
            "tp2": best.get("tp2", 0),
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "expires_at": expires.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "PENDING",
            "result_price": 0,
            "result_time": "",
            "pips_result": 0
        }
        
        # Se foi BLOQUEADO, salvar em array separado
        if blocked_reason:
            history_entry["blocked_reason"] = blocked_reason
            history_entry["virtual_result"] = None  # Será preenchido depois
            history_entry["virtual_pnl"] = 0
            
            if blocked_reason == "portfolio_full":
                history["blocked_portfolio"].append(history_entry)
            elif blocked_reason == "daily_limit":
                history["blocked_daily_limit"].append(history_entry)
                
            # Stats
            history["stats"]["blocked_count"] = history["stats"].get("blocked_count", 0) + 1
            
        else:
            # Sinal EXECUTADO normalmente
            history["signals"].append(history_entry)
            history["stats"]["total"] = history["stats"].get("total", 0) + 1
            history["stats"]["pending"] = history["stats"].get("pending", 0) + 1
    
    # Escrita atômica (só sinais executados vão para signal.json)
    if has_opportunity and not blocked_reason:
        symbol = tecnico.get('symbol', 'UNKNOWN')
        symbol_folder = get_symbol_folder(symbol)
        output_file = os.path.join(symbol_folder, "predictions.json")
        atomic_write(output_file, sinal)
    
    return has_opportunity

# =============================================================================
# LOOP PRINCIPAL - MULTI-SYMBOL
# =============================================================================
def run():
    ensure_folder()
    
    print("="*70)
    print("  TITAN FUSION QUANTUM - AI Trading System")
    print("="*70)
    print(f"Pasta Base: {DATA_FOLDER}")
    print(f"TFs: H4, H1, M30, M15, M5")
    print(f"Timeout: {SIGNAL_TIMEOUT_MIN} min")
    print("-"*70)
    
    try:
        while True:
            # Detectar símbolos ativos
            active_symbols = detect_active_symbols()
            
            if not active_symbols:
                print("[AGUARDANDO] Nenhum símbolo detectado. Aguardando cBots exportarem dados...")
                time.sleep(10)
                continue
            
            print(f"\n[SIMBOLOS ATIVOS] {', '.join(active_symbols)}")
            
            # Processar cada símbolo independentemente
            for symbol in active_symbols:
                try:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === ANALISE {symbol} ===")
                    
                    # Carregar dados e histórico do símbolo
                    ctrader_data = load_ctrader_data(symbol)
                    if not ctrader_data:
                        print(f"  [SKIP] Dados não disponíveis para {symbol}")
                        continue
                    
                    # Safe access com fallbacks para diferentes formatos
                    real_price = ctrader_data.get("price", ctrader_data.get("current_price", 0))
                    if real_price == 0:
                        print(f"  [SKIP] Preço inválido para {symbol}")
                        continue
                        
                    positions = ctrader_data.get("positions", {})
                    history = load_signal_history(symbol)
                    
                    # Verificar resultados de sinais anteriores
                    print("  0. Verificando sinais pendentes...")
                    if check_signal_results(history, real_price):
                        save_signal_history(history, symbol)
                        stats = history.get("stats", {})
                        print(f"  Stats: {stats.get('wins', 0)}W / {stats.get('losses', 0)}L / {stats.get('pending', 0)}P")
                    
                    # Validar sinais virtuais (bloqueados)
                    if validate_virtual_signals(history, real_price):
                        save_signal_history(history, symbol)
                        print(f"  [VIRTUAL] Sinais bloqueados validados")
                    
                    # Exportar stats virtuais para cBot
                    export_virtual_stats(history, symbol)
                    
                    # Posições
                    if positions:
                        buy_count = positions.get("buy_count", 0)
                        sell_count = positions.get("sell_count", 0)
                        pnl = positions.get("unrealized_pnl", 0)
                        if buy_count > 0 or sell_count > 0:
                            print(f"  POSICOES: {buy_count} Buy | {sell_count} Sell | PnL: ${pnl:.2f}")
                    
                    # Análise tecnica e macro
                    print("  1. Buscando candles multi-TF...")
                    tecnico = gerar_dados_tecnicos(symbol, real_price)
                    if not tecnico:
                        print(f"  [ERRO] Falha ao obter dados. Retry em próximo ciclo.")
                        continue
                    print(f"   [OK] Fonte: {tecnico.get('data_source', 'N/A')}")
                    
                    tecnico["open_positions"] = []
                    
                    # Suporte para NOVO FORMATO (Lista de objetos)
                    if "active_positions" in ctrader_data and isinstance(ctrader_data["active_positions"], list):
                        for p in ctrader_data["active_positions"]:
                            tecnico["open_positions"].append({
                                "id": p.get("id"),
                                "type": p.get("type"),
                                "entry": p.get("entry"),
                                "sl": p.get("sl"),      # NOVO
                                "tp": p.get("tp"),      # NOVO
                                "pnl": p.get("pnl"),
                                "strategy": p.get("strategy", "UNKNOWN")
                            })
                            
                    # Suporte para FORMATO LEGADO (Flat keys) - Fallback
                    elif positions:
                        if positions.get("buy_count", 0) > 0:
                            for i in range(positions["buy_count"]):
                                pos_id = positions.get(f"buy_id_{i+1}", 0)
                                entry = positions.get(f"buy_entry_{i+1}", 0)
                                pnl = positions.get(f"buy_pnl_{i+1}", 0)
                                strat = positions.get(f"buy_strategy_{i+1}", "UNKNOWN")
                                tecnico["open_positions"].append({
                                    "id": pos_id, "type": "BUY", "entry": entry,
                                    "pnl": pnl, "strategy": strat
                                })
                        if positions.get("sell_count", 0) > 0:
                            for i in range(positions["sell_count"]):
                                pos_id = positions.get(f"sell_id_{i+1}", 0)
                                entry = positions.get(f"sell_entry_{i+1}", 0)
                                pnl = positions.get(f"sell_pnl_{i+1}", 0)
                                strat = positions.get(f"sell_strategy_{i+1}", "UNKNOWN")
                                tecnico["open_positions"].append({
                                    "id": pos_id, "type": "SELL", "entry": entry,
                                    "pnl": pnl, "strategy": strat
                                })
                    
                    print("  2. Analisando macro...")
                    macro = gerar_dados_macro()
                    
                    print("  3. Consultando Gemini AI...")
                    stats = history.get("stats", {})
                    decisao = validar_com_gemini(macro, tecnico, stats)
                    
                    if not decisao or decisao.get("decision") == "WAIT":
                        print("  DECISAO: WAIT (sem oportunidade clara)")
                        continue
                    
                    # Position reviews - SEM CLOSE_NOW (só ajustes de SL/TP)
                    position_reviews = decisao.get("position_reviews", [])
                    if position_reviews:
                        # Filtrar CLOSE_NOW - bot NÃO fecha, só ajusta
                        allowed_reviews = [r for r in position_reviews if r.get("action") != "CLOSE_NOW"]
                        if allowed_reviews:
                            save_position_reviews(allowed_reviews, symbol)
                            print(f"  [AI-REVIEW] {len(allowed_reviews)} ajustes de SL/TP sugeridos")
                    
                    # Melhor oportunidade
                    best = decisao.get("best_opportunity", {})
                    if not best or best.get("confidence", 0) < MIN_CONFIDENCE:
                        print(f"  CONFIANCA BAIXA: {best.get('confidence', 0)}% (minimo: {MIN_CONFIDENCE}%)")
                        continue
                    
                    # Portfolio Limits
                    count_fast = sum(1 for p in tecnico["open_positions"] if "FAST" in p.get("strategy", ""))
                    count_scalp = sum(1 for p in tecnico["open_positions"] if "SCALP" in p.get("strategy", "") and "FAST" not in p.get("strategy", ""))
                    count_intra = sum(1 for p in tecnico["open_positions"] if "INTRA" in p.get("strategy", ""))
                    count_swing = sum(1 for p in tecnico["open_positions"] if "SWING" in p.get("strategy", ""))
                    
                    slot_full = False
                    strat_name = best.get("strategy", "").lower()
                    
                    if "fast" in strat_name:
                        if count_fast >= 2:
                            print(f"  [LIMIT] Fast Scalp Slot Cheio (2/2). Ignorando {strat_name}.")
                            slot_full = True
                    elif "scalp" in strat_name and "fast" not in strat_name:
                        if count_scalp >= 1:
                            print(f"  [LIMIT] Scalp Slot Cheio (1/1). Ignorando {strat_name}.")
                            slot_full = True
                    elif "intra" in strat_name:
                        if count_intra >= 1:
                            print(f"  [LIMIT] Intraday Slot Cheio (1/1). Ignorando {strat_name}.")
                            slot_full = True
                    elif "swing" in strat_name:
                        if count_swing >= 1:
                            print(f"  [LIMIT] Swing Slot Cheio (1/1). Ignorando {strat_name}.")
                            slot_full = True
                            
                    if slot_full:
                        print(f"\n  SINAL NEGADO POR PORTFOLIO: {best.get('strategy', 'N/A')} ({best.get('confidence', 0)}%)")
                        was_virtual = salvar_sinal(tecnico, decisao, history, blocked_reason="portfolio_full")
                        if was_virtual:
                            save_signal_history(history, symbol)
                            print(f"  [VIRTUAL] Sinal salvo para análise retroativa")
                    else:
                        print(f"\n  SINAL: {best.get('strategy', 'N/A')} {best.get('direction', 'N/A')} ({best.get('confidence', 0)}%)")
                        print(f"  Entry: {best.get('entry', 0):.2f} | SL: {best.get('sl', 0):.2f} | TP1: {best.get('tp1', 0):.2f}")
                        was_approved = salvar_sinal(tecnico, decisao, history)
                        if was_approved:
                            save_signal_history(history, symbol)
                
                except Exception as e:
                    import traceback
                    print(f"  [ERRO] Falha ao processar {symbol}: {e}")
                    traceback.print_exc()  # Mostrar linha exata do erro
                    continue
            
            # Aguardar próximo ciclo
            print(f"\n  Proxima em {UPDATE_INTERVAL}s...")
            time.sleep(UPDATE_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nEncerrando...")
    
    print("Finalizado!")

if __name__ == "__main__":
    run()

