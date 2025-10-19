#include "strategy.hpp"
#include <cmath>
#include <algorithm>

Strategy::Strategy(double spread_factor, double order_size)
    : spread_factor_(spread_factor)
    , order_size_(order_size)
    , inventory_(0.0)
    , realized_pnl_(0.0)
    , unrealized_pnl_(0.0)
    , avg_entry_price_(0.0)
    , next_order_id_(1) {
}

void Strategy::on_quote(const OrderBook& book, int ml_signal) {
    if (!book.is_valid()) return;
    
    // Cancel existing orders
    cancel_all_orders();
    
    double mid = book.get_mid_price();
    double spread = book.get_spread();
    
    // Calculate our quote prices based on ML signal
    double base_spread = mid * spread_factor_;
    
    double bid_price, ask_price;
    
    if (ml_signal == 1) {
        // Signal says price going up - be more aggressive on buy side
        bid_price = mid - base_spread * 0.5;
        ask_price = mid + base_spread * 1.5;
    } else if (ml_signal == -1) {
        // Signal says price going down - be more aggressive on sell side
        bid_price = mid - base_spread * 1.5;
        ask_price = mid + base_spread * 0.5;
    } else {
        // Neutral - symmetric quotes
        bid_price = mid - base_spread;
        ask_price = mid + base_spread;
    }
    
    // Inventory management: reduce position if too large
    double max_inventory = 0.1;  // Max 0.1 BTC
    if (std::abs(inventory_) > max_inventory) {
        if (inventory_ > 0) {
            // Long position - only place sell orders
            ask_price = mid - base_spread * 0.5;  // Aggressive sell
            place_orders(0, ask_price, ml_signal);
            return;
        } else {
            // Short position - only place buy orders
            bid_price = mid + base_spread * 0.5;  // Aggressive buy
            place_orders(bid_price, 0, ml_signal);
            return;
        }
    }
    
    place_orders(bid_price, ask_price, ml_signal);
}

void Strategy::place_orders(double bid_price, double ask_price, int ml_signal) {
    if (bid_price > 0) {
        auto bid_order = std::make_shared<Order>(
            next_order_id_++, Side::BUY, bid_price, order_size_
        );
        active_orders_.push_back(bid_order);
    }
    
    if (ask_price > 0) {
        auto ask_order = std::make_shared<Order>(
            next_order_id_++, Side::SELL, ask_price, order_size_
        );
        active_orders_.push_back(ask_order);
    }
}

void Strategy::cancel_all_orders() {
    for (auto& order : active_orders_) {
        order->is_active = false;
    }
    active_orders_.clear();
}

std::vector<std::shared_ptr<Order>> Strategy::get_active_orders() const {
    return active_orders_;
}

void Strategy::on_fill(int order_id, double fill_price, double fill_qty) {
    // Find and deactivate the filled order
    auto it = std::find_if(active_orders_.begin(), active_orders_.end(),
        [order_id](const auto& order) { return order->id == order_id; });
    
    if (it == active_orders_.end()) return;
    
    Side side = (*it)->side;
    (*it)->is_active = false;
    
    // Update inventory
    if (side == Side::BUY) {
        double old_inventory = inventory_;
        inventory_ += fill_qty;
        
        // Update average entry price
        if (old_inventory >= 0) {
            avg_entry_price_ = (avg_entry_price_ * old_inventory + fill_price * fill_qty) 
                             / inventory_;
        } else {
            // Closing short position
            realized_pnl_ += (avg_entry_price_ - fill_price) * std::min(fill_qty, std::abs(old_inventory));
            if (inventory_ > 0) {
                avg_entry_price_ = fill_price;
            }
        }
    } else {  // SELL
        double old_inventory = inventory_;
        inventory_ -= fill_qty;
        
        if (old_inventory <= 0) {
            avg_entry_price_ = (avg_entry_price_ * std::abs(old_inventory) + fill_price * fill_qty) 
                             / std::abs(inventory_);
        } else {
            // Closing long position
            realized_pnl_ += (fill_price - avg_entry_price_) * std::min(fill_qty, old_inventory);
            if (inventory_ < 0) {
                avg_entry_price_ = fill_price;
            }
        }
    }
}

// In your src/strategy.cpp file

// Add const back to the definition
double Strategy::get_position_value(double current_price) const {
    // DON'T assign to the member variable.
    // Instead, calculate the value in a local variable and return it.
    double pnl = (current_price - avg_entry_price_) * inventory_;
    return pnl;

    // Or, more concisely:
    // return (current_price - avg_entry_price_) * inventory_;
}