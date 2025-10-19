import asyncio
import json
import websockets
import pandas as pd
from datetime import datetime
import signal
import sys
from pathlib import Path

class KrakenDataCollector:
    def __init__(self, symbol="BTC/USD", duration_minutes=60):
        self.symbol = symbol
        self.duration_minutes = duration_minutes
        self.trades = []
        self.quotes = []
        self.running = True
        self.start_time = None
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        print('\nShutting down gracefully...')
        self.running = False
    
    async def collect_data(self):
        kraken_ws_url = "wss://ws.kraken.com/v2"
        
        subscribe_ticker = {
            "method": "subscribe",
            "params": {
                "channel": "ticker",
                "symbol": [self.symbol]
            }
        }
        
        subscribe_trade = {
            "method": "subscribe",
            "params": {
                "channel": "trade",
                "symbol": [self.symbol]
            }
        }
        
        try:
            async with websockets.connect(kraken_ws_url) as ws:
                await ws.send(json.dumps(subscribe_ticker))
                await ws.send(json.dumps(subscribe_trade))
                
                print(f"Collecting data for {self.duration_minutes} minutes...")
                print("Press Ctrl+C to stop early\n")
                
                self.start_time = datetime.now()
                
                async for message in ws:
                    if not self.running:
                        break
                    
                    # Check if duration exceeded
                    elapsed = (datetime.now() - self.start_time).total_seconds() / 60
                    if elapsed >= self.duration_minutes:
                        print(f"\n{self.duration_minutes} minutes elapsed. Stopping collection...")
                        break
                    
                    data = json.loads(message)
                    
                    if 'channel' not in data:
                        continue
                    
                    timestamp = datetime.now()
                    
                    # Process ticker (quote) data
                    if data.get('channel') == 'ticker':
                        ticker_data = data['data'][0]
                        quote = {
                            'timestamp': timestamp,
                            'symbol': ticker_data.get('symbol', self.symbol),
                            'best_bid': float(ticker_data['bid']),
                            'best_ask': float(ticker_data['ask']),
                            'bid_volume': float(ticker_data.get('bid_qty', 0)),
                            'ask_volume': float(ticker_data.get('ask_qty', 0))
                        }
                        self.quotes.append(quote)
                        
                        if len(self.quotes) % 100 == 0:
                            print(f"Collected: {len(self.quotes)} quotes, {len(self.trades)} trades | "
                                  f"Time: {elapsed:.1f}/{self.duration_minutes} min")
                    
                    # Process trade data
                    elif data.get('channel') == 'trade':
                        for trade_data in data['data']:
                            trade = {
                                'timestamp': timestamp,
                                'symbol': trade_data.get('symbol', self.symbol),
                                'price': float(trade_data['price']),
                                'quantity': float(trade_data['qty']),
                                'side': trade_data['side']
                            }
                            self.trades.append(trade)
        
        except Exception as e:
            print(f"Error during data collection: {e}")
        
        finally:
            self.save_data()
    
    def save_data(self):
        # Create data directories
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_file = f"data/raw/trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            trades_df.to_csv(trades_file, index=False)
            print(f"\nSaved {len(self.trades)} trades to {trades_file}")
        
        if self.quotes:
            quotes_df = pd.DataFrame(self.quotes)
            quotes_file = f"data/raw/quotes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            quotes_df.to_csv(quotes_file, index=False)
            print(f"Saved {len(self.quotes)} quotes to {quotes_file}")
        
        print(f"\nData collection complete!")
        print(f"Total duration: {(datetime.now() - self.start_time).total_seconds()/60:.2f} minutes")

async def main():
    # Collect 60 minutes of data by default
    # For testing, use 5-10 minutes
    collector = KrakenDataCollector(symbol="BTC/USD", duration_minutes=60)
    await collector.collect_data()

if __name__ == "__main__":
    asyncio.run(main())