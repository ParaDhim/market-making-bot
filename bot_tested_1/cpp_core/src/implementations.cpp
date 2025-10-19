// cpp_core/src/implementations.cpp

#include "Strategy.h"
#include <iostream>
#include <limits>

// --- Implementation of Class Methods ---

// OrderBook
void OrderBook::update_quote(const Quote& quote) {
    // For simplicity, we just set the new best bid/ask
    // A real order book would manage multiple price levels.
    bids_.clear();
    asks_.clear();
    if (quote.bid_qty > 0) {
        bids_[quote.bid_price] = quote.bid_qty;
    }
    if (quote.ask_qty > 0) {
        asks_[quote.ask_price] = quote.ask_qty;
    }
}

double OrderBook::get_best_bid() const {
    if (bids_.empty()) return 0.0;
    return bids_.begin()->first;
}

double OrderBook::get_best_ask() const {
    if (asks_.empty()) return std::numeric_limits<double>::max();
    return asks_.begin()->first;
}

double OrderBook::get_mid_price() const {
    if (bids_.empty() || asks_.empty()) return 0.0;
    return (get_best_bid() + get_best_ask()) / 2.0;
}

// ExecutionHandler
void ExecutionHandler::check_fills(const Trade& market_trade, double our_bid, double our_ask) {
    // If market sells into our bid
    if (market_trade.side == "sell" && market_trade.price <= our_bid) {
        pnl_ -= market_trade.qty * our_bid;
        position_ += market_trade.qty;
        std::cout << "FILLED BUY @ " << our_bid << std::endl;
    }
    // If market buys into our ask
    if (market_trade.side == "buy" && market_trade.price >= our_ask) {
        pnl_ += market_trade.qty * our_ask;
        position_ -= market_trade.qty;
        std::cout << "FILLED SELL @ " << our_ask << std::endl;
    }
}

// Strategy
void Strategy::on_quote(const Quote& quote) {
    order_book_.update_quote(quote);
    double mid_price = order_book_.get_mid_price();
    if (mid_price == 0.0) return;

    // Skew quotes based on ML signal
    double bid_skew = (current_signal_ == 1) ? 0.005 : 0; // If signal is UP, bid more aggressively
    double ask_skew = (current_signal_ == -1) ? 0.005 : 0; // If signal is DOWN, ask more aggressively

    our_bid_price_ = mid_price - (spread_ / 2.0) + bid_skew;
    our_ask_price_ = mid_price + (spread_ / 2.0) - ask_skew;
}

void Strategy::on_trade(const Trade& trade) {
    execution_handler_.check_fills(trade, our_bid_price_, our_ask_price_);
}

void Strategy::on_signal(int signal) {
    current_signal_ = signal;
    // std::cout << "Received signal: " << signal << std::endl;
}