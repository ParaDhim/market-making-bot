"""
Collect live market data from Kraken WebSocket API.
Saves trades and quotes to CSV files for later use.
Handles connection issues with automatic reconnection.
"""

import asyncio
import json
import websockets
import ssl
import pandas as pd
from datetime import datetime
import os
import signal
import sys
import certifi


class KrakenDataCollector:
    def __init__(self, output_dir='data/live', symbol='BTC/USD'):
        self.output_dir = output_dir
        self.symbol = symbol
        os.makedirs(output_dir, exist_ok=True)
        
        self.trades = []
        self.quotes = []
        self.running = True
        self.connection_attempts = 0
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully."""
        print('\n\nShutting down gracefully...')
        self.running = False
        
    async def collect_data(self, duration_minutes=60):
        """
        Connect to Kraken WebSocket and collect data.
        
        Args:
            duration_minutes: How long to collect data (default 60 minutes)
        """
        kraken_ws_url = "wss://ws.kraken.com"
        
        print(f"Connecting to Kraken WebSocket...")
        print(f"Symbol: {self.symbol}")
        print(f"Will collect data for {duration_minutes} minutes")
        print("Press Ctrl+C to stop early\n")
        
        # Create SSL context to handle certificate verification
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        start_time = datetime.now()
        message_count = 0
        
        try:
            # Attempt connection with retries
            for attempt in range(3):
                try:
                    async with websockets.connect(
                        kraken_ws_url,
                        ssl=ssl_context,
                        ping_interval=20,
                        ping_timeout=10,
                        close_timeout=10,
                        max_size=10_000_000
                    ) as ws:
                        print(f"✓ Connected to Kraken WebSocket (Attempt {attempt + 1})\n")
                        
                        # Subscribe to ticker
                        await ws.send(json.dumps({
                            "event": "subscribe",
                            "pair": [self.symbol],
                            "subscription": {"name": "ticker"}
                        }))
                        
                        # Subscribe to trades
                        await ws.send(json.dumps({
                            "event": "subscribe",
                            "pair": [self.symbol],
                            "subscription": {"name": "trade"}
                        }))
                        
                        print("✓ Subscribed to ticker and trade channels\n")
                        
                        async for message in ws:
                            if not self.running:
                                print("Stop signal received.")
                                break
                                
                            # Check duration
                            elapsed = (datetime.now() - start_time).total_seconds()
                            if elapsed > duration_minutes * 60:
                                print(f"\n{duration_minutes} minutes elapsed. Stopping collection.")
                                self.running = False
                                break
                            
                            try:
                                data = json.loads(message)
                            except json.JSONDecodeError:
                                continue
                            
                            # Handle system messages
                            if isinstance(data, dict):
                                if 'event' in data:
                                    event = data.get('event')
                                    if event in ['subscriptionStatus', 'systemStatus']:
                                        status = data.get('status', 'unknown')
                                        if status == 'error':
                                            print(f"Subscription error: {data.get('errorMessage', 'unknown')}")
                                    continue
                            
                            # Handle arrays (actual data)
                            if not isinstance(data, list):
                                continue
                            
                            message_count += 1
                            timestamp = datetime.now().timestamp() * 1e9
                            
                            try:
                                # Check if it's ticker data (has OHLC)
                                if len(data) > 1 and isinstance(data[1], dict):
                                    ticker_data = data[1]
                                    
                                    if 'b' in ticker_data and 'a' in ticker_data:
                                        # Ticker format
                                        bid_price = float(ticker_data['b'][0])
                                        bid_volume = float(ticker_data['b'][1])
                                        ask_price = float(ticker_data['a'][0])
                                        ask_volume = float(ticker_data['a'][1])
                                        
                                        self.quotes.append({
                                            'timestamp': timestamp,
                                            'bid_price': bid_price,
                                            'bid_volume': bid_volume,
                                            'ask_price': ask_price,
                                            'ask_volume': ask_volume
                                        })
                                        
                                        if message_count % 50 == 0:
                                            print(f"QUOTE | Bid: ${bid_price:.2f} @ {bid_volume:.4f} | Ask: ${ask_price:.2f} @ {ask_volume:.4f}")
                                    
                                    elif isinstance(ticker_data, list):
                                        # Trade format (array of trades)
                                        for trade in ticker_data:
                                            try:
                                                price = float(trade[0])
                                                qty = float(trade[1])
                                                time = float(trade[2])
                                                side = trade[3]
                                                
                                                self.trades.append({
                                                    'timestamp': timestamp,
                                                    'price': price,
                                                    'quantity': qty,
                                                    'side': side
                                                })
                                                
                                                print(f"TRADE | {side.upper():4s} | ${price:.2f} @ {qty:.4f}")
                                            except (IndexError, ValueError):
                                                pass
                                
                            except (KeyError, ValueError, IndexError) as e:
                                pass
                            
                            if message_count % 500 == 0:
                                print(f"\n--- Progress: {message_count} messages, {len(self.trades)} trades, {len(self.quotes)} quotes ---\n")
                        
                        # Break out of retry loop if successful
                        break
                        
                except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
                    print(f"Connection failed (attempt {attempt + 1}/3): {e}")
                    if attempt < 2:
                        print("Retrying in 5 seconds...")
                        await asyncio.sleep(5)
                    else:
                        raise
        
        except asyncio.CancelledError:
            print("Data collection cancelled.")
        except Exception as e:
            print(f"Error during data collection: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.save_data()
    
    def save_data(self):
        """Save collected data to CSV files."""
        if len(self.trades) == 0 and len(self.quotes) == 0:
            print("No data collected to save.")
            return
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if len(self.trades) > 0:
            trades_df = pd.DataFrame(self.trades)
            trades_path = os.path.join(self.output_dir, f'trades_{timestamp_str}.csv')
            trades_df.to_csv(trades_path, index=False)
            print(f"\n✓ Saved {len(trades_df)} trades to: {trades_path}")
        
        if len(self.quotes) > 0:
            quotes_df = pd.DataFrame(self.quotes)
            quotes_path = os.path.join(self.output_dir, f'quotes_{timestamp_str}.csv')
            quotes_df.to_csv(quotes_path, index=False)
            print(f"✓ Saved {len(quotes_df)} quotes to: {quotes_path}")
        
        print("\nData collection complete!")


async def main():
    """Main function to run the data collector."""
    print("=" * 60)
    print("Kraken Live Data Collector")
    print("=" * 60)
    
    collector = KrakenDataCollector(output_dir='data/live', symbol='BTC/USD')
    
    # Collect for 60 minutes (adjust as needed)
    await collector.collect_data(duration_minutes=60)
    
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCollection interrupted by user.")