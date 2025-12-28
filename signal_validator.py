#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
 TITAN FUSION - SIGNAL VALIDATOR v1.0
 Independent script to validate trading signals and calculate performance
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict

# Try to import matplotlib for charts (optional)
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    print("⚠️ matplotlib not installed. Charts disabled. Run: pip install matplotlib")

# Paths
DATA_FOLDER = r"C:\Users\Lucas Valério\Documents\TitanFusionAI"
JOURNAL_FOLDER = os.path.join(DATA_FOLDER, "Journal")
REPORT_FOLDER = os.path.join(DATA_FOLDER, "Reports")

# Strategy expected durations (in candles of their timeframe)
STRATEGY_TIMEFRAMES = {
    "FAST_SCALP": {"tf": "M5", "max_candles": 3},   # 15 min max
    "SCALP": {"tf": "M15", "max_candles": 4},       # 60 min max
    "MOMENTUM": {"tf": "H1", "max_candles": 4},    # 4 hours max
    "SWING": {"tf": "H4", "max_candles": 6},       # 24 hours max
}

def parse_journal_line(line):
    """Parse a journal line into structured data."""
    # Format: [HH:MM:SS] SYMBOL | DIRECTION | STRATEGY (reason...) | Conf: XX% | Entry: X.XXXX | TP: X.XXXX
    pattern = r'\[(\d{2}:\d{2}:\d{2})\] (\w+) \| (\w+) \| (\w+) \((.+?)\) \| Conf: (\d+)% \| Entry: ([\d.]+) \| TP: ([\d.]+)'
    match = re.match(pattern, line.strip())
    
    if match:
        return {
            "time": match.group(1),
            "symbol": match.group(2),
            "direction": match.group(3),
            "strategy": match.group(4),
            "reason": match.group(5),
            "confidence": int(match.group(6)),
            "entry": float(match.group(7)),
            "tp": float(match.group(8))
        }
    return None

def load_candle_data(symbol, timeframe):
    """Load historical candle data from cTrader export."""
    tf_map = {"M5": "m5", "M15": "m15", "M30": "m30", "H1": "h1", "H4": "h4"}
    tf_key = tf_map.get(timeframe, "m5")
    
    config_path = os.path.join(DATA_FOLDER, symbol, "symbol_config.json")
    if not os.path.exists(config_path):
        return None
    
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        return data.get(tf_key, [])
    except:
        return None

def validate_signal(signal, candles):
    """
    Check if a signal would have hit TP or SL based on candle data.
    Returns: 'HIT_TP', 'HIT_SL', 'EXPIRED', 'IN_PROGRESS'
    """
    if not candles:
        return "NO_DATA", 0, None
    
    entry = signal['entry']
    tp = signal['tp']
    direction = signal['direction']
    
    # Calculate SL (inverse of TP distance for simplicity)
    tp_distance = abs(tp - entry)
    sl = entry + tp_distance if direction == "SELL" else entry - tp_distance
    
    # Get strategy timeframe info
    strategy = signal['strategy'].upper()
    if strategy in STRATEGY_TIMEFRAMES:
        max_candles = STRATEGY_TIMEFRAMES[strategy]['max_candles']
    else:
        max_candles = 5  # Default
    
    # Check each candle after signal time
    candles_checked = 0
    for candle in candles[-max_candles:]:  # Only check recent candles
        candles_checked += 1
        high = candle.get('high', 0)
        low = candle.get('low', 0)
        
        if direction == "BUY":
            if high >= tp:
                return "HIT_TP", candles_checked, candle.get('time')
            if low <= sl:
                return "HIT_SL", candles_checked, candle.get('time')
        else:  # SELL
            if low <= tp:
                return "HIT_TP", candles_checked, candle.get('time')
            if high >= sl:
                return "HIT_SL", candles_checked, candle.get('time')
    
    return "EXPIRED", candles_checked, None

def generate_report(signals, results):
    """Generate detailed performance report."""
    
    # Calculate stats by strategy
    stats = defaultdict(lambda: {"total": 0, "wins": 0, "losses": 0, "expired": 0, "no_data": 0})
    
    for signal, result in zip(signals, results):
        strategy = signal['strategy'].upper()
        stats[strategy]["total"] += 1
        
        if result[0] == "HIT_TP":
            stats[strategy]["wins"] += 1
        elif result[0] == "HIT_SL":
            stats[strategy]["losses"] += 1
        elif result[0] == "EXPIRED":
            stats[strategy]["expired"] += 1
        else:
            stats[strategy]["no_data"] += 1
    
    # Print report
    print("\n" + "═" * 60)
    print("  SIGNAL VALIDATION REPORT")
    print("  Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("═" * 60)
    
    print(f"\n{'Strategy':<15} | {'Signals':>8} | {'Wins':>5} | {'Losses':>6} | {'Win Rate':>8}")
    print("-" * 60)
    
    total_signals = 0
    total_wins = 0
    total_losses = 0
    
    for strategy, data in sorted(stats.items()):
        total = data["total"]
        wins = data["wins"]
        losses = data["losses"]
        validated = wins + losses
        win_rate = (wins / validated * 100) if validated > 0 else 0
        
        total_signals += total
        total_wins += wins
        total_losses += losses
        
        status = "✅" if win_rate >= 60 else "⚠️" if win_rate >= 40 else "❌"
        print(f"{strategy:<15} | {total:>8} | {wins:>5} | {losses:>6} | {win_rate:>6.1f}% {status}")
    
    print("-" * 60)
    overall_validated = total_wins + total_losses
    overall_rate = (total_wins / overall_validated * 100) if overall_validated > 0 else 0
    print(f"{'TOTAL':<15} | {total_signals:>8} | {total_wins:>5} | {total_losses:>6} | {overall_rate:>6.1f}%")
    
    print("\n" + "═" * 60)
    
    # Recommendations
    print("\n📊 ANALYSIS:")
    
    best_strategy = max(stats.items(), key=lambda x: x[1]["wins"] / max(x[1]["wins"] + x[1]["losses"], 1) if x[1]["total"] > 0 else 0, default=None)
    if best_strategy and best_strategy[1]["total"] > 0:
        bs_rate = best_strategy[1]["wins"] / max(best_strategy[1]["wins"] + best_strategy[1]["losses"], 1) * 100
        print(f"   Best Strategy: {best_strategy[0]} ({bs_rate:.1f}% win rate)")
    
    if overall_rate < 50:
        print("   ⚠️ Overall win rate below 50%. Consider tightening entry filters.")
    elif overall_rate >= 65:
        print("   ✅ Strong performance! System is profitable.")
    
    return stats

def generate_chart(signals, results, stats):
    """Generate performance chart."""
    if not CHARTS_AVAILABLE:
        print("\n⚠️ Charts not available. Install matplotlib: pip install matplotlib")
        return
    
    # Prepare data
    strategies = list(stats.keys())
    wins = [stats[s]["wins"] for s in strategies]
    losses = [stats[s]["losses"] for s in strategies]
    
    if not strategies:
        print("No data for charts.")
        return
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Bar chart - Wins vs Losses by Strategy
    x = range(len(strategies))
    width = 0.35
    ax1.bar([i - width/2 for i in x], wins, width, label='Wins', color='#2ecc71')
    ax1.bar([i + width/2 for i in x], losses, width, label='Losses', color='#e74c3c')
    ax1.set_xlabel('Strategy')
    ax1.set_ylabel('Signals')
    ax1.set_title('Win/Loss by Strategy')
    ax1.set_xticks(x)
    ax1.set_xticklabels(strategies, rotation=45)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # Pie chart - Overall distribution
    total_wins = sum(wins)
    total_losses = sum(losses)
    if total_wins + total_losses > 0:
        ax2.pie([total_wins, total_losses], 
                labels=['Wins', 'Losses'],
                colors=['#2ecc71', '#e74c3c'],
                autopct='%1.1f%%',
                startangle=90)
        ax2.set_title('Overall Win Rate')
    
    plt.tight_layout()
    
    # Save chart
    if not os.path.exists(REPORT_FOLDER):
        os.makedirs(REPORT_FOLDER)
    
    chart_path = os.path.join(REPORT_FOLDER, f"validation_chart_{datetime.now().strftime('%Y%m%d')}.png")
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"\n📈 Chart saved: {chart_path}")
    
    # Show chart
    plt.show()

def main():
    print("\n🔍 TITAN FUSION - SIGNAL VALIDATOR v1.0")
    print("=" * 50)
    
    # Find journal files
    if not os.path.exists(JOURNAL_FOLDER):
        print(f"❌ Journal folder not found: {JOURNAL_FOLDER}")
        return
    
    journal_files = [f for f in os.listdir(JOURNAL_FOLDER) if f.endswith('.txt')]
    if not journal_files:
        print("❌ No journal files found.")
        return
    
    print(f"📂 Found {len(journal_files)} journal file(s)")
    
    # Parse all signals
    all_signals = []
    for jf in sorted(journal_files):
        filepath = os.path.join(JOURNAL_FOLDER, jf)
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                signal = parse_journal_line(line)
                if signal:
                    signal['date'] = jf.replace('trading_journal_', '').replace('.txt', '')
                    all_signals.append(signal)
    
    print(f"📊 Parsed {len(all_signals)} signals")
    
    if not all_signals:
        print("No valid signals to validate.")
        return
    
    # Validate each signal
    print("\n⏳ Validating signals against market data...")
    results = []
    
    for signal in all_signals:
        strategy = signal['strategy'].upper()
        tf = STRATEGY_TIMEFRAMES.get(strategy, {}).get('tf', 'M5')
        candles = load_candle_data(signal['symbol'], tf)
        result = validate_signal(signal, candles)
        results.append(result)
    
    # Generate report
    stats = generate_report(all_signals, results)
    
    # Generate chart
    generate_chart(all_signals, results, stats)
    
    print("\n✅ Validation complete!")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
