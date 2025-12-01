import asyncio
import json
import websockets
import time
import threading

# Constants
APP_ID = 1089
DEFAULT_SYMBOL = "R_75"  # Volatility 75 Index

class DerivClient:
    def __init__(self, token, app_id=APP_ID, symbol=DEFAULT_SYMBOL):
        self.url = f"wss://ws.binaryws.com/websockets/v3?app_id={app_id}"
        self.token = token
        self.symbol = symbol
        self.ws = None
        self.is_connected = False
        self.is_reconnecting = False
        self.reconnect_attempts = 0
        self.max_reconnect_delay = 30
        self.balance = 0.0
        self.currency = "USD"
        self.account_id = ""
        self.on_tick_callback = None
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.ping_task = None

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
        
        # Store account info
        auth_data = data['authorize']
        self.account_id = auth_data['loginid']
        self.balance = float(auth_data['balance'])
        self.currency = auth_data['currency']
        
        print(f"   Account: {self.account_id} | Balance: {self.balance} {self.currency}")
        
        # Start ping keepalive
        if self.ping_task:
            self.ping_task.cancel()
        self.ping_task = asyncio.create_task(self._ping_loop())
        
        return True
    
    async def _ping_loop(self):
        """Send ping every 30 seconds to keep connection alive"""
        try:
            while self.is_connected:
                await asyncio.sleep(30)
                if self.ws and not self.ws.closed:
                    await self.ws.send(json.dumps({"ping": 1}))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"⚠️ Ping error: {e}")
    
    def get_balance(self):
        """Get current account balance"""
        return self.balance, self.currency

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
                        
                elif 'pong' in data:
                    # Keepalive response, connection healthy
                    pass
                    
                elif 'error' in data:
                    print(f"⚠️ API Error: {data['error']['message']}")
                    
        except websockets.exceptions.ConnectionClosed as e:
            print(f"🔌 Connection closed: {e}")
            self.is_connected = False
            
            # Auto-reconnect
            if not self.is_reconnecting:
                asyncio.create_task(self._reconnect())
        except Exception as e:
            print(f"❌ Listen error: {e}")
            self.is_connected = False
            if not self.is_reconnecting:
                asyncio.create_task(self._reconnect())
    
    async def _reconnect(self):
        """Reconnect with exponential backoff"""
        self.is_reconnecting = True
        
        while not self.is_connected and self.reconnect_attempts < 10:
            self.reconnect_attempts += 1
            delay = min(2 ** self.reconnect_attempts, self.max_reconnect_delay)
            
            print(f"🔄 Reconnecting in {delay}s (attempt {self.reconnect_attempts}/10)...")
            await asyncio.sleep(delay)
            
            try:
                success = await self.connect()
                if success:
                    print("✅ Reconnected successfully!")
                    self.reconnect_attempts = 0
                    self.is_reconnecting = False
                    
                    # Re-subscribe to ticks
                    await self.subscribe_ticks()
                    return
            except Exception as e:
                print(f"❌ Reconnect failed: {e}")
        
        if self.reconnect_attempts >= 10:
            print("❌ Max reconnection attempts reached. Manual restart required.")
        
        self.is_reconnecting = False

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
