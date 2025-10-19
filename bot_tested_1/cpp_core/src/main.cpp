// cpp_core/src/main.cpp
#include "Strategy.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <boost/tokenizer.hpp>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <iomanip> // For std::fixed and std::setprecision

// --- Implementation of Class Methods ---

// OrderBook
void OrderBook::update_quote(const Quote& quote) {
    // For simplicity, we just set the new best bid/ask
    // A real order book would manage multiple price levels.
    bids_.clear();
    asks_.clear();
    if (quote.bid_qty > 0) {
        bids_[quote.bid_price] = quote.bid_qty;
    }
    if (quote.ask_qty > 0) {
        asks_[quote.ask_price] = quote.ask_qty;
    }
}

double OrderBook::get_best_bid() const {
    if (bids_.empty()) return 0.0;
    return bids_.begin()->first;
}

double OrderBook::get_best_ask() const {
    if (asks_.empty()) return std::numeric_limits<double>::max();
    return asks_.begin()->first;
}

double OrderBook::get_mid_price() const {
    if (bids_.empty() || asks_.empty()) return 0.0;
    return (get_best_bid() + get_best_ask()) / 2.0;
}

// ExecutionHandler
void ExecutionHandler::check_fills(const Trade& market_trade, double our_bid, double our_ask) {
    // If market sells into our bid
    if (market_trade.side == "sell" && market_trade.price <= our_bid) {
        pnl_ -= market_trade.qty * our_bid;
        position_ += market_trade.qty;
        std::cout << "FILLED BUY @ " << our_bid << std::endl;
    }
    // If market buys into our ask
    if (market_trade.side == "buy" && market_trade.price >= our_ask) {
        pnl_ += market_trade.qty * our_ask;
        position_ -= market_trade.qty;
        std::cout << "FILLED SELL @ " << our_ask << std::endl;
    }
}

// Strategy
void Strategy::on_quote(const Quote& quote) {
    order_book_.update_quote(quote);
    double mid_price = order_book_.get_mid_price();
    if (mid_price == 0.0) return;

    // Skew quotes based on ML signal
    double bid_skew = (current_signal_ == 1) ? 0.005 : 0; // If signal is UP, bid more aggressively
    double ask_skew = (current_signal_ == -1) ? 0.005 : 0; // If signal is DOWN, ask more aggressively

    our_bid_price_ = mid_price - (spread_ / 2.0) + bid_skew;
    our_ask_price_ = mid_price + (spread_ / 2.0) - ask_skew;
}

void Strategy::on_trade(const Trade& trade) {
    execution_handler_.check_fills(trade, our_bid_price_, our_ask_price_);
}

void Strategy::on_signal(int signal) {
    current_signal_ = signal;
    // std::cout << "Received signal: " << signal << std::endl;
}


// --- Main Application Logic ---

const char* IPC_PIPE_PATH = "ipc/signal_pipe";

int main() {
    // 1. Setup IPC named pipe
    mkfifo(IPC_PIPE_PATH, 0666);
    std::cout << "C++: Waiting for Python to connect to pipe..." << std::endl;
    int pipe_fd = open(IPC_PIPE_PATH, O_RDONLY | O_NONBLOCK);
    if (pipe_fd == -1) {
        std::cerr << "Error opening pipe" << std::endl;
        return 1;
    }
    std::cout << "C++: Pipe opened." << std::endl;

    // 2. Load Data
    std::ifstream quotes_file("/Users/parasdhiman/Desktop/market-making-bot/bot/python_ml/data/raw_quotes.csv");
    std::ifstream trades_file("/Users/parasdhiman/Desktop/market-making-bot/bot/python_ml/data/raw_trades.csv");
    std::ofstream results_file("/Users/parasdhiman/Desktop/market-making-bot/bot/backtest_results.csv");

    if (!quotes_file.is_open() || !trades_file.is_open()) {
        std::cerr << "Error: Could not open data files. Did you run the python data generator?" << std::endl;
        return 1;
    }

    results_file << "timestamp,pnl,position\n";
    
    std::string quote_line, trade_line, header;
    // Skip headers
    std::getline(quotes_file, header);
    std::getline(trades_file, header);

    Strategy strategy;
    long long current_timestamp = 0;

    // 3. Main Event Loopc  
    while (std::getline(quotes_file, quote_line) && std::getline(trades_file, trade_line)) {
        // Read and parse signal
        char buf[10];
        ssize_t num_read = read(pipe_fd, buf, sizeof(buf) - 1);
        if (num_read > 0) {
            buf[num_read] = '\0';
            try {
                strategy.on_signal(std::stoi(buf));
            } catch (const std::exception& e) {
                // Ignore conversion errors
            }
        }

        // Parse Quote Data
        boost::tokenizer<boost::escaped_list_separator<char>> quote_tok(quote_line);
        std::vector<std::string> quote_vals;
        for (const auto& t : quote_tok) quote_vals.push_back(t);

        Quote q;
        q.timestamp = current_timestamp; // Simple timestamp
        q.bid_price = std::stod(quote_vals[2]);
        q.bid_qty = std::stoi(quote_vals[3]);
        q.ask_price = std::stod(quote_vals[4]);
        q.ask_qty = std::stoi(quote_vals[5]);

        // Parse Trade Data
        boost::tokenizer<boost::escaped_list_separator<char>> trade_tok(trade_line);
        std::vector<std::string> trade_vals;
        for (const auto& t : trade_tok) trade_vals.push_back(t);
        
        Trade t;
        t.timestamp = current_timestamp;
        t.price = std::stod(trade_vals[2]);
        t.qty = std::stoi(trade_vals[3]);
        t.side = trade_vals[4];
        
        // Update strategy
        strategy.on_quote(q);
        strategy.on_trade(t);
        
        // Log results
        if (current_timestamp % 100 == 0) { // Log every 100 ticks
            double pnl = strategy.get_pnl();
            results_file << current_timestamp << "," << pnl << "," << 0 << "\n"; // Position not fully tracked for this simple log
            std::cout << "Timestamp: " << current_timestamp 
                      << " | PnL: " << std::fixed << std::setprecision(2) << pnl << "\r" << std::flush;
        }

        current_timestamp++;
    }

    std::cout << "\nBacktest finished." << std::endl;
    std::cout << "Final PnL: " << std::fixed << std::setprecision(2) << strategy.get_pnl() << std::endl;

    // 4. Cleanup
    close(pipe_fd);
    unlink(IPC_PIPE_PATH);
    quotes_file.close();
    trades_file.close();
    results_file.close();

    return 0;
}