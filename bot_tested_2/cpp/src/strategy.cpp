// FILE 5: cpp/src/strategy.cpp
// ============================================================================
#include "strategy.hpp"
#include <cmath>
#include <iostream>
#include <algorithm>

namespace trading {

Strategy::Strategy(const StrategyConfig& config)
    : config_(config), position_(0.0), avg_entry_price_(0.0),
      realized_pnl_(0.0), unrealized_pnl_(0.0), next_order_id_(1),
      total_orders_sent_(0), total_fills_(0) {}

void Strategy::on_quote(const Quote& quote) {
    last_quote_ = quote;
    order_book_.update(quote);
    
    auto mid = order_book_.mid_price();
    if (mid) {
        update_pnl(*mid);
    }
    
    update_quotes();
}

void Strategy::on_trade(const Trade& trade) {
    // Trade info can be used for additional signals if needed
}

void Strategy::on_fill(const Fill& fill) {
    total_fills_++;
    
    if (fill.side == Side::BUY) {
        position_ += fill.quantity;
    } else {
        position_ -= fill.quantity;
    }
    
    update_realized_pnl(fill);
    
    std::cout << "FILL: " << side_to_string(fill.side) 
              << " " << fill.quantity << " @ " << price_to_double(fill.price)
              << " | Position: " << position_ 
              << " | PnL: $" << pnl() << std::endl;
}

void Strategy::on_ml_signal(const MLSignal& signal) {
    std::cout << "SIGNAL RECEIVED: " << signal.signal 
              << " confidence=" << signal.confidence << std::endl;
    
    last_signal_ = signal;
    
    auto mid = order_book_.mid_price();
    if (!mid) return;
    
    double mid_double = price_to_double(*mid);
    
    // SELL signal: go short - place order at ask price to guarantee fill
    if (signal.signal < 0 && position_ > -config_.max_position) {
        Price sell_price = double_to_price(mid_double);  // Sell at ask (will be crossed)
        send_order(Side::SELL, sell_price, config_.order_size);
        std::cout << "  -> SELL ORDER PLACED (SHORT) at $" << mid_double << std::endl;
    }
    
    // BUY signal: go long - place order at bid price to guarantee fill
    else if (signal.signal > 0 && position_ < config_.max_position) {
        Price buy_price = double_to_price(mid_double);  // Buy at bid (will be crossed)
        send_order(Side::BUY, buy_price, config_.order_size);
        std::cout << "  -> BUY ORDER PLACED (LONG) at $" << mid_double << std::endl;
    }
    
    // Also update market-making quotes
    update_quotes();
}

void Strategy::set_order_callback(OrderCallback callback) {
    order_callback_ = callback;
}

void Strategy::update_quotes() {
    auto mid = order_book_.mid_price();
    if (!mid) return;
    
    if (std::abs(position_) >= config_.max_position) {
        if (position_ >= config_.max_position) {
            Price ask_price = *mid + double_to_price(config_.base_spread_bps * price_to_double(*mid) / 10000.0);
            send_order(Side::SELL, ask_price, config_.order_size);
        } else {
            Price bid_price = *mid - double_to_price(config_.base_spread_bps * price_to_double(*mid) / 10000.0);
            send_order(Side::BUY, bid_price, config_.order_size);
        }
        return;
    }
    
    Price bid_price, ask_price;
    Quantity bid_qty, ask_qty;
    calculate_target_quotes(bid_price, ask_price, bid_qty, ask_qty);
    
    if (bid_qty > 0) {
        send_order(Side::BUY, bid_price, bid_qty);
    }
    if (ask_qty > 0) {
        send_order(Side::SELL, ask_price, ask_qty);
    }
}

void Strategy::calculate_target_quotes(Price& bid_price, Price& ask_price,
                                       Quantity& bid_qty, Quantity& ask_qty) {
    auto mid = order_book_.mid_price();
    if (!mid) return;
    
    double mid_double = price_to_double(*mid);
    
    double half_spread = config_.base_spread_bps * mid_double / 20000.0;
    
    double skew = 0.0;
    if (last_signal_.signal != 0) {
        skew = last_signal_.signal * config_.skew_factor * half_spread;
    }
    
    double inventory_skew = position_ * config_.inventory_penalty * half_spread;
    
    bid_price = double_to_price(mid_double - half_spread + skew - inventory_skew);
    ask_price = double_to_price(mid_double + half_spread + skew - inventory_skew);
    
    bid_qty = config_.order_size;
    ask_qty = config_.order_size;
    
    if (position_ > 0) {
        bid_qty *= (1.0 - std::abs(position_) / config_.max_position * 0.5);
        ask_qty *= (1.0 + std::abs(position_) / config_.max_position * 0.5);
    } else if (position_ < 0) {
        bid_qty *= (1.0 + std::abs(position_) / config_.max_position * 0.5);
        ask_qty *= (1.0 - std::abs(position_) / config_.max_position * 0.5);
    }
}

void Strategy::send_order(Side side, Price price, Quantity quantity) {
    if (!order_callback_) return;
    
    Order order(next_order_id_++, last_quote_.timestamp, side, 
                OrderType::LIMIT, price, quantity);
    
    active_orders_.push_back(order);
    total_orders_sent_++;
    
    order_callback_(order);
}

void Strategy::cancel_all_orders() {
    active_orders_.clear();
}



void Strategy::update_pnl(Price current_price) {
    if (position_ == 0.0) {
        unrealized_pnl_ = 0;
        return;
    }
    
    double current_price_double = price_to_double(current_price);
    unrealized_pnl_ = position_ * (current_price_double - avg_entry_price_);
}

void Strategy::update_realized_pnl(const Fill& fill) {
    double fill_price = price_to_double(fill.price);
    
    if (position_ == 0.0) {
        avg_entry_price_ = fill_price;
    } else {
        bool same_direction = (position_ > 0 && fill.side == Side::BUY) ||
                             (position_ < 0 && fill.side == Side::SELL);
        
        if (same_direction) {
            double old_notional = position_ * avg_entry_price_;
            double new_notional = (fill.side == Side::BUY ? 1.0 : -1.0) * 
                                 fill.quantity * fill_price;
            
            double new_position = position_ + 
                                 (fill.side == Side::BUY ? fill.quantity : -fill.quantity);
            
            if (new_position != 0) {
                avg_entry_price_ = (old_notional + new_notional) / new_position;
            }
        } else {
            double pnl_per_unit = (fill.side == Side::SELL) ? 
                                 (fill_price - avg_entry_price_) :
                                 (avg_entry_price_ - fill_price);
            
            realized_pnl_ += pnl_per_unit * fill.quantity;
        }
    }
}

} // namespace trading