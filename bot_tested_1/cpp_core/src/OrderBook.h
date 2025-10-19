// cpp_core/src/OrderBook.h
#pragma once
#include "MarketData.h"
#include <map>
#include <limits>

class OrderBook {
public:
    void update_quote(const Quote& quote);
    double get_mid_price() const;
    double get_best_bid() const;
    double get_best_ask() const;

private:
    // Using std::map for sorted keys (prices)
    // For extreme performance, a custom data structure or sorted vector could be used.
    std::map<double, int, std::greater<double>> bids_; // descending order
    std::map<double, int> asks_; // ascending order
};