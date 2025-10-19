// cpp/tests/test_order_book.cpp
// Unit tests for OrderBook

#include "order_book.hpp"
#include <iostream>
#include <cassert>

using namespace trading;

void test_basic_operations() {
    std::cout << "Testing basic operations..." << std::endl;
    
    OrderBook book;
    
    // Add bid and ask
    Quote q1(1000, 
             double_to_price(100.00), 1.0,
             double_to_price(100.10), 1.0);
    
    book.update(q1);
    
    auto bid = book.best_bid();
    auto ask = book.best_ask();
    
    assert(bid.has_value());
    assert(ask.has_value());
    assert(bid.value() == double_to_price(100.00));
    assert(ask.value() == double_to_price(100.10));
    
    std::cout << "✓ Basic operations test passed" << std::endl;
}

void test_imbalance() {
    std::cout << "Testing order book imbalance..." << std::endl;
    
    OrderBook book;
    
    // Bid volume > Ask volume
    Quote q1(1000,
             double_to_price(100.00), 2.0,
             double_to_price(100.10), 1.0);
    
    book.update(q1);
    
    double imb = book.imbalance();
    assert(imb > 0);  // Positive imbalance (more bids)
    
    std::cout << "✓ Imbalance test passed (imbalance = " << imb << ")" << std::endl;
}

void test_depth() {
    std::cout << "Testing order book depth..." << std::endl;
    
    OrderBook book;
    
    Quote q1(1000,
             double_to_price(100.00), 1.5,
             double_to_price(100.10), 2.5);
    
    book.update(q1);
    
    auto bid_depth = book.total_bid_volume(1);
    auto ask_depth = book.total_ask_volume(1);
    
    assert(bid_depth == 1.5);
    assert(ask_depth == 2.5);
    
    std::cout << "✓ Depth test passed (bid: " << bid_depth 
              << ", ask: " << ask_depth << ")" << std::endl;
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "OrderBook Unit Tests" << std::endl;
    std::cout << "========================================\n" << std::endl;
    
    try {
        test_basic_operations();
        test_imbalance();
        test_depth();
        
        std::cout << "\n========================================" << std::endl;
        std::cout << "✓ All tests passed!" << std::endl;
        std::cout << "========================================" << std::endl;
        
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "\n✗ Test failed: " << e.what() << std::endl;
        return 1;
    }
}