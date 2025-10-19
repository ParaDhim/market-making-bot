#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Trading Bot Setup Script ===${NC}\n"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Warning: This script is optimized for macOS. Some steps may need modification.${NC}"
fi

# Step 1: Install Homebrew if not present (macOS)
if ! command -v brew &> /dev/null; then
    echo -e "${BLUE}Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Step 2: Install C++ dependencies
echo -e "${BLUE}Installing C++ dependencies...${NC}"
brew install cmake boost spdlog

# Step 3: Setup Python virtual environment
echo -e "${BLUE}Setting up Python environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Step 4: Install Python dependencies
echo -e "${BLUE}Installing Python packages...${NC}"
pip install --upgrade pip
pip install -r python/requirements.txt

# Step 5: Create necessary directories
echo -e "${BLUE}Creating directory structure...${NC}"
mkdir -p data/raw data/processed results cpp/build

# Step 6: Collect market data
echo -e "${BLUE}Collecting market data (this will take 5-10 minutes)...${NC}"
python python/data/collect_data.py

# Step 7: Process and engineer features
echo -e "${BLUE}Engineering features...${NC}"
python python/feature_engineering.py

# Step 8: Train ML model
echo -e "${BLUE}Training ML model...${NC}"
python python/train_model.py

# Step 9: Build C++ components
echo -e "${BLUE}Building C++ engine...${NC}"
cd cpp/build
cmake ..
make -j$(sysctl -n hw.ncpu)
cd ../..

# Step 10: Run the system
echo -e "\n${GREEN}=== Setup Complete! ===${NC}\n"
echo -e "To run the trading bot:"
echo -e "  1. Terminal 1: ${GREEN}python python/signal_generator.py${NC}"
echo -e "  2. Terminal 2: ${GREEN}./cpp/build/trading_engine${NC}"
echo -e "  3. After completion: ${GREEN}python python/backtest_analysis.py${NC}"
echo -e "\nOr run the automated test:"
echo -e "  ${GREEN}./run_backtest.sh${NC}\n"