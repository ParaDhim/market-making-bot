// cpp_core/src/Strategy.h
#pragma once
#include "OrderBook.h"
#include "ExecutionHandler.h"

class Strategy {
public:
    Strategy() : current_signal_(0), spread_(0.02) {}

    void on_quote(const Quote& quote);
    void on_trade(const Trade& trade);
    void on_signal(int signal);

    double get_pnl() const { return execution_handler_.get_pnl(); }

private:
    OrderBook order_book_;
    ExecutionHandler execution_handler_;
    
    int current_signal_; // -1, 0, or 1
    double spread_;
    
    // Our current resting orders
    double our_bid_price_ = 0.0;
    double our_ask_price_ = 0.0;
};