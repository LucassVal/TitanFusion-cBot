#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
 TITAN FUSION - SIGNAL VALIDATOR v2.0
 Validates signals against actual closed positions from cTrader
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import re
from datetime import datetime
from collections import defaultdict

# Paths
DATA_FOLDER = r"C:\Users\Lucas Valério\Documents\TitanFusionAI"
JOURNAL_FOLDER = os.path.join(DATA_FOLDER, "Journal")
CLOSED_POSITIONS_FILE = os.path.join(DATA_FOLDER, "closed_positions.json")
REJECTED_SIGNALS_FILE = os.path.join(DATA_FOLDER, "rejected_signals.json")
REPORT_FOLDER = os.path.join(DATA_FOLDER, "Reports")

# Try to import matplotlib for charts (optional)
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for background running
    import matplotlib.pyplot as plt
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False


def load_closed_positions():
    """Load closed positions exported by cBot."""
    if not os.path.exists(CLOSED_POSITIONS_FILE):
        return []
    
    try:
        with open(CLOSED_POSITIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def load_rejected_signals():
    """Load rejected signals from Python brain."""
    if not os.path.exists(REJECTED_SIGNALS_FILE):
        return []
    
    try:
        with open(REJECTED_SIGNALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def generate_report():
    """
    Generate validation report based on ACTUAL closed positions.
    This is the real win/loss rate from cTrader.
    """
    closed = load_closed_positions()
    rejected = load_rejected_signals()
    
    print("\n" + "═" * 60)
    print("  TITAN FUSION - VALIDATION REPORT v2.0")
    print("  Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("═" * 60)
    
    if not closed:
        print("\n  ⚠️ No closed positions found.")
        print("  Waiting for cBot to export closed_positions.json...")
        print("  (Positions are exported when they close in cTrader)")
        return None
    
    # Calculate stats by close type
    stats = defaultdict(lambda: {"total": 0, "tp_hits": 0, "sl_hits": 0, "manual": 0, "pnl": 0.0})
    
    for pos in closed:
        strategy = pos.get("strategy", "UNKNOWN")
        close_type = pos.get("close_type", "UNKNOWN")
        pnl = float(pos.get("pnl", 0))
        
        stats[strategy]["total"] += 1
        stats[strategy]["pnl"] += pnl
        
        if close_type == "HIT_TP":
            stats[strategy]["tp_hits"] += 1
        elif close_type == "HIT_SL":
            stats[strategy]["sl_hits"] += 1
        else:
            stats[strategy]["manual"] += 1
    
    # Print results table
    print(f"\n{'Strategy':<15} | {'Closed':>7} | {'TP Hit':>6} | {'SL Hit':>6} | {'Win %':>6} | {'PnL':>10}")
    print("-" * 65)
    
    total_trades = 0
    total_wins = 0
    total_losses = 0
    total_pnl = 0.0
    
    for strategy, data in sorted(stats.items()):
        total = data["total"]
        wins = data["tp_hits"]
        losses = data["sl_hits"]
        pnl = data["pnl"]
        validated = wins + losses
        win_rate = (wins / validated * 100) if validated > 0 else 0
        
        total_trades += total
        total_wins += wins
        total_losses += losses
        total_pnl += pnl
        
        status = "✅" if win_rate >= 60 else "⚠️" if win_rate >= 40 else "❌"
        pnl_str = f"${pnl:+.2f}"
        print(f"{strategy:<15} | {total:>7} | {wins:>6} | {losses:>6} | {win_rate:>5.1f}% | {pnl_str:>10} {status}")
    
    print("-" * 65)
    overall_validated = total_wins + total_losses
    overall_rate = (total_wins / overall_validated * 100) if overall_validated > 0 else 0
    total_pnl_str = f"${total_pnl:+.2f}"
    print(f"{'TOTAL':<15} | {total_trades:>7} | {total_wins:>6} | {total_losses:>6} | {overall_rate:>5.1f}% | {total_pnl_str:>10}")
    
    print("\n" + "═" * 60)
    
    # Rejected signals summary
    if rejected:
        print(f"\n📋 REJECTED SIGNALS: {len(rejected)} blocked")
        reasons = defaultdict(int)
        for r in rejected:
            reasons[r.get("reason", "UNKNOWN")] += 1
        for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
            print(f"   - {reason}: {count}")
    
    # Generate chart if available
    if CHARTS_AVAILABLE and stats:
        generate_chart(stats, total_wins, total_losses, total_pnl)
    
    return stats


def generate_chart(stats, total_wins, total_losses, total_pnl):
    """Generate and save performance chart."""
    if not os.path.exists(REPORT_FOLDER):
        os.makedirs(REPORT_FOLDER)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # 1. Win/Loss by Strategy
    strategies = list(stats.keys())
    wins = [stats[s]["tp_hits"] for s in strategies]
    losses = [stats[s]["sl_hits"] for s in strategies]
    
    x = range(len(strategies))
    width = 0.35
    axes[0].bar([i - width/2 for i in x], wins, width, label='TP Hit', color='#2ecc71')
    axes[0].bar([i + width/2 for i in x], losses, width, label='SL Hit', color='#e74c3c')
    axes[0].set_xlabel('Strategy')
    axes[0].set_ylabel('Count')
    axes[0].set_title('Win/Loss by Strategy')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(strategies, rotation=45, ha='right')
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # 2. Overall Win Rate Pie
    if total_wins + total_losses > 0:
        axes[1].pie([total_wins, total_losses], 
                    labels=[f'Wins ({total_wins})', f'Losses ({total_losses})'],
                    colors=['#2ecc71', '#e74c3c'],
                    autopct='%1.1f%%',
                    startangle=90)
        axes[1].set_title('Overall Win Rate')
    else:
        axes[1].text(0.5, 0.5, 'No Data', ha='center', va='center')
        axes[1].set_title('Overall Win Rate')
    
    # 3. PnL by Strategy
    pnls = [stats[s]["pnl"] for s in strategies]
    colors = ['#2ecc71' if p >= 0 else '#e74c3c' for p in pnls]
    axes[2].bar(strategies, pnls, color=colors)
    axes[2].set_xlabel('Strategy')
    axes[2].set_ylabel('PnL ($)')
    axes[2].set_title(f'PnL by Strategy (Total: ${total_pnl:+.2f})')
    axes[2].tick_params(axis='x', rotation=45)
    axes[2].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    axes[2].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    chart_path = os.path.join(REPORT_FOLDER, f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n📈 Chart saved: {chart_path}")


def main():
    """Main entry point for Signal Validator."""
    print("\n🔍 TITAN FUSION - SIGNAL VALIDATOR v2.0")
    print("=" * 50)
    print(f"📂 Data Folder: {DATA_FOLDER}")
    print(f"📊 Closed Positions: {CLOSED_POSITIONS_FILE}")
    
    generate_report()
    
    print("\n✅ Validation complete!")


if __name__ == "__main__":
    main()
