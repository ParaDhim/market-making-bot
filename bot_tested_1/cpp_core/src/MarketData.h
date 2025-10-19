// cpp_core/src/MarketData.h
#pragma once
#include <string>

struct Quote {
    long long timestamp;
    double bid_price;
    int bid_qty;
    double ask_price;
    int ask_qty;
};

struct Trade {
    long long timestamp;
    double price;
    int qty;
    std::string side;
};