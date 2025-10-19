// FILE 1: cpp/include/types.hpp
// ============================================================================
#ifndef TYPES_HPP
#define TYPES_HPP

#include <cstdint>
#include <string>

namespace trading {

using Timestamp = uint64_t;
using Price = int64_t;
using Quantity = double;
using OrderId = uint64_t;

enum class Side { BUY, SELL, UNKNOWN };
enum class OrderType { LIMIT, MARKET, CANCEL };
enum class OrderStatus { PENDING, ACCEPTED, FILLED, PARTIALLY_FILLED, CANCELLED, REJECTED };

struct Trade {
    Timestamp timestamp;
    Price price;
    Quantity quantity;
    Side side;
    
    Trade() : timestamp(0), price(0), quantity(0.0), side(Side::UNKNOWN) {}
    Trade(Timestamp ts, Price p, Quantity q, Side s) 
        : timestamp(ts), price(p), quantity(q), side(s) {}
};

struct Quote {
    Timestamp timestamp;
    Price bid_price;
    Quantity bid_volume;
    Price ask_price;
    Quantity ask_volume;
    
    Quote() : timestamp(0), bid_price(0), bid_volume(0.0), ask_price(0), ask_volume(0.0) {}
    Quote(Timestamp ts, Price bp, Quantity bv, Price ap, Quantity av)
        : timestamp(ts), bid_price(bp), bid_volume(bv), ask_price(ap), ask_volume(av) {}
    
    Price mid_price() const { return (bid_price + ask_price) / 2; }
    Price spread() const { return ask_price - bid_price; }
};

struct Order {
    OrderId id;
    Timestamp timestamp;
    Side side;
    OrderType type;
    Price price;
    Quantity quantity;
    OrderStatus status;
    
    Order() : id(0), timestamp(0), side(Side::UNKNOWN), type(OrderType::LIMIT), 
              price(0), quantity(0.0), status(OrderStatus::PENDING) {}
    Order(OrderId oid, Timestamp ts, Side s, OrderType t, Price p, Quantity q)
        : id(oid), timestamp(ts), side(s), type(t), price(p), quantity(q), 
          status(OrderStatus::PENDING) {}
};

struct Fill {
    OrderId order_id;
    Timestamp timestamp;
    Price price;
    Quantity quantity;
    Side side;
    
    Fill() : order_id(0), timestamp(0), price(0), quantity(0.0), side(Side::UNKNOWN) {}
    Fill(OrderId oid, Timestamp ts, Price p, Quantity q, Side s)
        : order_id(oid), timestamp(ts), price(p), quantity(q), side(s) {}
};

struct MLSignal {
    int signal;
    double confidence;
    Timestamp timestamp;
    
    MLSignal() : signal(0), confidence(0.5), timestamp(0) {}
    MLSignal(int sig, double conf, Timestamp ts) 
        : signal(sig), confidence(conf), timestamp(ts) {}
};

inline Side string_to_side(const std::string& str) {
    if (str == "buy" || str == "BUY") return Side::BUY;
    if (str == "sell" || str == "SELL") return Side::SELL;
    return Side::UNKNOWN;
}

inline std::string side_to_string(Side side) {
    switch (side) {
        case Side::BUY: return "BUY";
        case Side::SELL: return "SELL";
        default: return "UNKNOWN";
    }
}

inline Price double_to_price(double price) {
    return static_cast<Price>(price * 100.0);
}

inline double price_to_double(Price price) {
    return static_cast<double>(price) / 100.0;
}

} // namespace trading
#endif // TYPES_HPP

