# Symbol Metadata Cache - Economiza tokens do Gemini
# Armazena informações estáticas do símbolo para evitar recálculo

import json
import os
from datetime import datetime

def create_symbol_metadata(symbol, ctrader_data, price_history=None):
    """
    Cria metadata do símbolo baseado nos dados do cTrader
    Informações salvas UMA VEZ e reutilizadas sempre
    """
    
    # Detectar tipo de ativo
    asset_type = "UNKNOWN"
    if any(crypto in symbol.upper() for crypto in ["BTC", "ETH", "XRP", "LTC", "SOL", "FET", "ADA"]):
        asset_type = "CRYPTO"
    elif any(forex in symbol.upper() for forex in ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF"]):
        asset_type = "FOREX"
    elif any(idx in symbol.upper() for idx in ["US30", "SPX", "NAS", "GER", "UK100"]):
        asset_type = "INDEX"
    elif "XAU" in symbol.upper() or "XAG" in symbol.upper() or "OIL" in symbol.upper():
        asset_type = "COMMODITY"
    
    # Extrair preço atual
    current_price = ctrader_data.get("current_price", 0)
    
    # Calcular pip size baseado no preço
    if current_price < 1.0:
        pip_size = 0.0001  # Crypto de centavos
        pip_value_estimate = 0.01
    elif current_price < 10.0:
        pip_size = 0.001
        pip_value_estimate = 0.1
    elif current_price < 100.0:
        pip_size = 0.01
        pip_value_estimate = 1.0
    else:
        pip_size = 0.1  # Índices
        pip_value_estimate = 10.0
    
    # Calcular ranges típicos do histórico de candles
    all_highs = []
    all_lows = []
    
    for tf in ["h4", "h1", "m30", "m15"]:
        candles = ctrader_data.get(tf, [])
        if candles:
            for candle in candles[-20:]:  # Últimos 20 candles
                high = candle.get("high", 0)
                low = candle.get("low", 0)
                if high > 0:
                    all_highs.append(high)
                if low > 0:
                    all_lows.append(low)
    
    if all_highs and all_lows:
        avg_high = sum(all_highs) / len(all_highs)
        avg_low = sum(all_lows) / len(all_lows)
        avg_range = avg_high - avg_low
        volatility_pct = (avg_range / current_price * 100) if current_price > 0 else 0
    else:
        avg_high = current_price * 1.02
        avg_low = current_price * 0.98
        avg_range = current_price * 0.02
        volatility_pct = 2.0
    
    # Configurações de SL/TP recomendadas baseadas no tipo
    if asset_type == "CRYPTO":
        sl_multiplier = 2.0
        tp_multiplier = 2.0
        confidence_adjustment = -5  # Mais conservador
    elif asset_type == "INDEX":
        sl_multiplier = 1.0
        tp_multiplier = 1.0
        confidence_adjustment = 0
    else:  # FOREX, COMMODITY
        sl_multiplier = 1.0
        tp_multiplier = 1.0
        confidence_adjustment = 0
    
    metadata = {
        "symbol": symbol,
        "asset_type": asset_type,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        
        # Informações de preço
        "price_info": {
            "first_seen_price": current_price,
            "typical_range": round(avg_range, 6),
            "avg_high_20": round(avg_high, 6),
            "avg_low_20": round(avg_low, 6),
            "volatility_pct": round(volatility_pct, 2)
        },
        
        # Informações de pip
        "pip_info": {
            "pip_size": pip_size,
            "pip_value_estimate": pip_value_estimate,
            "decimals": 5 if current_price < 1 else 4 if current_price < 10 else 2
        },
        
        # Configurações estratégicas
        "strategy_config": {
            "sl_multiplier": sl_multiplier,
            "tp_multiplier": tp_multiplier,
            "confidence_adjustment": confidence_adjustment,
            "min_confidence": 75 if asset_type == "CRYPTO" else 70
        },
        
        # Contexto para Gemini (economiza tokens)
        "gemini_context": {
            "asset_class": asset_type,
            "volatility_profile": "HIGH" if volatility_pct > 3 else "MODERATE" if volatility_pct > 1 else "LOW",
            "typical_move_pct": round(volatility_pct, 1),
            "price_decimals": 5 if current_price < 1 else 4 if current_price < 10 else 2
        },
        
        # Stats de uso
        "usage_stats": {
            "analyses_count": 0,
            "signals_generated": 0,
            "last_analysis": None
        }
    }
    
    return metadata


def load_or_create_metadata(symbol, symbol_folder, ctrader_data):
    """
    Carrega metadata existente OU cria novo se não existir
    """
    metadata_file = os.path.join(symbol_folder, "symbol_metadata.json")
    
    # Se já existe, carregar
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                
            # Atualizar último uso
            metadata["usage_stats"]["analyses_count"] += 1
            metadata["usage_stats"]["last_analysis"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            metadata["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Salvar atualização
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            return metadata
        except:
            pass  # Se falhar, criar novo
    
    # Criar novo metadata
    metadata = create_symbol_metadata(symbol, ctrader_data)
    
    # Salvar
    try:
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"  [METADATA] Criado perfil do símbolo {symbol}")
    except Exception as e:
        print(f"  [ERROR] Falha ao salvar metadata: {e}")
    
    return metadata


def get_gemini_context_string(metadata):
    """
    Retorna string de contexto otimizada para Gemini (economiza tokens)
    """
    ctx = metadata["gemini_context"]
    price = metadata["price_info"]
    
    context = f"""
PERFIL DO ATIVO:
- Classe: {ctx['asset_class']}
- Volatilidade: {ctx['volatility_profile']} ({ctx['typical_move_pct']}% movimento típico)
- Precisão: {ctx['price_decimals']} decimais
- Range típico: {price['typical_range']:.6f} ({price['volatility_pct']:.1f}%)
"""
    return context.strip()
