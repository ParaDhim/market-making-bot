// FILE 4: cpp/src/simulated_exchange.cpp
// ============================================================================
#include "simulated_exchange.hpp"
#include <iostream>

namespace trading {

SimulatedExchange::SimulatedExchange()
    : total_fills_(0), total_volume_(0.0) {}

void SimulatedExchange::on_trade(const Trade& trade) {
    check_fills_against_trade(trade);
}

void SimulatedExchange::on_quote(const Quote& quote) {
    last_quote_ = quote;
    check_fills_against_quote(quote);
}

void SimulatedExchange::submit_order(const Order& order) {
    pending_orders_[order.id] = order;
    
    if (last_quote_.timestamp > 0) {
        check_fills_against_quote(last_quote_);
    }
}

void SimulatedExchange::cancel_order(OrderId order_id) {
    pending_orders_.erase(order_id);
}

void SimulatedExchange::on_fill(FillCallback callback) {
    fill_callback_ = callback;
}

void SimulatedExchange::check_fills_against_trade(const Trade& trade) {
    std::vector<OrderId> to_remove;
    
    for (auto& [order_id, order] : pending_orders_) {
        bool filled = false;
        
        if (order.side == Side::BUY) {
            if (trade.price <= order.price) {
                generate_fill(order, trade.price, order.quantity);
                filled = true;
            }
        } else {
            if (trade.price >= order.price) {
                generate_fill(order, trade.price, order.quantity);
                filled = true;
            }
        }
        
        if (filled) {
            to_remove.push_back(order_id);
        }
    }
    
    for (auto order_id : to_remove) {
        pending_orders_.erase(order_id);
    }
}

void SimulatedExchange::check_fills_against_quote(const Quote& quote) {
    std::vector<OrderId> to_remove;
    
    for (auto& [order_id, order] : pending_orders_) {
        bool filled = false;
        Price fill_price = order.price;
        
        if (order.side == Side::BUY) {
            if (order.price >= quote.ask_price) {
                fill_price = quote.ask_price;
                generate_fill(order, fill_price, 
                            std::min(order.quantity, quote.ask_volume));
                filled = true;
            }
        } else {
            if (order.price <= quote.bid_price) {
                fill_price = quote.bid_price;
                generate_fill(order, fill_price, 
                            std::min(order.quantity, quote.bid_volume));
                filled = true;
            }
        }
        
        if (filled) {
            to_remove.push_back(order_id);
        }
    }
    
    for (auto order_id : to_remove) {
        pending_orders_.erase(order_id);
    }
}

void SimulatedExchange::generate_fill(const Order& order, Price fill_price, 
                                     Quantity fill_quantity) {
    Fill fill(order.id, order.timestamp, fill_price, fill_quantity, order.side);
    
    total_fills_++;
    total_volume_ += fill_quantity;
    
    if (fill_callback_) {
        fill_callback_(fill);
    }
}

} // namespace trading
