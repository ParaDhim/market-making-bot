#pragma once

#include <string>
#include <fstream>
#include <sstream>
#include <vector>
#include <chrono>

struct Quote {
    std::chrono::system_clock::time_point timestamp;
    double best_bid;
    double best_ask;
    double bid_volume;
    double ask_volume;
    
    double mid_price() const {
        return (best_bid + best_ask) / 2.0;
    }
    
    double spread() const {
        return best_ask - best_bid;
    }
};

struct Trade {
    std::chrono::system_clock::time_point timestamp;
    double price;
    double quantity;
    std::string side;  // "buy" or "sell"
};

class MarketDataParser {
public:
    MarketDataParser(const std::string& quotes_file, const std::string& trades_file);
    ~MarketDataParser();
    
    bool has_more_data() const;
    Quote get_next_quote();
    Trade get_next_trade();
    bool peek_next_is_quote() const;
    
private:
    std::ifstream quotes_stream_;
    std::ifstream trades_stream_;
    
    Quote next_quote_;
    Trade next_trade_;
    bool has_next_quote_;
    bool has_next_trade_;
    
    bool read_next_quote();
    bool read_next_trade();
    
    std::chrono::system_clock::time_point parse_timestamp(const std::string& ts);
};