#!/bin/bash

# Root directory
mkdir -p trading-bot
cd trading-bot || exit

# Root files
touch CMakeLists.txt README.md setup.sh

# Data directory
mkdir -p data/raw data/processed
touch data/collect_data.py

# C++ directory
mkdir -p cpp/include cpp/src cpp/build
touch cpp/CMakeLists.txt
touch cpp/include/{market_data.hpp,order_book.hpp,strategy.hpp,simulated_exchange.hpp,signal_reader.hpp}
touch cpp/src/{market_data.cpp,order_book.cpp,strategy.cpp,simulated_exchange.cpp,signal_reader.cpp,main.cpp}

# Python directory
mkdir -p python
touch python/{requirements.txt,feature_engineering.py,train_model.py,signal_generator.py,backtest_analysis.py}

# Results directory
mkdir -p results
touch results/trades.csv

echo "✅ Trading bot project structure created successfully!"

