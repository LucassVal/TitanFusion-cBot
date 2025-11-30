"""
Dukascopy Historical Data Downloader
Downloads tick/candle data from Dukascopy Swiss Bank
For institutional-grade backtesting
"""

import pandas as pd
from datetime import datetime, timedelta
import requests
import struct
import lzma
import os

class DukascopyDownloader:
    """
    Download historical data from Dukascopy
    Format: Tick data or aggregated candles
    """
    
    BASE_URL = "https://datafeed.dukascopy.com/datafeed"
    
    # Symbol mapping (Dukascopy uses different names)
    SYMBOL_MAP = {
        'XAUUSD': 'XAUUSD',  # Gold
        'EURUSD': 'EURUSD',
        'GBPUSD': 'GBPUSD',
        'USDJPY': 'USDJPY',
        'AUDUSD': 'AUDUSD',
        'USDCHF': 'USDCHF'
    }
    
    def __init__(self, symbol='XAUUSD'):
        self.symbol = self.SYMBOL_MAP.get(symbol, symbol)
        
    def download_ticks(self, start_date, end_date):
        """
        Download tick data from Dukascopy
        Returns: DataFrame with columns [time, bid, ask, bid_volume, ask_volume]
        """
        print(f"📥 Downloading {self.symbol} ticks from {start_date} to {end_date}")
        
        all_ticks = []
        current = start_date
        
        while current <= end_date:
            # Dukascopy stores data in hourly .bi5 files
            # Format: {BASE_URL}/{SYMBOL}/{YEAR}/{MONTH}/{DAY}/{HOUR}h_ticks.bi5
            year = current.year
            month = str(current.month - 1).zfill(2)  # Dukascopy months are 0-indexed
            day = str(current.day).zfill(2)
            hour = str(current.hour).zfill(2)
            
            url = f"{self.BASE_URL}/{self.symbol}/{year}/{month}/{day}/{hour}h_ticks.bi5"
            
            try:
                ticks = self._download_hour(url, current)
                if ticks:
                    all_ticks.extend(ticks)
                    print(f"   ✓ {current.strftime('%Y-%m-%d %H:00')} - {len(ticks)} ticks")
                    
            except Exception as e:
                print(f"   ✗ {current.strftime('%Y-%m-%d %H:00')} - Error: {e}")
                
            # Next hour
            current += timedelta(hours=1)
            
        if not all_ticks:
            print("❌ No data downloaded!")
            return pd.DataFrame()
            
        # Convert to DataFrame
        df = pd.DataFrame(all_ticks, columns=['time', 'bid', 'ask', 'bid_vol', 'ask_vol'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        
        print(f"✅ Downloaded {len(df):,} ticks")
        return df
    
    def _download_hour(self, url, timestamp):
        """Download and decompress one hour of tick data"""
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            return None
            
        # Decompress LZMA
        try:
            data = lzma.decompress(response.content)
        except:
            return None
        
        # Parse binary format
        # Each tick: 20 bytes
        # 4 bytes: timestamp offset (ms from hour start)
        # 4 bytes: bid price (int * point)
        # 4 bytes: ask price (int * point)
        # 4 bytes: bid volume
        # 4 bytes: ask volume
        
        ticks = []
        point = 0.00001 if self.symbol != 'XAUUSD' else 0.01  # Gold has different pip value
        
        for i in range(0, len(data), 20):
            if i + 20 > len(data):
                break
                
            chunk = data[i:i+20]
            
            # Unpack binary
            time_offset, bid_int, ask_int, bid_vol, ask_vol = struct.unpack('>IIIff', chunk)
            
            # Convert to actual values
            tick_time = int(timestamp.timestamp() * 1000) + time_offset
            bid = bid_int * point
            ask = ask_int * point
            
            ticks.append([tick_time, bid, ask, bid_vol, ask_vol])
            
        return ticks
    
    def download_candles(self, start_date, end_date, timeframe='1H'):
        """
        Download and aggregate to candles
        timeframe: pandas resample string ('1min', '5min', '15min', '1H', etc.)
        """
        print(f"📊 Downloading {self.symbol} {timeframe} candles...")
        
        # Download ticks
        df_ticks = self.download_ticks(start_date, end_date)
        
        if df_ticks.empty:
            return df_ticks
            
        # Use mid price for OHLC
        df_ticks['price'] = (df_ticks['bid'] + df_ticks['ask']) / 2
        
        # Set time as index
        df_ticks.set_index('time', inplace=True)
        
        # Resample to candles
        print(f"🔄 Aggregating to {timeframe} candles...")
        
        df_candles = df_ticks['price'].resample(timeframe).agg([
            ('open', 'first'),
            ('high', 'max'),
            ('low', 'min'),
            ('close', 'last')
        ]).dropna()
        
        print(f"✅ Created {len(df_candles):,} {timeframe} candles")
        
        return df_candles.reset_index()
    
    def save_to_csv(self, df, filename):
        """Save DataFrame to CSV"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        
        df.to_csv(filepath, index=False)
        print(f"💾 Saved to {filepath}")
        
        return filepath


def main():
    """
    Download 6 months of XAUUSD data for stress testing
    """
    symbol = 'XAUUSD'
    timeframe = '1min'  # M1 data
    
    # 6 months back from today
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months
    
    print("="*70)
    print("DUKASCOPY DOWNLOADER - TITAN PRO")
    print("="*70)
    print(f"Symbol: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Duration: 6 months (Optimized for speed + robustness)")
    print("="*70)
    
    downloader = DukascopyDownloader(symbol=symbol)
    
    try:
        # Download candles
        df = downloader.download_candles(start_date, end_date, timeframe=timeframe)
        
        if not df.empty:
            # Save
            filename = f"dukascopy_{symbol}_{timeframe}_2years.csv"
            downloader.save_to_csv(df, filename)
            
            # Stats
            print("\n📈 DATA SUMMARY:")
            print(f"   Total Candles: {len(df):,}")
            print(f"   Date Range: {df['time'].min()} to {df['time'].max()}")
            print(f"   Price Range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
            print(f"   File Size: {os.path.getsize(os.path.join(os.path.dirname(__file__), filename)) / 1024 / 1024:.2f} MB")
            
            print("\n✅ Download Complete! Ready for Titan Pro stress testing.")
            
        else:
            print("\n❌ Download failed. Please check your internet connection.")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Download cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
