#include "OrderBook.h"
#include <iostream>
#include <cassert> // For simple assertions

// We need to include the .cpp file directly here to get the method implementations,
// or link them during compilation. For a simple test, including it is easiest.
#include "implementations.cpp" 

void run_orderbook_tests() {
    std::cout << "--- Running OrderBook Tests ---" << std::endl;

    OrderBook book;

    // Test 1: Initial state
    assert(book.get_best_bid() == 0.0);
    assert(book.get_best_ask() > 1e9); // Should be a very large number
    assert(book.get_mid_price() == 0.0);
    std::cout << "✅ Test 1 Passed: Initial state is correct." << std::endl;

    // Test 2: Update with a valid quote
    Quote q1;
    q1.bid_price = 99.5;
    q1.bid_qty = 10;
    q1.ask_price = 100.5;
    q1.ask_qty = 10;
    
    book.update_quote(q1);

    assert(book.get_best_bid() == 99.5);
    assert(book.get_best_ask() == 100.5);
    assert(book.get_mid_price() == 100.0);
    std::cout << "✅ Test 2 Passed: Quote update works correctly." << std::endl;

    // Test 3: Update with a zero-quantity quote (should effectively clear the book)
    Quote q2;
    q2.bid_price = 99.0;
    q2.bid_qty = 0;
    q2.ask_price = 101.0;
    q2.ask_qty = 0;

    book.update_quote(q2);
    assert(book.get_best_bid() == 0.0);
    assert(book.get_best_ask() > 1e9);
    std::cout << "✅ Test 3 Passed: Zero-quantity quote clears the book." << std::endl;

    std::cout << "--- All OrderBook Tests Passed ---" << std::endl;
}

int main() {
    run_orderbook_tests();
    // You can add calls to other test functions here, e.g., run_execution_tests()
    return 0;
}