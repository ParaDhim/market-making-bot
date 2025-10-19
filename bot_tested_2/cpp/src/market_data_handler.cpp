// FILE 1: cpp/src/market_data_handler.cpp
// ============================================================================
#include "market_data_handler.hpp"
#include <sstream>
#include <iostream>
#include <algorithm>

namespace trading {

MarketDataHandler::MarketDataHandler(const std::string& trades_file, 
                                    const std::string& quotes_file)
    : trades_file_(trades_file), quotes_file_(quotes_file),
      trades_count_(0), quotes_count_(0),
      has_next_trade_(false), has_next_quote_(false) {
    
    trades_stream_.open(trades_file_);
    quotes_stream_.open(quotes_file_);
    
    if (!trades_stream_.is_open()) {
        throw std::runtime_error("Failed to open trades file: " + trades_file_);
    }
    if (!quotes_stream_.is_open()) {
        throw std::runtime_error("Failed to open quotes file: " + quotes_file_);
    }
    
    std::string header;
    std::getline(trades_stream_, header);
    std::getline(quotes_stream_, header);
    
    has_next_trade_ = read_next_trade();
    has_next_quote_ = read_next_quote();
}

MarketDataHandler::~MarketDataHandler() {
    if (trades_stream_.is_open()) trades_stream_.close();
    if (quotes_stream_.is_open()) quotes_stream_.close();
}

void MarketDataHandler::on_trade(TradeCallback callback) {
    trade_callback_ = callback;
}

void MarketDataHandler::on_quote(QuoteCallback callback) {
    quote_callback_ = callback;
}

void MarketDataHandler::start() {
    while (process_next()) {}
}

bool MarketDataHandler::process_next() {
    if (!has_next_trade_ && !has_next_quote_) return false;
    
    if (has_next_trade_ && !has_next_quote_) {
        if (trade_callback_) trade_callback_(next_trade_);
        has_next_trade_ = read_next_trade();
        return true;
    }
    
    if (has_next_quote_ && !has_next_trade_) {
        if (quote_callback_) quote_callback_(next_quote_);
        has_next_quote_ = read_next_quote();
        return true;
    }
    
    if (next_trade_.timestamp <= next_quote_.timestamp) {
        if (trade_callback_) trade_callback_(next_trade_);
        has_next_trade_ = read_next_trade();
    } else {
        if (quote_callback_) quote_callback_(next_quote_);
        has_next_quote_ = read_next_quote();
    }
    
    return true;
}

bool MarketDataHandler::read_next_trade() {
    std::string line;
    if (std::getline(trades_stream_, line)) {
        next_trade_ = parse_trade_line(line);
        trades_count_++;
        return true;
    }
    return false;
}

bool MarketDataHandler::read_next_quote() {
    std::string line;
    if (std::getline(quotes_stream_, line)) {
        next_quote_ = parse_quote_line(line);
        quotes_count_++;
        return true;
    }
    return false;
}

Trade MarketDataHandler::parse_trade_line(const std::string& line) {
    auto fields = split_csv(line);
    if (fields.size() < 4) throw std::runtime_error("Invalid trade line: " + line);
    
    Trade trade;
    trade.timestamp = std::stoull(fields[0]);
    trade.price = double_to_price(std::stod(fields[1]));
    trade.quantity = std::stod(fields[2]);
    trade.side = string_to_side(fields[3]);
    
    return trade;
}

Quote MarketDataHandler::parse_quote_line(const std::string& line) {
    auto fields = split_csv(line);
    if (fields.size() < 5) throw std::runtime_error("Invalid quote line: " + line);
    
    Quote quote;
    quote.timestamp = std::stoull(fields[0]);
    quote.bid_price = double_to_price(std::stod(fields[1]));
    quote.bid_volume = std::stod(fields[2]);
    quote.ask_price = double_to_price(std::stod(fields[3]));
    quote.ask_volume = std::stod(fields[4]);
    
    return quote;
}

std::vector<std::string> MarketDataHandler::split_csv(const std::string& line) {
    std::vector<std::string> result;
    std::stringstream ss(line);
    std::string field;
    
    while (std::getline(ss, field, ',')) {
        field.erase(0, field.find_first_not_of(" \t\r\n"));
        field.erase(field.find_last_not_of(" \t\r\n") + 1);
        result.push_back(field);
    }
    
    return result;
}

} // namespace trading
