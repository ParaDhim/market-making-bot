// // main_improved.cpp
// // Enhanced trading engine with proper signal synchronization and IPC handshake
// // FIXED: Detects Python shutdown and stops gracefully
// // FIXED: Signal reader thread stops before final drain to prevent infinite loop

// #include "include/market_data_handler.hpp"
// #include "include/order_book.hpp"
// #include "include/strategy.hpp"
// #include "include/execution_handler.hpp"
// #include "include/simulated_exchange.hpp"
// #include <iostream>
// #include <fstream>
// #include <memory>
// #include <csignal>
// #include <sstream>
// #include <chrono>
// #include <thread>
// #include <queue>
// #include <mutex>
// #include <atomic>

// using namespace trading;

// volatile sig_atomic_t running = 1;

// size_t ml_signals_received = 0;
// size_t ml_signals_buy = 0;
// size_t ml_signals_sell = 0;
// size_t ml_signals_neutral = 0;
// size_t ml_signals_processed_in_decisions = 0;

// void signal_handler(int signal) {
//     std::cout << "\nShutting down gracefully..." << std::endl;
//     running = 0;
// }

// class BufferedSignalReader {
// public:
//     BufferedSignalReader(const std::string& signal_file, size_t buffer_size = 1000) 
//         : signal_file_(signal_file), 
//           buffer_size_(buffer_size),
//           file_position_(0),
//           read_errors_(0),
//           signals_seen_(0),
//           signals_used_in_strategy_(0) {
//         start_reader_thread();
//     }
    
//     ~BufferedSignalReader() {
//         should_exit_ = true;
//         if (reader_thread_.joinable()) {
//             reader_thread_.join();
//         }
//     }
    
//     bool try_get_signal(MLSignal& signal) {
//         std::lock_guard<std::mutex> lock(queue_mutex_);
//         if (!signal_queue_.empty()) {
//             signal = signal_queue_.front();
//             signal_queue_.pop();
//             signals_used_in_strategy_++;
//             return true;
//         }
//         return false;
//     }
    
//     size_t queue_size() const {
//         std::lock_guard<std::mutex> lock(queue_mutex_);
//         return signal_queue_.size();
//     }
    
//     size_t get_read_errors() const {
//         return read_errors_;
//     }
    
//     size_t signals_seen() const {
//         return signals_seen_;
//     }
    
//     size_t signals_used() const {
//         return signals_used_in_strategy_;
//     }
    
//     void stop_reader() {
//         should_exit_ = true;
//         if (reader_thread_.joinable()) {
//             reader_thread_.join();
//         }
//         std::cout << "[SIGNAL READER] Background thread stopped" << std::endl;
//     }
    
//     void print_debug_info() const {
//         std::cout << "[SIGNAL READER DEBUG]" << std::endl;
//         std::cout << "  Queue size: " << queue_size() << std::endl;
//         std::cout << "  Signals seen: " << signals_seen_ << std::endl;
//         std::cout << "  Signals used: " << signals_used_in_strategy_ << std::endl;
//         std::cout << "  Read errors: " << read_errors_ << std::endl;
//         std::cout << "  File position: " << file_position_ << std::endl;
//     }
    
// private:
//     void start_reader_thread() {
//         reader_thread_ = std::thread([this]() {
//             while (!should_exit_) {
//                 try_fill_buffer();
//                 std::this_thread::sleep_for(std::chrono::milliseconds(2));
//             }
//         });
//     }
    
//     void try_fill_buffer() {
//         std::lock_guard<std::mutex> lock(queue_mutex_);
        
//         if (signal_queue_.size() >= buffer_size_) {
//             return;
//         }
        
//         std::ifstream file(signal_file_);
//         if (!file.is_open()) {
//             return;
//         }
        
//         if (file_position_ > 0) {
//             file.seekg(file_position_);
//             if (!file.good()) {
//                 file.clear();
//                 file.seekg(0);
//                 file_position_ = 0;
//             }
//         }
        
//         std::string line;
//         int signals_read = 0;
        
//         while (std::getline(file, line) && signals_read < 200) {
//             if (line.empty() || line.find("signal,confidence") != std::string::npos) {
//                 continue;
//             }
            
//             size_t comma_pos = line.find(',');
//             if (comma_pos == std::string::npos) {
//                 read_errors_++;
//                 continue;
//             }
            
//             try {
//                 MLSignal signal;
//                 std::string signal_str = line.substr(0, comma_pos);
//                 std::string conf_str = line.substr(comma_pos + 1);
                
//                 signal_str.erase(0, signal_str.find_first_not_of(" \t\r\n"));
//                 signal_str.erase(signal_str.find_last_not_of(" \t\r\n") + 1);
//                 conf_str.erase(0, conf_str.find_first_not_of(" \t\r\n"));
//                 conf_str.erase(conf_str.find_last_not_of(" \t\r\n") + 1);
                
//                 signal.signal = std::stoi(signal_str);
//                 signal.confidence = std::stod(conf_str);
//                 signal.timestamp = std::chrono::duration_cast<std::chrono::nanoseconds>(
//                     std::chrono::system_clock::now().time_since_epoch()
//                 ).count();
                
//                 signal_queue_.push(signal);
//                 signals_read++;
//                 signals_seen_++;
//             } catch (const std::exception& e) {
//                 read_errors_++;
//                 std::cerr << "Parse error at line: " << line << " - " << e.what() << std::endl;
//             }
//         }
        
//         std::streampos current_pos = file.tellg();
//         if (current_pos != std::streampos(-1)) {
//             file_position_ = current_pos;
//         }
//     }
    
//     std::string signal_file_;
//     size_t buffer_size_;
//     std::streampos file_position_;
//     std::atomic<bool> should_exit_{false};
//     std::atomic<size_t> read_errors_{0};
//     std::atomic<size_t> signals_seen_{0};
//     std::atomic<size_t> signals_used_in_strategy_{0};
    
//     std::queue<MLSignal> signal_queue_;
//     mutable std::mutex queue_mutex_;
//     std::thread reader_thread_;
// };

// class ConnectionMonitor {
// public:
//     ConnectionMonitor(const std::string& cpp_file, const std::string& python_file)
//         : cpp_status_file_(cpp_file), python_status_file_(python_file) {}
    
//     void announce_cpp_ready() {
//         write_status_file(cpp_status_file_, "CPP_READY");
//         std::cout << "\n[CONNECTION] C++ Engine: READY (wrote status file)" << std::endl;
//     }
    
//     void announce_cpp_processing() {
//         write_status_file(cpp_status_file_, "CPP_PROCESSING");
//     }
    
//     void announce_cpp_shutdown() {
//         write_status_file(cpp_status_file_, "CPP_SHUTDOWN");
//         std::cout << "\n[CONNECTION] C++ Engine: SHUTDOWN (status updated)" << std::endl;
//     }
    
//     bool is_python_running() {
//         std::string status = read_status_file(python_status_file_);
//         return status == "PYTHON_RUNNING" || status == "PYTHON_SENDING";
//     }
    
//     bool is_python_sending_signals() {
//         return read_status_file(python_status_file_) == "PYTHON_SENDING";
//     }
    
//     bool is_python_shutdown() {
//         return read_status_file(python_status_file_) == "PYTHON_SHUTDOWN";
//     }
    
// private:
//     void write_status_file(const std::string& file, const std::string& status) {
//         std::ofstream f(file);
//         if (f.is_open()) {
//             f << status << std::endl;
//             f.close();
//         }
//     }
    
//     std::string read_status_file(const std::string& file) {
//         std::ifstream f(file);
//         if (f.is_open()) {
//             std::string status;
//             std::getline(f, status);
//             f.close();
//             return status;
//         }
//         return "";
//     }
    
//     std::string cpp_status_file_;
//     std::string python_status_file_;
// };

// class ResultsLogger {
// public:
//     ResultsLogger(const std::string& output_file) {
//         file_.open(output_file);
//         if (!file_.is_open()) {
//             throw std::runtime_error("Failed to open results file: " + output_file);
//         }
        
//         file_ << "timestamp,event_type,side,price,quantity,position,pnl,realized_pnl,fill_price,ml_signal_used" << std::endl;
//     }
    
//     ~ResultsLogger() {
//         if (file_.is_open()) {
//             file_.close();
//         }
//     }
    
//     void log_fill(const Fill& fill, double position, double pnl, double realized_pnl, bool signal_used) {
//         file_ << fill.timestamp << ","
//               << "FILL" << ","
//               << side_to_string(fill.side) << ","
//               << price_to_double(fill.price) << ","
//               << fill.quantity << ","
//               << position << ","
//               << pnl << ","
//               << realized_pnl << ","
//               << price_to_double(fill.price) << ","
//               << (signal_used ? "1" : "0")
//               << std::endl;
//     }
    
//     void log_quote(const Quote& quote, double position, double pnl, bool signal_used) {
//         file_ << quote.timestamp << ","
//               << "QUOTE" << ","
//               << "NA" << ","
//               << price_to_double(quote.mid_price()) << ","
//               << "0" << ","
//               << position << ","
//               << pnl << ","
//               << "0" << ","
//               << "NA" << ","
//               << (signal_used ? "1" : "0")
//               << std::endl;
//     }
    
// private:
//     std::ofstream file_;
// };

// int main(int argc, char* argv[]) {
//     std::signal(SIGINT, signal_handler);
    
//     std::cout << "======================================" << std::endl;
//     std::cout << "Low-Latency Trading Engine (FIXED)" << std::endl;
//     std::cout << "======================================" << std::endl;
    
//     try {
//         std::string trades_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/data/raw/trades.csv";
//         std::string quotes_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/data/raw/quotes.csv";
//         std::string signal_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/ipc/ml_signals.txt";
//         std::string results_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/results/backtest_results.csv";
//         std::string cpp_status_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/ipc/cpp_status.txt";
//         std::string python_status_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/ipc/python_status.txt";
        
//         if (argc > 1) trades_file = argv[1];
//         if (argc > 2) quotes_file = argv[2];
        
//         std::cout << "\nConfiguration:" << std::endl;
//         std::cout << "  Trades file: " << trades_file << std::endl;
//         std::cout << "  Quotes file: " << quotes_file << std::endl;
//         std::cout << "  Signal file: " << signal_file << std::endl;
//         std::cout << "  Results file: " << results_file << std::endl;
        
//         std::cout << "\nInitializing components..." << std::endl;
        
//         MarketDataHandler data_handler(trades_file, quotes_file);
//         std::cout << "✓ Market data handler initialized" << std::endl;
        
//         auto exchange = std::make_shared<SimulatedExchange>();
//         std::cout << "✓ Simulated exchange initialized" << std::endl;
        
//         auto execution = std::make_shared<ExecutionHandler>();
//         execution->set_exchange(exchange);
//         std::cout << "✓ Execution handler initialized" << std::endl;
        
//         StrategyConfig strategy_config;
//         strategy_config.base_spread_bps = 15.0;
//         strategy_config.max_position = 0.5;
//         strategy_config.order_size = 0.01;
//         strategy_config.skew_factor = 0.5;
        
//         auto strategy = std::make_shared<Strategy>(strategy_config);
//         std::cout << "✓ Strategy initialized" << std::endl;
        
//         ResultsLogger logger(results_file);
//         std::cout << "✓ Results logger initialized" << std::endl;
        
//         BufferedSignalReader signal_reader(signal_file, 10000);
//         std::cout << "✓ Buffered signal reader initialized (buffer: 10000)" << std::endl;
        
//         ConnectionMonitor connection(cpp_status_file, python_status_file);
//         std::cout << "✓ Connection monitor initialized" << std::endl;
        
//         std::cout << "\nWiring up callbacks..." << std::endl;
        
//         strategy->set_order_callback([&execution](const Order& order) {
//             try {
//                 execution->send_order(order);
//             } catch (const std::exception& e) {
//                 std::cerr << "Error sending order: " << e.what() << std::endl;
//             }
//         });
        
//         execution->on_fill([&strategy, &logger](const Fill& fill) {
//             strategy->on_fill(fill);
//             logger.log_fill(fill, strategy->position(), strategy->pnl(), strategy->realized_pnl(), false);
//         });
        
//         data_handler.on_quote([&strategy, &signal_reader, &logger, &exchange](const Quote& quote) {
//             strategy->on_quote(quote);
//             exchange->on_quote(quote);
            
//             bool signal_used = false;
//             MLSignal signal;
//             while (signal_reader.try_get_signal(signal)) {
//                 ml_signals_received++;
//                 ml_signals_processed_in_decisions++;
                
//                 if (signal.signal > 0) ml_signals_buy++;
//                 else if (signal.signal < 0) ml_signals_sell++;
//                 else ml_signals_neutral++;
                
//                 strategy->on_ml_signal(signal);
//                 signal_used = true;
//             }
            
//             logger.log_quote(quote, strategy->position(), strategy->pnl(), signal_used);
//         });
        
//         data_handler.on_trade([&strategy, &exchange](const Trade& trade) {
//             strategy->on_trade(trade);
//             exchange->on_trade(trade);
//         });
        
//         std::cout << "✓ All callbacks wired" << std::endl;
        
//         connection.announce_cpp_ready();
        
//         std::cout << "\n" << std::string(70, '=') << std::endl;
//         std::cout << "WAITING FOR PYTHON SIGNAL GENERATOR CONNECTION..." << std::endl;
//         std::cout << std::string(70, '=') << std::endl;
//         std::cout << "\nIn another terminal, run:" << std::endl;
//         std::cout << "  python3 python/ml/signal_generator_simple.py" << std::endl;
//         std::cout << "\n" << std::string(70, '=') << "\n" << std::endl;
        
//         auto start_wait = std::chrono::high_resolution_clock::now();
//         bool python_detected = false;
//         int wait_count = 0;
        
//         while (!python_detected && std::chrono::high_resolution_clock::now() - start_wait < std::chrono::seconds(60)) {
//             if (connection.is_python_running()) {
//                 python_detected = true;
//                 std::cout << "✓ [CONNECTION] Python process detected! Connection established.\n" << std::endl;
//                 break;
//             }
            
//             wait_count++;
//             if (wait_count % 4 == 0) {
//                 std::cout << "  Waiting for Python... (" << (wait_count / 2) << "s)" << std::endl;
//             }
//             std::this_thread::sleep_for(std::chrono::milliseconds(500));
//         }
        
//         if (!python_detected) {
//             std::cerr << "\n✗ TIMEOUT: Python process not detected after 60 seconds." << std::endl;
//             std::cerr << "  Please start Python in another terminal:" << std::endl;
//             std::cerr << "    python3 python/ml/signal_generator_simple.py" << std::endl;
//             connection.announce_cpp_shutdown();
//             return 1;
//         }
        
//         std::cout << "Waiting for Python to start sending signals...\n" << std::endl;
//         int signal_wait = 0;
//         while (!connection.is_python_sending_signals() && signal_wait < 30) {
//             std::cout << "  Waiting... (" << signal_wait << "s)" << std::endl;
//             std::this_thread::sleep_for(std::chrono::seconds(1));
//             signal_wait++;
//         }
        
//         if (connection.is_python_sending_signals()) {
//             std::cout << "✓ [CONNECTION] Python started sending signals!\n" << std::endl;
//         }
        
//         std::cout << "\n" << std::string(70, '=') << std::endl;
//         std::cout << "STARTING TRADING ENGINE - MONITORING ML SIGNAL DECISIONS" << std::endl;
//         std::cout << std::string(70, '=') << "\n" << std::endl;
        
//         size_t events_processed = 0;
//         auto start_time = std::chrono::high_resolution_clock::now();
//         size_t last_signals_received = 0;
//         size_t last_signals_used = 0;
//         auto last_python_check = start_time;
        
//         // CRITICAL FIX: Check for Python shutdown in main loop
//         while (running && data_handler.process_next()) {
//             events_processed++;
//             connection.announce_cpp_processing();
            
//             // Check if Python has shutdown every second
//             auto now = std::chrono::high_resolution_clock::now();
//             if (now - last_python_check > std::chrono::seconds(1)) {
//                 if (connection.is_python_shutdown()) {
//                     std::cout << "\n[CONNECTION] Python shutdown detected. Finishing processing..." << std::endl;
//                     // Continue processing remaining events for a bit
//                     auto shutdown_time = std::chrono::high_resolution_clock::now();
//                     int remaining_events = 0;
//                     while (data_handler.process_next() && remaining_events < 1000 &&
//                            std::chrono::high_resolution_clock::now() - shutdown_time < std::chrono::seconds(2)) {
//                         remaining_events++;
//                         events_processed++;
//                     }
//                     std::cout << "Processed " << remaining_events << " remaining events after Python shutdown." << std::endl;
//                     break;
//                 }
//                 last_python_check = now;
//             }
            
//             if (events_processed % 500 == 0) {
//                 auto elapsed = now - start_time;
//                 double elapsed_ms = std::chrono::duration<double, std::milli>(elapsed).count();
//                 double throughput = events_processed / (elapsed_ms / 1000.0);
                
//                 size_t new_signals = ml_signals_received - last_signals_received;
//                 size_t new_signals_used = ml_signals_processed_in_decisions - last_signals_used;
//                 last_signals_received = ml_signals_received;
//                 last_signals_used = ml_signals_processed_in_decisions;
                
//                 std::cout << "[" << events_processed << "] "
//                           << "Rate: " << static_cast<int>(throughput) << " ev/s | "
//                           << "Signals[Recv/Used]: " << ml_signals_received << "/" << ml_signals_processed_in_decisions 
//                           << " (++" << new_signals << "/+" << new_signals_used << ") | "
//                           << "Queue: " << signal_reader.queue_size() << " | "
//                           << "Pos: " << strategy->position() << " | "
//                           << "PnL: $" << strategy->pnl()
//                           << std::endl;
//             }
//         }
        
//         std::cout << "\nStopping signal reader thread..." << std::endl;
//         signal_reader.stop_reader();
        
//         std::cout << "\n" << std::string(70, '=') << std::endl;
//         std::cout << "DRAINING ALL REMAINING SIGNALS IN QUEUE" << std::endl;
//         std::cout << std::string(70, '=') << "\n" << std::endl;
        
//         int signals_drained = 0;
        
//         // Drain ALL remaining signals and print each one
//         MLSignal signal;
//         while (signal_reader.try_get_signal(signal)) {
//             std::string signal_type;
//             if (signal.signal > 0) {
//                 signal_type = "BUY";
//                 ml_signals_buy++;
//             } else if (signal.signal < 0) {
//                 signal_type = "SELL";
//                 ml_signals_sell++;
//             } else {
//                 signal_type = "NEUTRAL";
//                 ml_signals_neutral++;
//             }
            
//             ml_signals_received++;
//             ml_signals_processed_in_decisions++;
//             signals_drained++;
            
//             // Print each signal
//             std::cout << "[" << signals_drained << "] " 
//                       << signal_type << " | Confidence: " 
//                       << std::fixed << std::setprecision(4) << signal.confidence
//                       << " | Queue remaining: " << signal_reader.queue_size()
//                       << std::endl;
//         }
        
//         std::cout << "\n" << std::string(70, '=') << std::endl;
//         std::cout << "QUEUE DRAIN COMPLETE" << std::endl;
//         std::cout << std::string(70, '=') << std::endl;
//         std::cout << "Total signals drained: " << signals_drained << std::endl;
//         std::cout << "  BUY: " << ml_signals_buy << std::endl;
//         std::cout << "  SELL: " << ml_signals_sell << std::endl;
//         std::cout << "  NEUTRAL: " << ml_signals_neutral << std::endl;
//         std::cout << std::string(70, '=') << "\n" << std::endl;
        
//         auto elapsed = std::chrono::high_resolution_clock::now() - start_time;
//         double elapsed_sec = std::chrono::duration<double>(elapsed).count();
        
//         std::cout << "\n" << std::string(70, '=') << std::endl;
//         std::cout << "BACKTEST COMPLETE" << std::endl;
//         std::cout << std::string(70, '=') << "\n" << std::endl;
        
//         std::cout << "Events Processed: " << events_processed << std::endl;
//         std::cout << "  Trades: " << data_handler.trades_processed() << std::endl;
//         std::cout << "  Quotes: " << data_handler.quotes_processed() << std::endl;
//         std::cout << "Execution Time: " << elapsed_sec << " seconds" << std::endl;
//         std::cout << "Throughput: " << static_cast<int>(events_processed / elapsed_sec) << " events/sec" << std::endl;
        
//         std::cout << "\nML Signal Statistics:" << std::endl;
//         std::cout << "  Total Received: " << ml_signals_received << std::endl;
//         std::cout << "  Total Used in Decisions: " << ml_signals_processed_in_decisions << std::endl;
//         std::cout << "  Buffered (reader): " << signal_reader.signals_seen() << std::endl;
//         if (ml_signals_received > 0) {
//             std::cout << "  BUY: " << ml_signals_buy 
//                       << " (" << (100.0 * ml_signals_buy / ml_signals_received) << "%)" << std::endl;
//             std::cout << "  SELL: " << ml_signals_sell 
//                       << " (" << (100.0 * ml_signals_sell / ml_signals_received) << "%)" << std::endl;
//             std::cout << "  NEUTRAL: " << ml_signals_neutral 
//                       << " (" << (100.0 * ml_signals_neutral / ml_signals_received) << "%)" << std::endl;
//         }
        
//         signal_reader.print_debug_info();
        
//         std::cout << "\n✓ [CONNECTION] Strategy was actively using ML signals!" << std::endl;
        
//         std::cout << "\nStrategy Performance:" << std::endl;
//         std::cout << "  Final Position: " << strategy->position() << std::endl;
//         std::cout << "  Total PnL: $" << strategy->pnl() << std::endl;
//         std::cout << "  Realized PnL: $" << strategy->realized_pnl() << std::endl;
        
//         std::cout << "\nResults: " << results_file << std::endl;
        
//         connection.announce_cpp_shutdown();
        
//         std::cout << "\n✓ Exiting cleanly." << std::endl;
//         std::cout.flush();
        
//         // Force exit to prevent any hanging threads
//         std::exit(0);
        
//     } catch (const std::exception& e) {
//         std::cerr << "\n✗ Error: " << e.what() << std::endl;
//         return 1;
//     }
// }


// main_improved.cpp
// Enhanced trading engine with proper signal synchronization and IPC handshake
// FIXED: Uses content-based deduplication to prevent re-reading signals

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
#include <queue>
#include <mutex>
#include <atomic>
#include <unordered_set>
#include <functional>
#include <iomanip>

using namespace trading;

volatile sig_atomic_t running = 1;

size_t ml_signals_received = 0;
size_t ml_signals_buy = 0;
size_t ml_signals_sell = 0;
size_t ml_signals_neutral = 0;
size_t ml_signals_processed_in_decisions = 0;

void signal_handler(int signal) {
    std::cout << "\nShutting down gracefully..." << std::endl;
    running = 0;
}

class BufferedSignalReader {
public:
    BufferedSignalReader(const std::string& signal_file, size_t buffer_size = 1000) 
        : signal_file_(signal_file), 
          buffer_size_(buffer_size),
          read_errors_(0),
          signals_seen_(0),
          signals_used_in_strategy_(0) {
        start_reader_thread();
    }
    
    ~BufferedSignalReader() {
        should_exit_ = true;
        if (reader_thread_.joinable()) {
            reader_thread_.join();
        }
    }
    
    bool try_get_signal(MLSignal& signal) {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        if (!signal_queue_.empty()) {
            signal = signal_queue_.front();
            signal_queue_.pop();
            signals_used_in_strategy_++;
            return true;
        }
        return false;
    }
    
    size_t queue_size() const {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        return signal_queue_.size();
    }
    
    size_t get_read_errors() const {
        return read_errors_;
    }
    
    size_t signals_seen() const {
        return signals_seen_;
    }
    
    size_t signals_used() const {
        return signals_used_in_strategy_;
    }
    
    void stop_reader() {
        should_exit_ = true;
        if (reader_thread_.joinable()) {
            reader_thread_.join();
        }
        std::cout << "[SIGNAL READER] Background thread stopped" << std::endl;
    }
    
    void print_debug_info() const {
        std::cout << "[SIGNAL READER DEBUG]" << std::endl;
        std::cout << "  Queue size: " << queue_size() << std::endl;
        std::cout << "  Signals seen (unique): " << signals_seen_ << std::endl;
        std::cout << "  Signals used: " << signals_used_in_strategy_ << std::endl;
        std::cout << "  Read errors: " << read_errors_ << std::endl;
        std::cout << "  Duplicate signals skipped: " << duplicates_skipped_ << std::endl;
    }
    
private:
    void start_reader_thread() {
        reader_thread_ = std::thread([this]() {
            while (!should_exit_) {
                try_fill_buffer();
                std::this_thread::sleep_for(std::chrono::milliseconds(5));
            }
        });
    }
    
    std::string hash_signal(int sig, double conf) {
        // Create a simple hash of the signal to detect duplicates
        std::stringstream ss;
        ss << sig << ":" << std::fixed << std::setprecision(6) << conf;
        return ss.str();
    }
    
    void try_fill_buffer() {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        
        if (signal_queue_.size() >= buffer_size_) {
            return;
        }
        
        std::ifstream file(signal_file_);
        if (!file.is_open()) {
            return;
        }
        
        std::string line;
        int signals_read = 0;
        
        while (std::getline(file, line) && signals_read < 200) {
            if (line.empty() || line.find("signal,confidence") != std::string::npos) {
                continue;
            }
            
            size_t comma_pos = line.find(',');
            if (comma_pos == std::string::npos) {
                read_errors_++;
                continue;
            }
            
            try {
                std::string signal_str = line.substr(0, comma_pos);
                std::string conf_str = line.substr(comma_pos + 1);
                
                signal_str.erase(0, signal_str.find_first_not_of(" \t\r\n"));
                signal_str.erase(signal_str.find_last_not_of(" \t\r\n") + 1);
                conf_str.erase(0, conf_str.find_first_not_of(" \t\r\n"));
                conf_str.erase(conf_str.find_last_not_of(" \t\r\n") + 1);
                
                int sig = std::stoi(signal_str);
                double conf = std::stod(conf_str);
                
                // Check if we've already seen this exact signal
                std::string sig_hash = hash_signal(sig, conf);
                if (seen_signals_.find(sig_hash) != seen_signals_.end()) {
                    duplicates_skipped_++;
                    continue;
                }
                
                // Mark as seen
                seen_signals_.insert(sig_hash);
                
                MLSignal signal;
                signal.signal = sig;
                signal.confidence = conf;
                signal.timestamp = std::chrono::duration_cast<std::chrono::nanoseconds>(
                    std::chrono::system_clock::now().time_since_epoch()
                ).count();
                
                signal_queue_.push(signal);
                signals_read++;
                signals_seen_++;
                
            } catch (const std::exception& e) {
                read_errors_++;
                std::cerr << "Parse error at line: " << line << " - " << e.what() << std::endl;
            }
        }
    }
    
    std::string signal_file_;
    size_t buffer_size_;
    std::atomic<bool> should_exit_{false};
    std::atomic<size_t> read_errors_{0};
    std::atomic<size_t> signals_seen_{0};
    std::atomic<size_t> signals_used_in_strategy_{0};
    std::atomic<size_t> duplicates_skipped_{0};
    
    std::queue<MLSignal> signal_queue_;
    std::unordered_set<std::string> seen_signals_;  // Track which signals we've already read
    mutable std::mutex queue_mutex_;
    std::thread reader_thread_;
};

class ConnectionMonitor {
public:
    ConnectionMonitor(const std::string& cpp_file, const std::string& python_file)
        : cpp_status_file_(cpp_file), python_status_file_(python_file) {}
    
    void announce_cpp_ready() {
        write_status_file(cpp_status_file_, "CPP_READY");
        std::cout << "\n[CONNECTION] C++ Engine: READY (wrote status file)" << std::endl;
    }
    
    void announce_cpp_processing() {
        write_status_file(cpp_status_file_, "CPP_PROCESSING");
    }
    
    void announce_cpp_shutdown() {
        write_status_file(cpp_status_file_, "CPP_SHUTDOWN");
        std::cout << "\n[CONNECTION] C++ Engine: SHUTDOWN (status updated)" << std::endl;
    }
    
    bool is_python_running() {
        std::string status = read_status_file(python_status_file_);
        return status == "PYTHON_RUNNING" || status == "PYTHON_SENDING";
    }
    
    bool is_python_sending_signals() {
        return read_status_file(python_status_file_) == "PYTHON_SENDING";
    }
    
    bool is_python_shutdown() {
        return read_status_file(python_status_file_) == "PYTHON_SHUTDOWN";
    }
    
private:
    void write_status_file(const std::string& file, const std::string& status) {
        std::ofstream f(file);
        if (f.is_open()) {
            f << status << std::endl;
            f.close();
        }
    }
    
    std::string read_status_file(const std::string& file) {
        std::ifstream f(file);
        if (f.is_open()) {
            std::string status;
            std::getline(f, status);
            f.close();
            return status;
        }
        return "";
    }
    
    std::string cpp_status_file_;
    std::string python_status_file_;
};

class ResultsLogger {
public:
    ResultsLogger(const std::string& output_file) {
        file_.open(output_file);
        if (!file_.is_open()) {
            throw std::runtime_error("Failed to open results file: " + output_file);
        }
        
        file_ << "timestamp,event_type,side,price,quantity,position,pnl,realized_pnl,fill_price,ml_signal_used" << std::endl;
    }
    
    ~ResultsLogger() {
        if (file_.is_open()) {
            file_.close();
        }
    }
    
    void log_fill(const Fill& fill, double position, double pnl, double realized_pnl, bool signal_used) {
        file_ << fill.timestamp << ","
              << "FILL" << ","
              << side_to_string(fill.side) << ","
              << price_to_double(fill.price) << ","
              << fill.quantity << ","
              << position << ","
              << pnl << ","
              << realized_pnl << ","
              << price_to_double(fill.price) << ","
              << (signal_used ? "1" : "0")
              << std::endl;
    }
    
    void log_quote(const Quote& quote, double position, double pnl, bool signal_used) {
        file_ << quote.timestamp << ","
              << "QUOTE" << ","
              << "NA" << ","
              << price_to_double(quote.mid_price()) << ","
              << "0" << ","
              << position << ","
              << pnl << ","
              << "0" << ","
              << "NA" << ","
              << (signal_used ? "1" : "0")
              << std::endl;
    }
    
private:
    std::ofstream file_;
};

int main(int argc, char* argv[]) {
    std::signal(SIGINT, signal_handler);
    
    std::cout << "======================================" << std::endl;
    std::cout << "Low-Latency Trading Engine (FIXED v2)" << std::endl;
    std::cout << "======================================" << std::endl;
    
    try {
        std::string trades_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/data/raw/trades.csv";
        std::string quotes_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/data/raw/quotes.csv";
        std::string signal_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/ipc/ml_signals.txt";
        std::string results_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/results/backtest_results.csv";
        std::string cpp_status_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/ipc/cpp_status.txt";
        std::string python_status_file = "/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/ipc/python_status.txt";
        
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
        
        BufferedSignalReader signal_reader(signal_file, 10000);
        std::cout << "✓ Buffered signal reader initialized (buffer: 10000)" << std::endl;
        
        ConnectionMonitor connection(cpp_status_file, python_status_file);
        std::cout << "✓ Connection monitor initialized" << std::endl;
        
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
            logger.log_fill(fill, strategy->position(), strategy->pnl(), strategy->realized_pnl(), false);
        });
        
        data_handler.on_quote([&strategy, &signal_reader, &logger, &exchange](const Quote& quote) {
            strategy->on_quote(quote);
            exchange->on_quote(quote);
            
            bool signal_used = false;
            MLSignal signal;
            while (signal_reader.try_get_signal(signal)) {
                ml_signals_received++;
                ml_signals_processed_in_decisions++;
                
                if (signal.signal > 0) ml_signals_buy++;
                else if (signal.signal < 0) ml_signals_sell++;
                else ml_signals_neutral++;
                
                strategy->on_ml_signal(signal);
                signal_used = true;
            }
            
            logger.log_quote(quote, strategy->position(), strategy->pnl(), signal_used);
        });
        
        data_handler.on_trade([&strategy, &exchange](const Trade& trade) {
            strategy->on_trade(trade);
            exchange->on_trade(trade);
        });
        
        std::cout << "✓ All callbacks wired" << std::endl;
        
        connection.announce_cpp_ready();
        
        std::cout << "\n" << std::string(70, '=') << std::endl;
        std::cout << "WAITING FOR PYTHON SIGNAL GENERATOR CONNECTION..." << std::endl;
        std::cout << std::string(70, '=') << std::endl;
        std::cout << "\nIn another terminal, run:" << std::endl;
        std::cout << "  python3 python/ml/signal_generator_simple.py" << std::endl;
        std::cout << "\n" << std::string(70, '=') << "\n" << std::endl;
        
        auto start_wait = std::chrono::high_resolution_clock::now();
        bool python_detected = false;
        int wait_count = 0;
        
        while (!python_detected && std::chrono::high_resolution_clock::now() - start_wait < std::chrono::seconds(60)) {
            if (connection.is_python_running()) {
                python_detected = true;
                std::cout << "✓ [CONNECTION] Python process detected! Connection established.\n" << std::endl;
                break;
            }
            
            wait_count++;
            if (wait_count % 4 == 0) {
                std::cout << "  Waiting for Python... (" << (wait_count / 2) << "s)" << std::endl;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }
        
        if (!python_detected) {
            std::cerr << "\n✗ TIMEOUT: Python process not detected after 60 seconds." << std::endl;
            std::cerr << "  Please start Python in another terminal:" << std::endl;
            std::cerr << "    python3 python/ml/signal_generator_simple.py" << std::endl;
            connection.announce_cpp_shutdown();
            return 1;
        }
        
        std::cout << "Waiting for Python to start sending signals...\n" << std::endl;
        int signal_wait = 0;
        while (!connection.is_python_sending_signals() && signal_wait < 30) {
            std::cout << "  Waiting... (" << signal_wait << "s)" << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(1));
            signal_wait++;
        }
        
        if (connection.is_python_sending_signals()) {
            std::cout << "✓ [CONNECTION] Python started sending signals!\n" << std::endl;
        }
        
        std::cout << "\n" << std::string(70, '=') << std::endl;
        std::cout << "STARTING TRADING ENGINE - MONITORING ML SIGNAL DECISIONS" << std::endl;
        std::cout << std::string(70, '=') << "\n" << std::endl;
        
        size_t events_processed = 0;
        auto start_time = std::chrono::high_resolution_clock::now();
        size_t last_signals_received = 0;
        size_t last_signals_used = 0;
        auto last_python_check = start_time;
        
        // Main processing loop
        while (running && data_handler.process_next()) {
            events_processed++;
            connection.announce_cpp_processing();
            
            // Check if Python has shutdown every second
            auto now = std::chrono::high_resolution_clock::now();
            if (now - last_python_check > std::chrono::seconds(1)) {
                if (connection.is_python_shutdown()) {
                    std::cout << "\n[CONNECTION] Python shutdown detected. Finishing processing..." << std::endl;
                    // Continue processing remaining events for a bit
                    auto shutdown_time = std::chrono::high_resolution_clock::now();
                    int remaining_events = 0;
                    while (data_handler.process_next() && remaining_events < 1000 &&
                           std::chrono::high_resolution_clock::now() - shutdown_time < std::chrono::seconds(2)) {
                        remaining_events++;
                        events_processed++;
                    }
                    std::cout << "Processed " << remaining_events << " remaining events after Python shutdown." << std::endl;
                    break;
                }
                last_python_check = now;
            }
            
            if (events_processed % 500 == 0) {
                auto elapsed = now - start_time;
                double elapsed_ms = std::chrono::duration<double, std::milli>(elapsed).count();
                double throughput = events_processed / (elapsed_ms / 1000.0);
                
                size_t new_signals = ml_signals_received - last_signals_received;
                size_t new_signals_used = ml_signals_processed_in_decisions - last_signals_used;
                last_signals_received = ml_signals_received;
                last_signals_used = ml_signals_processed_in_decisions;
                
                std::cout << "[" << events_processed << "] "
                          << "Rate: " << static_cast<int>(throughput) << " ev/s | "
                          << "Signals[Recv/Used]: " << ml_signals_received << "/" << ml_signals_processed_in_decisions 
                          << " (++" << new_signals << "/+" << new_signals_used << ") | "
                          << "Queue: " << signal_reader.queue_size() << " | "
                          << "Pos: " << strategy->position() << " | "
                          << "PnL: $" << strategy->pnl()
                          << std::endl;
            }
        }
        
        std::cout << "\nStopping signal reader thread..." << std::endl;
        signal_reader.stop_reader();
        
        std::cout << "\n" << std::string(70, '=') << std::endl;
        std::cout << "DRAINING ALL REMAINING SIGNALS IN QUEUE" << std::endl;
        std::cout << std::string(70, '=') << "\n" << std::endl;
        
        int signals_drained = 0;
        MLSignal signal;
        
        // First, count total signals in queue
        std::vector<MLSignal> temp_signals;
        while (signal_reader.try_get_signal(signal)) {
            temp_signals.push_back(signal);
        }
        
        int total_in_queue = temp_signals.size();
        std::cout << "Total signals in queue: " << total_in_queue << "\n" << std::endl;
        
        // Now process them
        for (const auto& sig : temp_signals) {
            std::string signal_type;
            if (sig.signal > 0) {
                signal_type = "BUY";
                ml_signals_buy++;
            } else if (sig.signal < 0) {
                signal_type = "SELL";
                ml_signals_sell++;
            } else {
                signal_type = "NEUTRAL";
                ml_signals_neutral++;
            }
            
            ml_signals_received++;
            ml_signals_processed_in_decisions++;
            signals_drained++;
            
            int remaining = total_in_queue - signals_drained;
            
            // Print each signal
            std::cout << "[" << std::setw(6) << signals_drained << "/" << total_in_queue << "] " 
                      << std::setw(7) << signal_type 
                      << " | Conf: " << std::fixed << std::setprecision(4) << sig.confidence
                      << " | Remaining: " << std::setw(6) << remaining
                      << std::endl;
        }
        
        std::cout << "\n" << std::string(70, '=') << std::endl;
        std::cout << "QUEUE DRAIN COMPLETE" << std::endl;
        std::cout << std::string(70, '=') << std::endl;
        std::cout << "Total signals drained: " << signals_drained << std::endl;
        std::cout << "  BUY: " << ml_signals_buy << std::endl;
        std::cout << "  SELL: " << ml_signals_sell << std::endl;
        std::cout << "  NEUTRAL: " << ml_signals_neutral << std::endl;
        std::cout << std::string(70, '=') << "\n" << std::endl;
        
        auto elapsed = std::chrono::high_resolution_clock::now() - start_time;
        double elapsed_sec = std::chrono::duration<double>(elapsed).count();
        
        std::cout << "\n" << std::string(70, '=') << std::endl;
        std::cout << "BACKTEST COMPLETE" << std::endl;
        std::cout << std::string(70, '=') << "\n" << std::endl;
        
        std::cout << "Events Processed: " << events_processed << std::endl;
        std::cout << "  Trades: " << data_handler.trades_processed() << std::endl;
        std::cout << "  Quotes: " << data_handler.quotes_processed() << std::endl;
        std::cout << "Execution Time: " << elapsed_sec << " seconds" << std::endl;
        std::cout << "Throughput: " << static_cast<int>(events_processed / elapsed_sec) << " events/sec" << std::endl;
        
        std::cout << "\nML Signal Statistics:" << std::endl;
        std::cout << "  Total Received: " << ml_signals_received << std::endl;
        std::cout << "  Total Used in Decisions: " << ml_signals_processed_in_decisions << std::endl;
        std::cout << "  Buffered (reader): " << signal_reader.signals_seen() << std::endl;
        if (ml_signals_received > 0) {
            std::cout << "  BUY: " << ml_signals_buy 
                      << " (" << (100.0 * ml_signals_buy / ml_signals_received) << "%)" << std::endl;
            std::cout << "  SELL: " << ml_signals_sell 
                      << " (" << (100.0 * ml_signals_sell / ml_signals_received) << "%)" << std::endl;
            std::cout << "  NEUTRAL: " << ml_signals_neutral 
                      << " (" << (100.0 * ml_signals_neutral / ml_signals_received) << "%)" << std::endl;
        }
        
        signal_reader.print_debug_info();
        
        std::cout << "\n✓ [CONNECTION] Strategy was actively using ML signals!" << std::endl;
        
        std::cout << "\nStrategy Performance:" << std::endl;
        std::cout << "  Final Position: " << strategy->position() << std::endl;
        std::cout << "  Total PnL: $" << strategy->pnl() << std::endl;
        std::cout << "  Realized PnL: $" << strategy->realized_pnl() << std::endl;
        
        std::cout << "\nResults: " << results_file << std::endl;
        
        connection.announce_cpp_shutdown();
        
        std::cout << "\n✓ Exiting cleanly." << std::endl;
        std::cout.flush();
        
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "\n✗ Error: " << e.what() << std::endl;
        return 1;
    }
}