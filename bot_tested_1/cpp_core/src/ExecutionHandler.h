// cpp_core/src/ExecutionHandler.h
#pragma once
#include "MarketData.h"

class ExecutionHandler {
public:
    ExecutionHandler() : pnl_(0.0), position_(0) {}

    // Simulates checking if our orders would be filled by an incoming market trade
    void check_fills(const Trade& market_trade, double our_bid, double our_ask);

    double get_pnl() const { return pnl_; }
    int get_position() const { return position_; }

private:
    double pnl_;
    int position_; // Our inventory
};