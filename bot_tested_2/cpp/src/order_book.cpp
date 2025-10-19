// FILE 2: cpp/src/order_book.cpp
// ============================================================================
#include "order_book.hpp"
#include <algorithm>

namespace trading {

OrderBook::OrderBook() : cache_valid_(false) {}

void OrderBook::update(const Quote& quote) {
    if (quote.bid_volume > 0) {
        bids_[quote.bid_price] = quote.bid_volume;
    }
    
    if (quote.ask_volume > 0) {
        asks_[quote.ask_price] = quote.ask_volume;
    }
    
    invalidate_cache();
}

std::optional<Price> OrderBook::best_bid() const {
    if (!cache_valid_) {
        if (!bids_.empty()) {
            cached_best_bid_ = bids_.begin()->first;
        } else {
            cached_best_bid_ = std::nullopt;
        }
    }
    return cached_best_bid_;
}

std::optional<Price> OrderBook::best_ask() const {
    if (!cache_valid_) {
        if (!asks_.empty()) {
            cached_best_ask_ = asks_.begin()->first;
        } else {
            cached_best_ask_ = std::nullopt;
        }
        cache_valid_ = true;
    }
    return cached_best_ask_;
}

std::optional<Price> OrderBook::mid_price() const {
    auto bid = best_bid();
    auto ask = best_ask();
    
    if (bid && ask) {
        return (*bid + *ask) / 2;
    }
    return std::nullopt;
}

Quantity OrderBook::bid_volume_at(Price price) const {
    auto it = bids_.find(price);
    if (it != bids_.end()) return it->second;
    return 0.0;
}

Quantity OrderBook::ask_volume_at(Price price) const {
    auto it = asks_.find(price);
    if (it != asks_.end()) return it->second;
    return 0.0;
}

Quantity OrderBook::total_bid_volume(size_t levels) const {
    Quantity total = 0.0;
    size_t count = 0;
    
    for (const auto& [price, volume] : bids_) {
        if (count >= levels) break;
        total += volume;
        count++;
    }
    
    return total;
}

Quantity OrderBook::total_ask_volume(size_t levels) const {
    Quantity total = 0.0;
    size_t count = 0;
    
    for (const auto& [price, volume] : asks_) {
        if (count >= levels) break;
        total += volume;
        count++;
    }
    
    return total;
}

double OrderBook::imbalance() const {
    auto bid_vol = total_bid_volume(1);
    auto ask_vol = total_ask_volume(1);
    
    double total = bid_vol + ask_vol;
    if (total > 0) {
        return (bid_vol - ask_vol) / total;
    }
    return 0.0;
}

void OrderBook::clear() {
    bids_.clear();
    asks_.clear();
    invalidate_cache();
}

void OrderBook::invalidate_cache() {
    cache_valid_ = false;
}

} // namespace trading

