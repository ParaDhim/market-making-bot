// FILE 4: cpp/include/strategy.hpp
// ============================================================================
#ifndef STRATEGY_HPP
#define STRATEGY_HPP

#include "types.hpp"
#include "order_book.hpp"
#include <vector>
#include <memory>
#include <functional>

namespace trading {

class ExecutionHandler;

struct StrategyConfig {
    double base_spread_bps = 10.0;
    double max_position = 1.0;
    double order_size = 0.01;
    double skew_factor = 0.5;
    double inventory_penalty = 0.1;
    
    StrategyConfig() = default;
};

class Strategy {
public:
    using OrderCallback = std::function<void(const Order&)>;
    
    Strategy(const StrategyConfig& config);
    
    void on_quote(const Quote& quote);
    void on_trade(const Trade& trade);
    void on_fill(const Fill& fill);
    void on_ml_signal(const MLSignal& signal);
    
    void set_order_callback(OrderCallback callback);
    
    double position() const { return position_; }
    double pnl() const { return realized_pnl_ + unrealized_pnl_; }
    double realized_pnl() const { return realized_pnl_; }
    
    size_t total_orders() const { return total_orders_sent_; }
    size_t total_fills() const { return total_fills_; }
    
private:
    StrategyConfig config_;
    OrderCallback order_callback_;
    
    OrderBook order_book_;
    Quote last_quote_;
    MLSignal last_signal_;
    
    double position_;
    double avg_entry_price_;
    double realized_pnl_;
    double unrealized_pnl_;
    
    std::vector<Order> active_orders_;
    OrderId next_order_id_;
    
    size_t total_orders_sent_;
    size_t total_fills_;
    
    void update_quotes();
    void calculate_target_quotes(Price& bid_price, Price& ask_price, 
                                 Quantity& bid_qty, Quantity& ask_qty);
    void cancel_all_orders();
    void send_order(Side side, Price price, Quantity quantity);
    
    void update_pnl(Price current_price);
    void update_realized_pnl(const Fill& fill);
};

} // namespace trading
#endif // STRATEGY_HPP

