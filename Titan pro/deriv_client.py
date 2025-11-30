import asyncio
import json
import websockets
import time
import threading

# Constants
APP_ID = 1089
DEFAULT_TOKEN = "f6iBrpnmPI8tXUI"
DEFAULT_SYMBOL = "R_75"  # Volatility 75 Index

class DerivClient:
    def __init__(self, token=DEFAULT_TOKEN, app_id=APP_ID, symbol=DEFAULT_SYMBOL):
        self.url = f"wss://ws.binaryws.com/websockets/v3?app_id={app_id}"
        self.token = token
        self.symbol = symbol
        self.ws = None
        self.is_connected = False
        self.on_tick_callback = None
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def connect(self):
        print(f"🔌 Connecting to Deriv API...")
        try:
            self.ws = await websockets.connect(self.url)
            self.is_connected = True
            
            if await self.authorize():
                print("✅ Authorized successfully")
                return True
            else:
                print("❌ Authorization failed")
                return False
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return False

    async def authorize(self):
        req = {"authorize": self.token}
        await self.ws.send(json.dumps(req))
        res = await self.ws.recv()
        data = json.loads(res)
        if 'error' in data:
            print(f"Auth Error: {data['error']['message']}")
            return False
        
        print(f"   Account: {data['authorize']['loginid']} | Balance: {data['authorize']['balance']} {data['authorize']['currency']}")
        return True

    async def subscribe_ticks(self):
        req = {"ticks": self.symbol, "subscribe": 1}
        await self.ws.send(json.dumps(req))
        print(f"📡 Subscribed to {self.symbol} ticks")
        
        asyncio.run_coroutine_threadsafe(self._listen(), self.loop)

    async def _listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                
                if 'tick' in data:
                    tick = data['tick']
                    if self.on_tick_callback:
                        self.on_tick_callback(tick)
                        
                elif 'error' in data:
                    print(f"⚠️ API Error: {data['error']['message']}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed")
            self.is_connected = False

    def start(self, on_tick):
        self.on_tick_callback = on_tick
        future = asyncio.run_coroutine_threadsafe(self.connect(), self.loop)
        connected = future.result()
        
        if connected:
            asyncio.run_coroutine_threadsafe(self.subscribe_ticks(), self.loop)
            return True
        return False

if __name__ == "__main__":
    def print_tick(t):
        print(f"Tick: {t['quote']} @ {t['epoch']}")

    client = DerivClient()
    client.start(print_tick)
    
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
