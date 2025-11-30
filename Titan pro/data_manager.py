"""
Data Manager for Titan Pro
Handles Dukascopy and Deriv data sources
Automatic weekly updates
"""

import os
import json
from datetime import datetime, timedelta
import pandas as pd

class DataManager:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_file = os.path.join(self.script_dir, "data_cache.json")
        self.load_cache()
    
    def load_cache(self):
        """Load data update history"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
        else:
            self.cache = {
                'dukascopy': {
                    'last_update': None,
                    'file': None,
                    'candles': 0
                },
                'deriv': {
                    'last_update': None,
                    'file': None,
                    'candles': 0
                }
            }
    
    def save_cache(self):
        """Save data update history"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def needs_update(self, source='dukascopy', days=7):
        """Check if data needs update (older than X days)"""
        last_update = self.cache[source]['last_update']
        
        if not last_update:
            return True
        
        last_date = datetime.fromisoformat(last_update)
        age_days = (datetime.now() - last_date).days
        
        return age_days >= days
    
    def update_dukascopy(self, symbol='XAUUSD', months=3, force=False):
        """Update Dukascopy data for specific symbol"""
        cache_key = f"dukascopy_{symbol}"
        
        if not force and cache_key in self.cache:
            last_update = self.cache[cache_key].get('last_update')
            if last_update:
                last_date = datetime.fromisoformat(last_update)
                age_days = (datetime.now() - last_date).days
                
                if age_days < 7:
                    print(f"⏭️ {symbol} data is recent (updated {age_days} days ago)")
                    print(f"   Use force=True to re-download")
                    return self.cache[cache_key].get('file')
        
        print(f"📥 Downloading {symbol} from Dukascopy ({months} months)...")
        
        from dukascopy_downloader import DukascopyDownloader
        
        downloader = DukascopyDownloader(symbol=symbol)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)
        
        df = downloader.download_candles(start_date, end_date, timeframe='1min')
        
        if df.empty:
            print("❌ Download failed!")
            return None
        
        # Save
        filename = f"dukascopy_{symbol}_M1_{months}months.csv"
        filepath = downloader.save_to_csv(df, filename)
        
        # Update cache with symbol-specific key
        self.cache[cache_key] = {
            'last_update': datetime.now().isoformat(),
            'file': filepath,
            'candles': len(df),
            'symbol': symbol,
            'months': months,
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        }
        self.save_cache()
        
        print(f"✅ {symbol} updated: {len(df):,} candles")
        return filepath
    
    def update_deriv(self, symbol='R_75', months=3, force=False):
        """Update Deriv data for specific symbol"""
        cache_key = f"deriv_{symbol}"
        
        if not force and cache_key in self.cache:
            last_update = self.cache[cache_key].get('last_update')
            if last_update:
                last_date = datetime.fromisoformat(last_update)
                age_days = (datetime.now() - last_date).days
                
                if age_days < 7:
                    print(f"⏭️ {symbol} data is recent (updated {age_days} days ago)")
                    return self.cache[cache_key].get('file')
        
        print(f"📥 Downloading {symbol} from Deriv ({months} months)...")
        
        # Calculate candles needed (months * 30 days * 24 hours * 60 minutes)
        total_candles = months * 30 * 24 * 60
        
        # Use deriv_downloader
        import deriv_downloader
        import asyncio
        
        # Temporarily override symbol
        original_symbol = deriv_downloader.SYMBOL
        deriv_downloader.SYMBOL = symbol
        
        try:
            asyncio.run(deriv_downloader.main())
        finally:
            deriv_downloader.SYMBOL = original_symbol
        
        # Check if file was created
        filename = f"deriv_{symbol}_M1_{months}months.csv"
        filepath = os.path.join(self.script_dir, "deriv_data.csv")
        
        if os.path.exists(filepath):
            # Rename to symbol-specific
            new_filepath = os.path.join(self.script_dir, filename)
            import shutil
            shutil.move(filepath, new_filepath)
            
            df = pd.read_csv(new_filepath)
            
            self.cache[cache_key] = {
                'last_update': datetime.now().isoformat(),
                'file': new_filepath,
                'candles': len(df),
                'symbol': symbol,
                'months': months
            }
            self.save_cache()
            
            print(f"✅ {symbol} updated: {len(df):,} candles")
            return new_filepath
        
        return None
    
    def get_data(self, source='dukascopy', auto_update=True):
        """Get data (auto-update if needed)"""
        if auto_update and self.needs_update(source, days=7):
            print(f"🔄 Data is old, auto-updating {source}...")
            if source == 'dukascopy':
                self.update_dukascopy()
            else:
                self.update_deriv()
        
        filepath = self.cache[source]['file']
        
        if not filepath or not os.path.exists(filepath):
            print(f"⚠️ No {source} data found. Run update first.")
            return None
        
        print(f"📂 Loading {source} data: {self.cache[source]['candles']:,} candles")
        df = pd.read_csv(filepath)
        df['time'] = pd.to_datetime(df['time'])
        
        return df
    
    def show_status(self):
        """Show data status"""
        print("\n" + "="*70)
        print("📊 DATA MANAGER STATUS")
        print("="*70)
        
        for source in ['dukascopy', 'deriv']:
            info = self.cache[source]
            print(f"\n{source.upper()}:")
            
            if info['last_update']:
                last = datetime.fromisoformat(info['last_update'])
                age = (datetime.now() - last).days
                
                print(f"   Last Update: {last.strftime('%Y-%m-%d %H:%M')} ({age} days ago)")
                print(f"   Candles: {info['candles']:,}")
                print(f"   File: {os.path.basename(info['file']) if info['file'] else 'None'}")
                
                if age >= 7:
                    print(f"   ⚠️ OUTDATED (>7 days) - Update recommended")
                else:
                    print(f"   ✅ Fresh data")
            else:
                print(f"   ❌ No data - Download required")
        
        print("="*70 + "\n")


if __name__ == "__main__":
    manager = DataManager()
    manager.show_status()
    
    print("\nOptions:")
    print("[1] Update Dukascopy (6 months)")
    print("[2] Update Deriv (3 months)")
    print("[3] Force update both")
    print("[4] Show status")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        manager.update_dukascopy(months=6)
    elif choice == '2':
        manager.update_deriv()
    elif choice == '3':
        manager.update_dukascopy(force=True)
        manager.update_deriv()
    elif choice == '4':
        manager.show_status()
