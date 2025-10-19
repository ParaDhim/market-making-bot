#include "order_book.hpp"
#include <algorithm>
#include <cmath>

void OrderBook::update(double bid_price, double bid_volume, 
                       double ask_price, double ask_volume) {
    // Simple update: replace the top of book
    bids_.clear();
    asks_.clear();
    
    if (bid_volume > 0) {
        bids_[bid_price] = bid_volume;
    }
    
    if (ask_volume > 0) {
        asks_[ask_price] = ask_volume;
    }
}

std::pair<double, double> OrderBook::get_best_bid() const {
    if (bids_.empty()) return {0.0, 0.0};
    return *bids_.begin();
}

std::pair<double, double> OrderBook::get_best_ask() const {
    if (asks_.empty()) return {0.0, 0.0};
    return *asks_.begin();
}

double OrderBook::get_mid_price() const {
    if (!is_valid()) return 0.0;
    auto [bid_price, _1] = get_best_bid();
    auto [ask_price, _2] = get_best_ask();
    return (bid_price + ask_price) / 2.0;
}

double OrderBook::get_spread() const {
    if (!is_valid()) return 0.0;
    auto [bid_price, _1] = get_best_bid();
    auto [ask_price, _2] = get_best_ask();
    return ask_price - bid_price;
}

double OrderBook::get_imbalance() const {
    if (!is_valid()) return 0.5;
    auto [_, bid_vol] = get_best_bid();
    auto [__, ask_vol] = get_best_ask();
    return bid_vol / (bid_vol + ask_vol + 1e-10);
}