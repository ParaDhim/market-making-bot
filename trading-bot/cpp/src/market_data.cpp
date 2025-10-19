#include "market_data.hpp"
#include <iostream>
#include <iomanip>
#include <sstream>

MarketDataParser::MarketDataParser(const std::string& quotes_file, 
                                   const std::string& trades_file)
    : has_next_quote_(false), has_next_trade_(false) {
    
    quotes_stream_.open(quotes_file);
    trades_stream_.open(trades_file);
    
    if (!quotes_stream_.is_open()) {
        throw std::runtime_error("Cannot open quotes file: " + quotes_file);
    }
    
    if (!trades_stream_.is_open()) {
        throw std::runtime_error("Cannot open trades file: " + trades_file);
    }
    
    // Skip headers
    std::string header;
    std::getline(quotes_stream_, header);
    std::getline(trades_stream_, header);
    
    // Pre-read first entries
    has_next_quote_ = read_next_quote();
    has_next_trade_ = read_next_trade();
}

MarketDataParser::~MarketDataParser() {
    if (quotes_stream_.is_open()) quotes_stream_.close();
    if (trades_stream_.is_open()) trades_stream_.close();
}

bool MarketDataParser::has_more_data() const {
    return has_next_quote_ || has_next_trade_;
}

bool MarketDataParser::peek_next_is_quote() const {
    if (!has_next_quote_) return false;
    if (!has_next_trade_) return true;
    return next_quote_.timestamp <= next_trade_.timestamp;
}

Quote MarketDataParser::get_next_quote() {
    Quote result = next_quote_;
    has_next_quote_ = read_next_quote();
    return result;
}

Trade MarketDataParser::get_next_trade() {
    Trade result = next_trade_;
    has_next_trade_ = read_next_trade();
    return result;
}

bool MarketDataParser::read_next_quote() {
    std::string line;
    if (!std::getline(quotes_stream_, line)) {
        return false;
    }
    
    std::stringstream ss(line);
    std::string timestamp_str, symbol, bid_str, ask_str, bid_vol_str, ask_vol_str;
    
    // Parse CSV: timestamp,symbol,best_bid,best_ask,bid_volume,ask_volume
    std::getline(ss, timestamp_str, ',');
    std::getline(ss, symbol, ',');
    std::getline(ss, bid_str, ',');
    std::getline(ss, ask_str, ',');
    std::getline(ss, bid_vol_str, ',');
    std::getline(ss, ask_vol_str, ',');
    
    next_quote_.timestamp = parse_timestamp(timestamp_str);
    next_quote_.best_bid = std::stod(bid_str);
    next_quote_.best_ask = std::stod(ask_str);
    next_quote_.bid_volume = std::stod(bid_vol_str);
    next_quote_.ask_volume = std::stod(ask_vol_str);
    
    return true;
}

bool MarketDataParser::read_next_trade() {
    std::string line;
    if (!std::getline(trades_stream_, line)) {
        return false;
    }
    
    std::stringstream ss(line);
    std::string timestamp_str, symbol, price_str, qty_str, side;
    
    // Parse CSV: timestamp,symbol,price,quantity,side
    std::getline(ss, timestamp_str, ',');
    std::getline(ss, symbol, ',');
    std::getline(ss, price_str, ',');
    std::getline(ss, qty_str, ',');
    std::getline(ss, side, ',');
    
    next_trade_.timestamp = parse_timestamp(timestamp_str);
    next_trade_.price = std::stod(price_str);
    next_trade_.quantity = std::stod(qty_str);
    next_trade_.side = side;
    
    return true;
}

std::chrono::system_clock::time_point MarketDataParser::parse_timestamp(const std::string& ts) {
    // Simple timestamp parsing - assumes ISO format
    std::tm tm = {};
    std::stringstream ss(ts);
    ss >> std::get_time(&tm, "%Y-%m-%d %H:%M:%S");
    return std::chrono::system_clock::from_time_t(std::mktime(&tm));
}