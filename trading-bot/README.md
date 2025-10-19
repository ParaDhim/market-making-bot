# Low-Latency Market Making Trading Bot

A high-performance algorithmic trading system combining C++ for low-latency execution and Python for machine learning. This project demonstrates a complete quantitative trading workflow suitable for HFT/prop trading firm portfolios.

## ˙Project Overview

This trading bot implements a market-making strategy enhanced with ML predictions:
- **C++ Core Engine**: Low-latency order execution and market data processing
- **Python ML Brain**: LightGBM model for price direction prediction
- **Backtesting Suite**: Comprehensive performance analysis and visualization

## Project Structure

```
trading-bot/
├── setup.sh                      # One-command setup script
├── run_backtest.sh              # Automated backtest runner
├── data/
│   ├── collect_data.py          # Kraken WebSocket data collector
│   ├── raw/                     # Raw market data (trades & quotes)
│   └── processed/               # Processed features
├── cpp/                         # C++ trading engine
│   ├── include/                 # Header files
│   ├── src/                     # Implementation
│   └── CMakeLists.txt          # Build configuration
├── python/
│   ├── feature_engineering.py   # Feature creation pipeline
│   ├── train_model.py          # ML model training
│   ├── signal_generator.py     # Real-time signal generation
│   └── backtest_analysis.py    # Performance analysis
└── results/                     # Backtest outputs and models
```

## Quick Start

### Prerequisites
- macOS with M1/M2 chip (or Linux with modifications)
- Python 3.8+
- 5GB free disk space

### One-Command Setup

```bash
chmod +x setup.sh
./setup.sh
```

This will:
1. Install all dependencies (Homebrew, CMake, Boost, Python packages)
2. Collect 60 minutes of live BTC/USD data from Kraken
3. Engineer features and train the ML model
4. Build the C++ trading engine

**Note**: Data collection takes 60 minutes. For testing, edit `collect_data.py` and change `duration_minutes=60` to `duration_minutes=5`.

### Running the Backtest

After setup completes:

```bash
chmod +x run_backtest.sh
./run_backtest.sh
```

Or manually:

```bash
# Terminal 1: Generate ML signals
source venv/bin/activate
python python/signal_generator.py

# Terminal 2: Run trading engine
./cpp/build/trading_engine

# Terminal 3: Analyze results
python python/backtest_analysis.py
```

## System Components

### 1. Data Collection
- Connects to Kraken's WebSocket API
- Collects real-time trades and quotes (order book updates)
- Saves to timestamped CSV files

### 2. Feature Engineering
Creates 15 features including:
- Order book imbalance (OBI)
- Spread metrics
- Price momentum (5, 10, 20, 50 ticks)
- Volatility measures
- Bid-Ask pressure ratios
- Price velocity and acceleration

### 3. ML Model Training
- **Model**: LightGBM Classifier
- **Task**: Predict price direction (up/down/neutral)
- **Features**: 15 engineered features
- **Validation**: Time-series split (80/20)
- **Output**: Trained model saved to `results/trained_model.joblib`

### 4. C++ Trading Engine

**Key Components**:
- `MarketDataParser`: Reads historical tick data with minimal latency
- `OrderBook`: Efficient bid/ask state management
- `Strategy`: Market-making logic with ML signal integration
- `SimulatedExchange`: Realistic order matching and fill simulation
- `SignalReader`: Consumes ML predictions in real-time

**Performance Optimizations**:
- Modern C++17 features
- Zero-copy data parsing where possible
- Efficient STL containers (std::map for sorted order book)
- Minimal heap allocations in hot path
- Compiled with `-O3 -march=native`

### 5. Strategy Logic

**Base Strategy**: Symmetric market making
- Places bid/ask quotes around mid-price
- Default spread: 2 basis points (0.02%)
- Position size: 0.01 BTC per order

**ML Enhancement**:
- **Signal +1 (Price Up)**: Aggressive bid, wider ask
- **Signal -1 (Price Down)**: Wider bid, aggressive ask
- **Signal 0 (Neutral)**: Symmetric quotes

**Risk Management**:
- Max position: ±0.1 BTC
- Automatic position flattening when limit breached

## Performance Metrics

The analysis suite calculates:
- **Returns**: Final PnL, Max PnL, Max Drawdown
- **Risk-Adjusted**: Sharpe Ratio, Sortino Ratio
- **Trade Stats**: Win rate, Profit Factor, Avg Win/Loss
- **Visualizations**: Equity curve, drawdown, inventory, returns distribution

## 🎓 Training Recommendations

### M2 MacBook Air vs Cloud

**Train Locally (M2)** Recommended:
- Faster for this project size (< 1M samples)
- No upload/download overhead
- Better debugging experience
- Real-time monitoring

**Use Kaggle/Colab** when:
- Dataset > 10M samples
- Training > 30 minutes locally
- Need GPU for deep learning (not required here)

The M2 chip will train LightGBM in 1-3 minutes for typical 60-min data collection.

## 🔧 Configuration

### Collect More/Less Data

Edit `data/collect_data.py`:
```python
collector = KrakenDataCollector(duration_minutes=60)  # Change this
```

### Adjust Strategy Parameters

Edit `cpp/src/main.cpp`:
```cpp
Strategy strategy(
    0.0002,  // spread_factor (0.02%)
    0.01     // order_size (0.01 BTC)
);
```

### Change ML Model

Edit `python/train_model.py` to use different models:
```python
from sklearn.ensemble import RandomForestClassifier
# or
import tensorflow as tf
# etc.
```

## Dependencies

### C++
- CMake 3.15+
- Boost (system, filesystem)
- spdlog (logging)
- C++17 compiler (GCC/Clang)

### Python
- pandas, numpy
- scikit-learn
- lightgbm
- matplotlib, seaborn
- websockets

All installed automatically by `setup.sh`.

## Troubleshooting

### "Cannot find Boost"
```bash
brew install boost
export BOOST_ROOT=/opt/homebrew/opt/boost  # M1/M2 Mac
```

### "No quotes files found"
Run data collection first:
```bash
python data/collect_data.py
```

### "Trading engine crashes"
Check that signal file exists:
```bash
python python/signal_generator.py
```

### Build errors
Clean and rebuild:
```bash
cd cpp/build
rm -rf *
cmake ..
make -j8
```

## Learning Resources

This project demonstrates:
- Low-latency C++ programming
- Market microstructure (order books, market making)
- Feature engineering for financial ML
- Backtesting methodology
- Risk management
- Inter-process communication (C++ ↔ Python)

## Next Steps

To enhance this project:
1. **Add more features**: VWAP, trade flow toxicity, order flow imbalance
2. **Better models**: LSTM for sequence prediction, ensemble methods
3. **Risk controls**: Dynamic position limits, stop-loss
4. **Multi-asset**: Trade multiple pairs simultaneously
5. **Live trading**: Connect to exchange APIs (paper trading first!)
6. **Performance**: Profile with `perf`, optimize hot paths
7. **Testing**: Add unit tests, integration tests

## Disclaimer

This is an educational project. Do not use for live trading without:
- Extensive additional testing
- Proper risk management
- Understanding of exchange rules and fees
- Paper trading validation
- Professional review

Trading involves significant risk of loss.
