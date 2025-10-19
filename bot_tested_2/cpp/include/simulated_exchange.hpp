// FILE 6: cpp/include/simulated_exchange.hpp
// ============================================================================
#ifndef SIMULATED_EXCHANGE_HPP
#define SIMULATED_EXCHANGE_HPP

#include "types.hpp"
#include <unordered_map>
#include <functional>
#include <memory>

namespace trading {

class ExecutionHandler;

class SimulatedExchange {
public:
    using FillCallback = std::function<void(const Fill&)>;
    
    SimulatedExchange();
    
    void on_trade(const Trade& trade);
    void on_quote(const Quote& quote);
    
    void submit_order(const Order& order);
    void cancel_order(OrderId order_id);
    
    void on_fill(FillCallback callback);
    
    size_t total_fills() const { return total_fills_; }
    double total_volume_traded() const { return total_volume_; }
    
private:
    FillCallback fill_callback_;
    
    std::unordered_map<OrderId, Order> pending_orders_;
    
    Quote last_quote_;
    
    size_t total_fills_;
    double total_volume_;
    
    void check_fills_against_trade(const Trade& trade);
    void check_fills_against_quote(const Quote& quote);
    
    void generate_fill(const Order& order, Price fill_price, Quantity fill_quantity);
};

} // namespace trading
#endif // SIMULATED_EXCHANGE_HPP