import os
import sys

# Add Titan pro to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def show_banner():
    print("="*70)
    print("""
    ████████╗██╗████████╗ █████╗ ███╗   ██╗    ██████╗ ██████╗  ██████╗ 
    ╚══██╔══╝██║╚══██╔══╝██╔══██╗████╗  ██║    ██╔══██╗██╔══██╗██╔═══██╗
       ██║   ██║   ██║   ███████║██╔██╗ ██║    ██████╔╝██████╔╝██║   ██║
       ██║   ██║   ██║   ██╔══██║██║╚██╗██║    ██╔═══╝ ██╔══██╗██║   ██║
       ██║   ██║   ██║   ██║  ██║██║ ╚████║    ██║     ██║  ██║╚██████╔╝
       ╚═╝   ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ 
    """)
    print("    🚀 HYBRID GPU TRADING SYSTEM - MULTI-STRATEGY OPTIMIZER 🚀")
    print("="*70)

def select_market():
    print("\n📊 SELECT MARKET:")
    print("\n   SYNTHETIC INDICES (24/7)")
    print("   ─────────────────────────")
    print("   [1] Volatility 75 Index  (R_75)")
    print("   [2] Volatility 100 Index (R_100)")
    print("   [3] Volatility 25 Index  (R_25)")
    print("   [4] Volatility 50 Index  (R_50)")
    
    print("\n   REAL MARKETS (Forex)")
    print("   ─────────────────────────")
    print("   [5] EUR/USD")
    print("   [6] USD/JPY")
    print("   [7] XAU/USD (Gold)")
    print("   [8] GBP/USD")
    
    while True:
        try:
            choice = input("\n👉 Enter choice (1-8): ").strip()
            choice_num = int(choice)
            
            markets = {
                1: ("R_75", "Volatility 75 Index"),
                2: ("R_100", "Volatility 100 Index"),
                3: ("R_25", "Volatility 25 Index"),
                4: ("R_50", "Volatility 50 Index"),
                5: ("frxEURUSD", "EUR/USD"),
                6: ("frxUSDJPY", "USD/JPY"),
                7: ("frxXAUUSD", "XAU/USD (Gold)"),
                8: ("frxGBPUSD", "GBP/USD")
            }
            
            if choice_num in markets:
                symbol, name = markets[choice_num]
                print(f"\n✅ Selected: {name}")
                return symbol, name
            else:
                print("❌ Invalid choice! Please enter 1-8")
        except ValueError:
            print("❌ Invalid input! Please enter a number 1-8")

def select_timeframe():
    print("\n⏰ SELECT TIMEFRAME:")
    print("   ─────────────────────────")
    print("   [1] M1  (1 minute)")
    print("   [2] M5  (5 minutes)")
    print("   [3] M15 (15 minutes)")
    print("   [4] M30 (30 minutes)")
    print("   [5] H1  (1 hour)")
    
    while True:
        try:
            choice = input("\n👉 Enter choice (1-5): ").strip()
            choice_num = int(choice)
            
            timeframes = {
                1: ("1min", "M1", 1),
                2: ("5min", "M5", 5),
                3: ("15min", "M15", 15),
                4: ("30min", "M30", 30),
                5: ("1H", "H1", 60)
            }
            
            if choice_num in timeframes:
                tf_pandas, tf_name, tf_minutes = timeframes[choice_num]
                print(f"\n✅ Selected: {tf_name}")
                return tf_pandas, tf_name, tf_minutes
            else:
                print("❌ Invalid choice! Please enter 1-5")
        except ValueError:
            print("❌ Invalid input! Please enter a number 1-5")

def select_data_source():
    print("\n📁 SELECT DATA SOURCE:")
    print("   ─────────────────────────")
    print("   [1] Dukascopy (Institutional, 6 months history)")
    print("   [2] Deriv     (Live API, 3 months history)")
    
    while True:
        try:
            choice = input("\n👉 Enter choice (1-2): ").strip()
            choice_num = int(choice)
            
            sources = {
                1: ("dukascopy", "Dukascopy (Institutional)"),
                2: ("deriv", "Deriv (Live API)")
            }
            
            if choice_num in sources:
                source, name = sources[choice_num]
                print(f"\n✅ Selected: {name}")
                return source
            else:
                print("❌ Invalid choice! Please enter 1-2")
        except ValueError:
            print("❌ Invalid input! Please enter a number 1-2")

def main():
    show_banner()
    
    # Market selection FIRST
    symbol, market_name = select_market()
    
    # Timeframe selection
    tf_pandas, tf_name, tf_minutes = select_timeframe()
    
    # AUTO-DETECT: Real ou Sintético
    is_synthetic = symbol.startswith('R_')  # R_75, R_100, etc
    
    if is_synthetic:
        data_source = 'deriv'
        source_name = 'Deriv (Synthetic)'
    else:
        data_source = 'dukascopy'
        source_name = 'Dukascopy (Real Market)'
    
    print("\n" + "="*70)
    print(f"📌 CONFIGURATION:")
    print(f"   Market:      {market_name}")
    print(f"   Symbol:      {symbol}")
    print(f"   Type:        {'SYNTHETIC' if is_synthetic else 'REAL'}")
    print(f"   Data Source: {source_name} (auto-detected)")
    print(f"   Timeframe:   {tf_name}")
    print(f"   Balance:     $50")
    print(f"   Risk:        2% per trade")
    print(f"   Strategies:  Scalper + Breakout + Pullback")
    print("="*70)
    
    # Check/download data AUTOMATICALLY
    from data_manager import DataManager
    manager = DataManager()
    
    print(f"\n🔍 Checking {data_source.upper()} data for {symbol}...")
    
    # Check if we have data for THIS SPECIFIC symbol
    cache_key = f"{data_source}_{symbol}"
    needs_download = True
    
    if cache_key in manager.cache:
        last_update = manager.cache[cache_key].get('last_update')
        if last_update:
            from datetime import datetime
            last_date = datetime.fromisoformat(last_update)
            age_days = (datetime.now() - last_date).days
            
            if age_days < 7:
                needs_download = False
                print(f"✅ Fresh data found ({age_days} days old)")
    
    if needs_download:
        print(f"📥 Downloading 3 months of {symbol} from {source_name}...")
        
        if data_source == 'dukascopy':
            # Download from Dukascopy
            filepath = manager.update_dukascopy(symbol=symbol, months=3, force=True)
        else:
            # Download from Deriv
            filepath = manager.update_deriv(symbol=symbol, months=3, force=True)
        
        if not filepath:
            print("❌ Download failed! Cannot proceed.")
            return
        
        print(f"✅ Downloaded 3 months of {symbol}")
    
    # Final confirmation
    confirm = input("\n✅ Start trading with these settings? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("\n❌ Cancelled. Exiting...")
        return
    
    print("\n🚀 Starting Titan Pro Hybrid System...")
    print("   Initializing dual GPU engines...")
    
    # Launch main system
    from titan_hybrid import run_live_trading
    import titan_hybrid
    
    # Update global settings
    titan_hybrid.SELECTED_SYMBOL = symbol
    titan_hybrid.SELECTED_TIMEFRAME = tf_pandas
    titan_hybrid.SELECTED_TF_MINUTES = tf_minutes
    titan_hybrid.DATA_SOURCE = data_source
    
    run_live_trading()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
