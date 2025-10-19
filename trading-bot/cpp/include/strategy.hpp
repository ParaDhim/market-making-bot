#pragma once

#include "order_book.hpp"
#include <vector>
#include <memory>

enum class Side { BUY, SELL };

struct Order {
    int id;
    Side side;
    double price;
    double quantity;
    bool is_active;
    
    Order(int id_, Side side_, double price_, double qty_)
        : id(id_), side(side_), price(price_), quantity(qty_), is_active(true) {}
};

class Strategy {
public:
    Strategy(double spread_factor = 0.0002, double order_size = 0.01);
    
    void on_quote(const OrderBook& book, int ml_signal);
    std::vector<std::shared_ptr<Order>> get_active_orders() const;
    
    double get_inventory() const { return inventory_; }
    double get_pnl() const { return realized_pnl_ + unrealized_pnl_; }
    double get_position_value(double current_price) const;
    
    void on_fill(int order_id, double fill_price, double fill_qty);
    
private:
    void cancel_all_orders();
    void place_orders(double bid_price, double ask_price, int ml_signal);
    
    double spread_factor_;
    double order_size_;
    double inventory_;
    double realized_pnl_;
    double unrealized_pnl_;
    double avg_entry_price_;
    
    int next_order_id_;
    std::vector<std::shared_ptr<Order>> active_orders_;
};