// main_file_based.cpp
// Trading engine with file-based ML signal reading (for debugging)

#include "include/market_data_handler.hpp"
#include "include/order_book.hpp"
#include "include/strategy.hpp"
#include "include/execution_handler.hpp"
#include "include/simulated_exchange.hpp"
#include <iostream>
#include <fstream>
#include <memory>
#include <csignal>
#include <sstream>
#include <chrono>
#include <thread>

using namespace trading;

volatile sig_atomic_t running = 1;

size_t ml_signals_received = 0;
size_t ml_signals_buy = 0;
size_t ml_signals_sell = 0;
size_t ml_signals_neutral = 0;

void signal_handler(int signal) {
    std::cout << "\nShutting down gracefully..." << std::endl;
    running = 0;
}

class FileSignalReader {
public:
    FileSignalReader(const std::string& signal_file) 
        : signal_file_(signal_file), last_position_(0) {}
    
    bool try_read_signal(MLSignal& signal) {
        std::ifstream file(signal_file_);
        if (!file.is_open()) {
            return false;
        }
        
        // Skip to last read position
        file.seekg(last_position_);
        
        std::string line;
        if (!std::getline(file, line)) {
            return false;
        }
        
        // Update position for next read
        last_position_ = file.tellg();
        
        // Parse: "signal,confidence"
        size_t comma_pos = line.find(',');
        if (comma_pos == std::string::npos) {
            return false;
        }
        
        try {
            signal.signal = std::stoi(line.substr(0, comma_pos));
            signal.confidence = std::stod(line.substr(comma_pos + 1));
            signal.timestamp = std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::system_clock::now().time_since_epoch()
            ).count();
            return true;
        } catch (...) {
            return false;
        }
    }
    
private:
    std::string signal_file_;
    std::streampos last_position_;
};

class ResultsLogger {
public:
    ResultsLogger(const std::string& output_file) {
        file_.open(output_file);
        if (!file_.is_open()) {
            throw std::runtime_error("Failed to open results file: " + output_file);
        }
        
        file_ << "timestamp,event_type,side,price,quantity,position,pnl,realized_pnl,fill_price" << std::endl;
    }
    
    ~ResultsLogger() {
        if (file_.is_open()) {
            file_.close();
        }
    }
    
    void log_fill(const Fill& fill, double position, double pnl, double realized_pnl) {
        file_ << fill.timestamp << ","
              << "FILL" << ","
              << side_to_string(fill.side) << ","
              << price_to_double(fill.price) << ","
              << fill.quantity << ","
              << position << ","
              << pnl << ","
              << realized_pnl << ","
              << price_to_double(fill.price)
              << std::endl;
    }
    
    void log_quote(const Quote& quote, double position, double pnl) {
        file_ << quote.timestamp << ","
              << "QUOTE" << ","
              << "NA" << ","
              << price_to_double(quote.mid_price()) << ","
              << "0" << ","
              << position << ","
              << pnl << ","
              << "0" << ","
              << "NA"
              << std::endl;
    }
    
private:
    std::ofstream file_;
};

int main(int argc, char* argv[]) {
    std::signal(SIGINT, signal_handler);
    
    std::cout << "======================================" << std::endl;
    std::cout << "Low-Latency Trading Engine (File-Based)" << std::endl;
    std::cout << "======================================" << std::endl;
    
    try {
        std::string trades_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/data/raw/trades.csv";
        std::string quotes_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/data/raw/quotes.csv";
        std::string signal_file = "ipc/ml_signals.txt";
        std::string results_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/results/backtest_results.csv";
        std::string ready_file = "ipc/python_ready.txt";
        
        if (argc > 1) trades_file = argv[1];
        if (argc > 2) quotes_file = argv[2];
        
        std::cout << "\nConfiguration:" << std::endl;
        std::cout << "  Trades file: " << trades_file << std::endl;
        std::cout << "  Quotes file: " << quotes_file << std::endl;
        std::cout << "  Signal file: " << signal_file << std::endl;
        std::cout << "  Results file: " << results_file << std::endl;
        
        std::cout << "\nInitializing components..." << std::endl;
        
        MarketDataHandler data_handler(trades_file, quotes_file);
        std::cout << "✓ Market data handler initialized" << std::endl;
        
        auto exchange = std::make_shared<SimulatedExchange>();
        std::cout << "✓ Simulated exchange initialized" << std::endl;
        
        auto execution = std::make_shared<ExecutionHandler>();
        execution->set_exchange(exchange);
        std::cout << "✓ Execution handler initialized" << std::endl;
        
        StrategyConfig strategy_config;
        strategy_config.base_spread_bps = 15.0;
        strategy_config.max_position = 0.5;
        strategy_config.order_size = 0.01;
        strategy_config.skew_factor = 0.5;
        
        auto strategy = std::make_shared<Strategy>(strategy_config);
        std::cout << "✓ Strategy initialized" << std::endl;
        
        ResultsLogger logger(results_file);
        std::cout << "✓ Results logger initialized" << std::endl;
        
        FileSignalReader signal_reader(signal_file);
        std::cout << "✓ File signal reader initialized" << std::endl;
        
        std::cout << "\nWiring up callbacks..." << std::endl;
        
        strategy->set_order_callback([&execution](const Order& order) {
            try {
                execution->send_order(order);
            } catch (const std::exception& e) {
                std::cerr << "Error sending order: " << e.what() << std::endl;
            }
        });
        
        execution->on_fill([&strategy, &logger](const Fill& fill) {
            strategy->on_fill(fill);
            logger.log_fill(fill, strategy->position(), strategy->pnl(), strategy->realized_pnl());
        });
        
        data_handler.on_quote([&strategy, &signal_reader, &logger](const Quote& quote) {
            strategy->on_quote(quote);
            logger.log_quote(quote, strategy->position(), strategy->pnl());
            
            // Try to read ML signals (non-blocking)
            MLSignal signal;
            int signals_read = 0;
            while (signal_reader.try_read_signal(signal) && signals_read < 10) {
                ml_signals_received++;
                signals_read++;
                
                if (signal.signal > 0) ml_signals_buy++;
                else if (signal.signal < 0) ml_signals_sell++;
                else ml_signals_neutral++;
                
                if (ml_signals_received <= 10) {
                    std::string signal_type = signal.signal > 0 ? "BUY" : 
                                             signal.signal < 0 ? "SELL" : "NEUTRAL";
                    std::cout << "🔔 ML Signal #" << ml_signals_received << ": " 
                              << signal_type << " (confidence: " << signal.confidence << ")" 
                              << std::endl;
                }
                
                strategy->on_ml_signal(signal);
            }
        });
        
        data_handler.on_trade([&strategy](const Trade& trade) {
            strategy->on_trade(trade);
        });
        
        std::cout << "✓ All callbacks wired" << std::endl;
        
        std::cout << "\n" << std::string(50, '=') << std::endl;
        std::cout << "READY FOR ML SIGNAL GENERATOR" << std::endl;
        std::cout << "Start Python: python3 python/ml/signal_generator_simple.py" << std::endl;
        std::cout << std::string(50, '=') << "\n" << std::endl;
        
        // WAIT FOR PYTHON TO BE READY - with progress indicator
        std::cout << "Waiting for Python signal generator to be ready..." << std::endl;
        auto wait_start = std::chrono::high_resolution_clock::now();
        bool python_ready = false;
        int wait_count = 0;
        
        while (!python_ready) {
            // Check if Python has created the ready file
            std::ifstream ready_check(ready_file);
            if (ready_check.good()) {
                python_ready = true;
                ready_check.close();
                std::cout << "\n✓ Python signal generator is ready!\n" << std::endl;
                break;
            }
            
            auto elapsed = std::chrono::high_resolution_clock::now() - wait_start;
            auto elapsed_secs = std::chrono::duration_cast<std::chrono::seconds>(elapsed).count();
            
            if (elapsed_secs > 120) {  // 2 minute timeout
                std::cout << "\n✗ Timeout waiting for Python. Starting anyway...\n" << std::endl;
                break;
            }
            
            // Print progress every 5 seconds
            if (wait_count % 50 == 0) {
                std::cout << "  Still waiting... (" << elapsed_secs << "s)" << std::endl;
            }
            wait_count++;
            
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        
        std::cout << "\n" << std::string(50, '=') << std::endl;
        std::cout << "STARTING TRADING ENGINE" << std::endl;
        std::cout << std::string(50, '=') << "\n" << std::endl;
        
        size_t events_processed = 0;
        auto start_time = std::chrono::high_resolution_clock::now();
        auto last_signal_check = start_time;
        
        while (running && data_handler.process_next()) {
            events_processed++;
            
            // Check for signals more frequently
            auto now = std::chrono::high_resolution_clock::now();
            auto time_since_check = std::chrono::duration_cast<std::chrono::milliseconds>(now - last_signal_check).count();
            
            if (time_since_check > 10) {  // Check every 10ms
                MLSignal signal;
                int signals_read = 0;
                while (signal_reader.try_read_signal(signal) && signals_read < 5) {
                    ml_signals_received++;
                    signals_read++;
                    
                    if (signal.signal > 0) ml_signals_buy++;
                    else if (signal.signal < 0) ml_signals_sell++;
                    else ml_signals_neutral++;
                    
                    if (ml_signals_received <= 10) {
                        std::string signal_type = signal.signal > 0 ? "BUY" : 
                                                 signal.signal < 0 ? "SELL" : "NEUTRAL";
                        std::cout << "🔔 ML Signal #" << ml_signals_received << ": " 
                                  << signal_type << " (confidence: " << signal.confidence << ")" 
                                  << std::endl;
                    }
                    
                    strategy->on_ml_signal(signal);
                }
                last_signal_check = now;
            }
            
            // Progress update
            if (events_processed % 500 == 0) {
                auto elapsed = now - start_time;
                double elapsed_ms = std::chrono::duration<double, std::milli>(elapsed).count();
                double throughput = events_processed / (elapsed_ms / 1000.0);
                
                std::cout << "[" << events_processed << "] "
                          << "Rate: " << static_cast<int>(throughput) << " ev/s | "
                          << "ML Signals: " << ml_signals_received << " | "
                          << "Position: " << strategy->position() << " | "
                          << "PnL: $" << strategy->pnl()
                          << std::endl;
            }
        }
        
        std::cout << "\nWaiting 2 seconds for remaining signals..." << std::endl;
        for (int i = 0; i < 20; i++) {
            MLSignal signal;
            while (signal_reader.try_read_signal(signal)) {
                ml_signals_received++;
                if (signal.signal > 0) ml_signals_buy++;
                else if (signal.signal < 0) ml_signals_sell++;
                else ml_signals_neutral++;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        
        auto elapsed = std::chrono::high_resolution_clock::now() - start_time;
        double elapsed_sec = std::chrono::duration<double>(elapsed).count();
        
        std::cout << "\n" << std::string(50, '=') << std::endl;
        std::cout << "BACKTEST COMPLETE" << std::endl;
        std::cout << std::string(50, '=') << "\n" << std::endl;
        
        std::cout << "Events Processed: " << events_processed << std::endl;
        std::cout << "  Trades: " << data_handler.trades_processed() << std::endl;
        std::cout << "  Quotes: " << data_handler.quotes_processed() << std::endl;
        std::cout << "Execution Time: " << elapsed_sec << " seconds" << std::endl;
        std::cout << "Throughput: " << static_cast<int>(events_processed / elapsed_sec) << " events/sec" << std::endl;
        
        std::cout << "\nML Signal Statistics:" << std::endl;
        std::cout << "  Total Received: " << ml_signals_received << std::endl;
        if (ml_signals_received > 0) {
            std::cout << "  BUY: " << ml_signals_buy 
                      << " (" << (100.0 * ml_signals_buy / ml_signals_received) << "%)" << std::endl;
            std::cout << "  SELL: " << ml_signals_sell 
                      << " (" << (100.0 * ml_signals_sell / ml_signals_received) << "%)" << std::endl;
            std::cout << "  NEUTRAL: " << ml_signals_neutral 
                      << " (" << (100.0 * ml_signals_neutral / ml_signals_received) << "%)" << std::endl;
        }
        
        std::cout << "\nStrategy Performance:" << std::endl;
        std::cout << "  Final Position: " << strategy->position() << std::endl;
        std::cout << "  Total PnL: $" << strategy->pnl() << std::endl;
        std::cout << "  Realized PnL: $" << strategy->realized_pnl() << std::endl;
        
        std::cout << "\nResults: " << results_file << std::endl;
        std::cout << "✓ Engine shutdown complete" << std::endl;
        
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "\n✗ Error: " << e.what() << std::endl;
        return 1;
    }
}