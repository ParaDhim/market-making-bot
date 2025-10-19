#include "market_data.hpp"
#include "order_book.hpp"
#include "strategy.hpp"
#include "simulated_exchange.hpp"
#include "signal_reader.hpp"
#include <iostream>
#include <iomanip>
#include <spdlog/spdlog.h>

int main(int argc, char* argv[]) {
    // Setup logging
    spdlog::set_pattern("[%H:%M:%S] [%^%l%$] %v");
    spdlog::info("=== Low-Latency Trading Engine Starting ===");
    
    // Get file paths
    std::string quotes_file = "../data/raw/quotes_latest.csv";
    std::string trades_file = "../data/raw/trades_latest.csv";
    std::string signals_file = "../results/signals.txt";
    std::string results_file = "../results/trades.csv";
    
    if (argc >= 3) {
        quotes_file = argv[1];
        trades_file = argv[2];
    }
    
    try {
        // Initialize components
        spdlog::info("Loading market data...");
        MarketDataParser parser(quotes_file, trades_file);
        
        OrderBook book;
        Strategy strategy(0.0002, 0.01);  // 2bps spread, 0.01 BTC orders
        SimulatedExchange exchange(results_file);
        SignalReader signals(signals_file);
        
        spdlog::info("Starting backtest simulation...");
        
        int quote_count = 0;
        int trade_count = 0;
        int signal_updates = 0;
        
        // Main event loop
        while (parser.has_more_data()) {
            if (parser.peek_next_is_quote()) {
                // Process quote
                Quote quote = parser.get_next_quote();
                book.update(quote.best_bid, quote.bid_volume, 
                           quote.best_ask, quote.ask_volume);
                
                // Update strategy with ML signal
                int signal = signals.get_current_signal();
                strategy.on_quote(book, signal);
                
                // Log state periodically
                if (quote_count % 100 == 0) {
                    double timestamp = quote_count;
                    exchange.log_state(timestamp, strategy, book.get_mid_price());
                    
                    if (quote_count % 1000 == 0) {
                        spdlog::info("Processed {} quotes, {} trades | PnL: ${:.2f} | Inventory: {:.4f}",
                                   quote_count, trade_count, strategy.get_pnl(), 
                                   strategy.get_inventory());
                    }
                }
                
                quote_count++;
                
                // Try to read next signal
                if (quote_count % 10 == 0 && signals.update()) {
                    signal_updates++;
                }
                
            } else {
                // Process trade
                Trade trade = parser.get_next_trade();
                exchange.process_trade(trade, strategy);
                trade_count++;
            }
        }
        
        // Final statistics
        spdlog::info("=== Backtest Complete ===");
        spdlog::info("Total Quotes Processed: {}", quote_count);
        spdlog::info("Total Trades Processed: {}", trade_count);
        spdlog::info("Signal Updates: {}", signal_updates);
        spdlog::info("Total Fills: {}", exchange.get_total_fills());
        spdlog::info("Final PnL: ${:.2f}", strategy.get_pnl());
        spdlog::info("Final Inventory: {:.4f} BTC", strategy.get_inventory());
        spdlog::info("Results saved to: {}", results_file);
        
    } catch (const std::exception& e) {
        spdlog::error("Fatal error: {}", e.what());
        return 1;
    }
    
    return 0;
}