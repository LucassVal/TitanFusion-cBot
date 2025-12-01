import os
import sys

# Version
VERSION = "2.0.0"

# Add Titan pro to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def show_banner():
    # Set console title
    os.system(f'title Titan Pro {VERSION} - Configuration')
    
    print("="*70)
    print(f"""
    ████████╗██╗████████╗ █████╗ ███╗   ██╗    ██████╗ ██████╗  ██████╗ 
    ╚══██╔══╝██║╚══██╔══╝██╔══██╗████╗  ██║    ██╔══██╗██╔══██╗██╔═══██╗
       ██║   ██║   ██║   ███████║██╔██╗ ██║    ██████╔╝██████╔╝██║   ██║
       ██║   ██║   ██║   ██╔══██║██║╚██╗██║    ██╔═══╝ ██╔══██╗██║   ██║
       ██║   ██║   ██║   ██║  ██║██║ ╚████║    ██║     ██║  ██║╚██████╔╝
       ╚═╝   ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ 
    """)
    print(f"    🚀 HYBRID GPU TRADING SYSTEM v{VERSION} - MULTI-STRATEGY OPTIMIZER 🚀")
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
    print("\n   SYSTEM")
    print("   ─────────────────────────")
    print("   [0] 🔄 UPDATE SYSTEM (Git Pull)")
    
    while True:
        try:
            choice = input("\n👉 Enter choice (0-8): ").strip()
            choice_num = int(choice)
            
            if choice_num == 0:
                print("\n🔄 Updating Titan Pro...")
                
                # Check if .git directory exists
                launcher_dir = os.path.dirname(os.path.abspath(__file__))
                git_dir = os.path.join(launcher_dir, '..', '.git')
                
                if not os.path.exists(git_dir):
                    print("\n⚠️  Git repository not detected!")
                    print("   This installation was done via the installer.")
                    print("\n   To update, run the installer again:")
                    print("   irm https://raw.githubusercontent.com/LucassVal/TitanFusion-cBot/main/install.ps1 | iex")
                    input("\nPress Enter to continue...")
                    continue
                
                result = os.system("git pull")
                if result == 0:
                    print("\n✅ Update complete! Please restart the launcher.")
                else:
                    print("\n❌ Update failed. Please check your git configuration.")
                input("Press Enter to exit...")
                sys.exit()
            
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

def configure_risk_management():
    print("\n🛡️ RISK MANAGEMENT CONFIGURATION:")
    print("   ─────────────────────────")
    
    # 1. Risk Per Trade
    while True:
        try:
            r = input("   👉 Risk per trade (%) [Default: 2.0]: ").strip()
            if not r:
                risk = 0.02
                break
            risk = float(r) / 100.0
            if 0.001 <= risk <= 0.10:
                break
            print("   ❌ Risk must be between 0.1% and 10%")
        except:
            print("   ❌ Invalid number")
            
    # 2. Daily Profit Goal
    while True:
        try:
            g = input("   👉 Daily Profit Goal ($) [Default: 50.0]: ").strip()
            if not g:
                daily_goal = 50.0
                break
            daily_goal = float(g)
            if daily_goal > 0:
                break
            print("   ❌ Goal must be positive")
        except:
            print("   ❌ Invalid number")

    # 3. Max Daily Loss
    while True:
        try:
            l = input("   👉 Max Daily Loss ($) [Default: 25.0]: ").strip()
            if not l:
                max_loss = 25.0
                break
            max_loss = float(l)
            if max_loss > 0:
                break
            print("   ❌ Loss limit must be positive")
        except:
            print("   ❌ Invalid number")
            
    # 4. Total Profit Target
    while True:
        try:
            t = input("   👉 Total Profit Target ($) [Default: 1000.0]: ").strip()
            if not t:
                total_target = 1000.0
                break
            total_target = float(t)
            if total_target > 0:
                break
            print("   ❌ Target must be positive")
        except:
            print("   ❌ Invalid number")
            
    print(f"\n✅ Risk Configured: {risk*100}% Risk | Goal: ${daily_goal} | Max Loss: ${max_loss}")
    return risk, daily_goal, max_loss, total_target

def main():
    show_banner()
    
    # 1. Market selection
    symbol, market_name = select_market()
    
    # 2. Timeframe selection
    tf_pandas, tf_name, tf_minutes = select_timeframe()
    
    # 3. Risk Management
    risk, daily_goal, max_loss, total_target = configure_risk_management()
    
    # 4. Auto-detect Data Source
    is_synthetic = symbol.startswith('R_')  # R_75, R_100, etc
    
    if is_synthetic:
        data_source = 'deriv'
        source_name = 'Deriv (Synthetic)'
    else:
        data_source = 'dukascopy'
        source_name = 'Dukascopy (Real Market)'
    
    # Initialize working capital variables
    working_capital = 50.0
    account_balance = 50.0
    currency = "USD"
    
    # API TOKEN CHECK & BALANCE FETCH (for Deriv only)
    if data_source == 'deriv':
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "titan_config.json")
        import json
        
        token = None
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    token = config.get('deriv_token')
            except:
                pass
        
        if not token:
            print("\n🔑 DERIV API TOKEN REQUIRED")
            print("   Please enter your Deriv API Token (Settings -> API Token -> Read/Trade)")
            token = input("👉 API Token: ").strip()
            
            if token:
                save = input("   Save token for future use? (y/n): ").strip().lower()
                if save == 'y':
                    with open(config_file, 'w') as f:
                        json.dump({'deriv_token': token}, f)
                    print("   ✅ Token saved securely.")
        
        if not token:
            print("❌ API Token is required for Deriv trading!")
            return
        
        # Connect to get real balance
        print("\n🔌 Connecting to Deriv to fetch account balance...")
        from deriv_client import DerivClient
        import time
        
        temp_client = DerivClient(token, symbol=symbol)
        connected = temp_client.start(lambda t: None)
        
        if not connected:
            print("❌ Failed to connect to Deriv API")
            return
        
        time.sleep(1)  # Wait for auth
        account_balance, currency = temp_client.get_balance()
        
        print(f"\n💰 ACCOUNT BALANCE: {account_balance} {currency}")
        print("\n📊 WORKING CAPITAL SELECTION:")
        print("   How much of your balance do you want to use for trading?")
        print(f"   Available: {account_balance} {currency}")
        
        # Working capital selection
        while True:
            try:
                wc_input = input(f"\n👉 Enter amount to trade (or % of balance, e.g., '50%'): ").strip()
                
                if '%' in wc_input:
                    pct = float(wc_input.replace('%', '').strip()) / 100.0
                    working_capital = account_balance * pct
                else:
                    working_capital = float(wc_input)
                
                if 0 < working_capital <= account_balance:
                    pct_used = (working_capital / account_balance) * 100
                    print(f"\n✅ Working Capital: {working_capital:.2f} {currency} ({pct_used:.1f}% of account)")
                    break
                else:
                    print(f"❌ Amount must be between 0 and {account_balance}")
            except:
                print("❌ Invalid input. Try '50' or '50%'")
        
        # Set token for titan_hybrid
        import titan_hybrid
        titan_hybrid.API_TOKEN = token
    
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
            filepath = manager.update_dukascopy(symbol=symbol, months=3, force=True)
        else:
            filepath = manager.update_deriv(symbol=symbol, months=3, force=True)
        
        if not filepath:
            print("❌ Download failed! Cannot proceed.")
            return
        
        print(f"✅ Downloaded 3 months of {symbol}")
    
    # Final confirmation
    print("\n" + "="*70)
    print(f"📌 FINAL CONFIGURATION:")
    print(f"   Market:      {market_name}")
    print(f"   Symbol:      {symbol}")
    if data_source == 'deriv':
        print(f"   Account:     {account_balance} {currency}")
        print(f"   Working Cap: {working_capital:.2f} {currency} ({(working_capital/account_balance)*100:.1f}%)")
    print(f"   Timeframe:   {tf_name}")
    print(f"   Risk:        {risk*100:.1f}% per trade")
    print(f"   Daily Goal:  ${daily_goal}")
    print(f"   Max Loss:    ${max_loss}")
    print("="*70)
    
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
    
    # Pass Risk Settings and Working Capital
    titan_hybrid.RISK_PER_TRADE = risk
    titan_hybrid.DAILY_PROFIT_GOAL = daily_goal
    titan_hybrid.MAX_DAILY_LOSS = max_loss
    titan_hybrid.TOTAL_PROFIT_TARGET = total_target
    titan_hybrid.WORKING_CAPITAL = working_capital
    titan_hybrid.ACCOUNT_BALANCE = account_balance
    
    run_live_trading()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to exit...")
