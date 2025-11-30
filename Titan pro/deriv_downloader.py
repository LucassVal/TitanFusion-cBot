import asyncio
import json
import pandas as pd
from datetime import datetime
import websockets

# Constants
APP_ID = 1089
API_TOKEN = "f6iBrpnmPI8tXUI"
SYMBOL = "R_75"  # Volatility 75 Index (synthetic, 24/7)
TIMEFRAME = "60"

class DerivDownloader:
    def __init__(self, token, app_id=1089):
        self.url = f"wss://ws.binaryws.com/websockets/v3?app_id={app_id}"
        self.token = token

    async def connect(self):
        self.ws = await websockets.connect(self.url)
        await self.authorize()

    async def authorize(self):
        auth_req = {"authorize": self.token}
        await self.ws.send(json.dumps(auth_req))
        response = await self.ws.recv()
        data = json.loads(response)
        if 'error' in data:
            print(f"Auth Error: {data['error']['message']}")
            return False
        print(f"Authorized: {data['authorize']['email']}")
        return True

    async def get_candles(self, symbol, style="candles", end="latest", count=1000, granularity=60):
        # granularity 60 = 1 minute
        req = {
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": end,
            "style": style,
            "granularity": granularity
        }
        await self.ws.send(json.dumps(req))
        response = await self.ws.recv()
        data = json.loads(response)
        
        if 'error' in data:
            print(f"Error fetching candles: {data['error']['message']}")
            return None
            
        return data.get('candles')

    async def download_history(self, symbol, output_file="deriv_data.csv", total_candles=50000):
        if not await self.authorize():
            return

        print(f"Downloading up to {total_candles} M1 candles for {symbol}...")
        
        all_candles = []
        batch_size = 5000  # Deriv API limit per call
        current_end = "latest"
        
        # Loop to fetch multiple batches
        for batch_num in range((total_candles // batch_size) + 1):
            if len(all_candles) >= total_candles:
                break
                
            print(f"Fetching batch {batch_num + 1}...")
            candles = await self.get_candles(symbol, count=min(batch_size, total_candles - len(all_candles)), end=current_end, granularity=60)
            
            if not candles or len(candles) == 0:
                print(f"No more data available. Got {len(all_candles)} total candles.")
                break
            
            all_candles.extend(candles)
            
            # Set the 'end' for next call to be the oldest timestamp from this batch minus 1 second
            # This allows us to paginate backwards in time
            oldest_epoch = min(c['epoch'] for c in candles)
            current_end = str(oldest_epoch - 60)  # Go back 1 minute
            
            print(f"  Retrieved {len(candles)} candles. Total: {len(all_candles)}")
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        if all_candles:
            # Remove duplicates and sort by time
            unique_candles = {c['epoch']: c for c in all_candles}.values()
            sorted_candles = sorted(unique_candles, key=lambda x: x['epoch'])
            
            df = pd.DataFrame(sorted_candles)
            df['time'] = pd.to_datetime(df['epoch'], unit='s')
            df = df[['time', 'open', 'high', 'low', 'close', 'epoch']]
            
            # Save to CSV in the same directory as the script
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            save_path = os.path.join(script_dir, output_file)
            
            df.to_csv(save_path, index=False)
            print(f"Saved {len(df)} candles to {save_path}")
        else:
            print("No candles received.")
    
    async def close(self):
        if self.ws:
            await self.ws.close()

async def main():
    downloader = DerivDownloader(token=API_TOKEN)
    await downloader.connect()
    try:
        # frxXAUUSD is the symbol for Gold/USD on Deriv
        # Request 50,000 candles (~35 days of M1 data, 24/5 market)
        await downloader.download_history(SYMBOL, total_candles=50000)
    finally:
        await downloader.close()

if __name__ == "__main__":
    asyncio.run(main())
