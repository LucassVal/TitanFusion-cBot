# ══════════════════════════════════════════════════════════════════
# TITAN FUSION QUANTUM - TP/SL Validator (PERCENTUAL-BASED)
# ══════════════════════════════════════════════════════════════════
# 
# Purpose: Enforce strict TP/SL limits based on PERCENTAGE of price
# Focus: 1-5 USD per lot, consistent small wins
#
# ══════════════════════════════════════════════════════════════════

def validate_and_cap_targets(strategy_name, sl_val, tp_val, entry_price, symbol):
    """
    VALIDAÇÃO CONSERVADORA: Limita TP/SL baseado em PERCENTUAL do preço
    
    Limites por estratégia (% do preço):
    - FAST SCALP: SL max 0.15% | TP max 0.25%
    - SCALP: SL max 0.3% | TP max 0.5%
    - INTRADAY: SL max 0.8% | TP max 1.5%
    - SWING: SL max 1.5% | TP max 3.0%
    
    Se AI sugerir valores maiores → CORREÇÃO AUTOMÁTICA
    """
    # Limites máximos por estratégia (PERCENTUAL DO PREÇO)
    limits = {
        "fast_scalp": {"max_sl_pct": 0.15, "max_tp_pct": 0.25},
        "scalp": {"max_sl_pct": 0.30, "max_tp_pct": 0.50},
        "intraday": {"max_sl_pct": 0.80, "max_tp_pct": 1.50},
        "swing": {"max_sl_pct": 1.50, "max_tp_pct": 3.00}
    }
    
    # Detectar estratégia
    strat_key = "scalp"  # default conservador
    if "FAST" in strategy_name.upper():
        strat_key = "fast_scalp"
    elif "SCALP" in strategy_name.upper():
        strat_key = "scalp"
    elif "INTRADAY" in strategy_name.upper():
        strat_key = "intraday"
    elif "SWING" in strategy_name.upper():
        strat_key = "swing"
    
    max_sl_pct = limits[strat_key]["max_sl_pct"]
    max_tp_pct = limits[strat_key]["max_tp_pct"]
    
    # Calcular distância em PERCENTUAL
    sl_pct = (abs(entry_price - sl_val) / entry_price * 100) if sl_val > 0 else 0
    tp_pct = (abs(tp_val - entry_price) / entry_price * 100) if tp_val > 0 else 0
    
    # VALIDAÇÃO E CORREÇÃO AUTOMÁTICA
    warnings = []
    capped = False
    
    # Corrigir SL excessivo (STRICTLY greater, not equal)
    if sl_pct > max_sl_pct + 0.01:  # Small tolerance for floating point
        warnings.append(f"⚠️ SL MUITO GRANDE! {sl_pct:.2f}% (limite: {max_sl_pct}%)")
        # Determinar direção do trade
        if entry_price > sl_val:  # SELL trade
            sl_val = entry_price * (1 - max_sl_pct / 100)
        else:  # BUY trade
            sl_val = entry_price * (1 + max_sl_pct / 100)
        capped = True
        print(f"  🔧 [AUTO-CORREÇÃO] SL ajustado para {max_sl_pct}% do preço")
    
    # Corrigir TP excessivo (STRICTLY greater, not equal)
    if tp_pct > max_tp_pct + 0.01:  # Small tolerance for floating point
        warnings.append(f"⚠️ TP MUITO GRANDE! {tp_pct:.2f}% (limite: {max_tp_pct}%)")
        # Determinar direção do trade
        if entry_price < tp_val:  # BUY trade
            tp_val = entry_price * (1 + max_tp_pct / 100)
        else:  # SELL trade
            tp_val = entry_price * (1 - max_tp_pct / 100)
        capped = True
        print(f"  🔧 [AUTO-CORREÇÃO] TP ajustado para {max_tp_pct}% do preço")
    
    # Recalcular percentual após correção
    sl_pct_final = (abs(entry_price - sl_val) / entry_price * 100) if sl_val > 0 else 0
    tp_pct_final = (abs(tp_val - entry_price) / entry_price * 100) if tp_val > 0 else 0
    
    # Calcular distância absoluta para referência
    sl_distance = abs(entry_price - sl_val)
    tp_distance = abs(tp_val - entry_price)
    
    # Imprimir resumo
    if capped:
        print(f"\n  ═══ VALIDAÇÃO CONSERVADORA ═══")
        print(f"  Estratégia: {strategy_name.upper()}")
        print(f"  Símbolo: {symbol} | Preço Entry: ${entry_price:.5f}")
        print(f"  Limites: SL ≤ {max_sl_pct}% | TP ≤ {max_tp_pct}%")
        print(f"  Valores finais:")
        print(f"    SL: ${sl_val:.5f} ({sl_pct_final:.2f}% = ${sl_distance:.5f})")
        print(f"    TP: ${tp_val:.5f} ({tp_pct_final:.2f}% = ${tp_distance:.5f})")
        print(f"  ════════════════════════════════\n")
    elif sl_pct > 0 and tp_pct > 0:
        print(f"  ✅ TP/SL dentro dos limites:")
        print(f"     SL = {sl_pct:.2f}% | TP = {tp_pct:.2f}%")
    
    return sl_val, tp_val, warnings


# ══════════════════════════════════════════════════════════════════
# EXEMPLO DE USO:
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Teste 1: XRPUSD Scalp (caso do usuário)
    print("TESTE 1: XRPUSD Scalp com TP excessivo")
    sl, tp, warns = validate_and_cap_targets(
        strategy_name="SCALP",
        sl_val=1.6824,
        tp_val=1.7003,  # 131 pips = 7.7% !
        entry_price=1.6872,
        symbol="XRPUSD"
    )
    print(f"SL Corrigido: {sl:.5f}")
    print(f"TP Corrigido: {tp:.5f}\n")
    
    # Teste 2: EURUSD Scalp conservador
    print("TESTE 2: EURUSD Scalp conservador")
    sl, tp, warns = validate_and_cap_targets(
        strategy_name="SCALP",
        sl_val=1.0970,
        tp_val=1.1030,  # 0.5% OK
        entry_price=1.1000,
        symbol="EURUSD"
    )
    print(f"SL: {sl:.5f}")
    print(f"TP: {tp:.5f}\n")
    
    # Teste 3: Gold Fast Scalp
    print("TESTE 3: Gold Fast Scalp")
    sl, tp, warns = validate_and_cap_targets(
        strategy_name="FAST SCALP",
        sl_val=2596.00,
        tp_val=2606.50,  # 0.25% OK
        entry_price=2600.00,
        symbol="XAUUSD"
    )
    print(f"SL: {sl:.2f}")
    print(f"TP: {tp:.2f}\n")

# ══════════════════════════════════════════════════════════════════
# Como integrar no quantum_brain.py:
# ══════════════════════════════════════════════════════════════════
#
# 1. Import no topo:
# from tp_sl_validator import validate_and_cap_targets
#
# 2. Depois de parsear resposta do Gemini:
# sl_corrected, tp_corrected, warns = validate_and_cap_targets(
#     strategy_name=chosen_strategy,
#     sl_val=float(sl_from_ai),
#     tp_val=float(tp_from_ai),
#     entry_price=current_price,
#     symbol=symbol
# )
#
# 3. Usar valores corrigidos:
# result["sl"] = sl_corrected
# result["tp"] = tp_corrected
#
# 4. Mostrar warnings se houver:
# for warn in warns:
#     print(f"  {warn}")
#
# ══════════════════════════════════════════════════════════════════
