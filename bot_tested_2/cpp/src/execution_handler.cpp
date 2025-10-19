// FILE 3: cpp/src/execution_handler.cpp
// ============================================================================
#include "execution_handler.hpp"
#include "simulated_exchange.hpp"

namespace trading {

ExecutionHandler::ExecutionHandler()
    : total_orders_sent_(0), total_fills_received_(0) {}

ExecutionHandler::~ExecutionHandler() {}

void ExecutionHandler::set_exchange(std::shared_ptr<SimulatedExchange> exchange) {
    exchange_ = exchange;
    
    if (exchange_) {
        exchange_->on_fill([this](const Fill& fill) {
            this->process_fill(fill);
        });
    }
}

OrderId ExecutionHandler::send_order(const Order& order) {
    if (!exchange_) {
        throw std::runtime_error("No exchange connected");
    }
    
    active_orders_[order.id] = order;
    total_orders_sent_++;
    
    exchange_->submit_order(order);
    
    return order.id;
}

bool ExecutionHandler::cancel_order(OrderId order_id) {
    if (!exchange_) return false;
    
    auto it = active_orders_.find(order_id);
    if (it == active_orders_.end()) return false;
    
    exchange_->cancel_order(order_id);
    active_orders_.erase(it);
    
    return true;
}

bool ExecutionHandler::modify_order(OrderId order_id, Price new_price, 
                                    Quantity new_quantity) {
    auto it = active_orders_.find(order_id);
    if (it == active_orders_.end()) return false;
    
    Order old_order = it->second;
    cancel_order(order_id);
    
    Order new_order = old_order;
    new_order.price = new_price;
    new_order.quantity = new_quantity;
    
    send_order(new_order);
    return true;
}

void ExecutionHandler::on_fill(FillCallback callback) {
    fill_callback_ = callback;
}

OrderStatus ExecutionHandler::get_order_status(OrderId order_id) const {
    auto it = active_orders_.find(order_id);
    if (it != active_orders_.end()) {
        return it->second.status;
    }
    return OrderStatus::REJECTED;
}

size_t ExecutionHandler::active_order_count() const {
    return active_orders_.size();
}

void ExecutionHandler::process_fill(const Fill& fill) {
    total_fills_received_++;
    
    active_orders_.erase(fill.order_id);
    
    if (fill_callback_) {
        fill_callback_(fill);
    }
}

} // namespace trading
