#pragma once

#include <map>
#include <utility>

class OrderBook {
public:
    OrderBook() = default;
    
    void update(double bid_price, double bid_volume, double ask_price, double ask_volume);
    
    std::pair<double, double> get_best_bid() const;  // price, volume
    std::pair<double, double> get_best_ask() const;  // price, volume
    
    double get_mid_price() const;
    double get_spread() const;
    double get_imbalance() const;  // Order book imbalance
    
    bool is_valid() const { return !bids_.empty() && !asks_.empty(); }
    
private:
    std::map<double, double, std::greater<double>> bids_;  // descending order
    std::map<double, double> asks_;  // ascending order
};