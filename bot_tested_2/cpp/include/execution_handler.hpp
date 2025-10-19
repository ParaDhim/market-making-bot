// FILE 5: cpp/include/execution_handler.hpp
// ============================================================================
#ifndef EXECUTION_HANDLER_HPP
#define EXECUTION_HANDLER_HPP

#include "types.hpp"
#include <unordered_map>
#include <functional>
#include <memory>

namespace trading {

class SimulatedExchange;

class ExecutionHandler {
public:
    using FillCallback = std::function<void(const Fill&)>;
    
    ExecutionHandler();
    ~ExecutionHandler();
    
    void set_exchange(std::shared_ptr<SimulatedExchange> exchange);
    
    OrderId send_order(const Order& order);
    bool cancel_order(OrderId order_id);
    bool modify_order(OrderId order_id, Price new_price, Quantity new_quantity);
    
    void on_fill(FillCallback callback);
    
    OrderStatus get_order_status(OrderId order_id) const;
    size_t active_order_count() const;
    
    size_t total_orders_sent() const { return total_orders_sent_; }
    size_t total_fills_received() const { return total_fills_received_; }
    
private:
    std::shared_ptr<SimulatedExchange> exchange_;
    FillCallback fill_callback_;
    
    std::unordered_map<OrderId, Order> active_orders_;
    
    size_t total_orders_sent_;
    size_t total_fills_received_;
    
    void process_fill(const Fill& fill);
    
    friend class SimulatedExchange;
};

} // namespace trading
#endif // EXECUTION_HANDLER_HPP
