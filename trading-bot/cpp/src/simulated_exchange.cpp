#include "simulated_exchange.hpp"
#include <iostream>
#include <iomanip>

SimulatedExchange::SimulatedExchange(const std::string& results_file)
    : total_fills_(0) {
    
    results_file_.open(results_file);
    if (!results_file_.is_open()) {
        throw std::runtime_error("Cannot open results file: " + results_file);
    }
    
    // Write CSV header
    results_file_ << "timestamp,price,inventory,realized_pnl,unrealized_pnl,total_pnl\n";
}

SimulatedExchange::~SimulatedExchange() {
    if (results_file_.is_open()) {
        results_file_.close();
    }
}

void SimulatedExchange::process_trade(const Trade& trade, Strategy& strategy) {
    auto orders = strategy.get_active_orders();
    
    for (const auto& order : orders) {
        if (!order->is_active) continue;
        
        bool filled = false;
        
        // Check if order would be filled
        if (order->side == Side::BUY) {
            // Buy order fills if market trades at or below our bid
            if (trade.side == "sell" && trade.price <= order->price) {
                filled = true;
            }
        } else {  // SELL
            // Sell order fills if market trades at or above our ask
            if (trade.side == "buy" && trade.price >= order->price) {
                filled = true;
            }
        }
        
        if (filled) {
            strategy.on_fill(order->id, order->price, order->quantity);
            total_fills_++;
        }
    }
}

void SimulatedExchange::log_state(double timestamp, const Strategy& strategy, 
                                  double current_price) {
    double inventory = strategy.get_inventory();
    double realized_pnl = strategy.get_pnl();
    double unrealized_pnl = strategy.get_position_value(current_price);
    double total_pnl = realized_pnl + unrealized_pnl;
    
    results_file_ << std::fixed << std::setprecision(6)
                 << timestamp << ","
                 << current_price << ","
                 << inventory << ","
                 << realized_pnl << ","
                 << unrealized_pnl << ","
                 << total_pnl << "\n";
}