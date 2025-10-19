// FILE 2: cpp/include/market_data_handler.hpp
// ============================================================================
#ifndef MARKET_DATA_HANDLER_HPP
#define MARKET_DATA_HANDLER_HPP

#include "types.hpp"
#include <string>
#include <fstream>
#include <vector>
#include <functional>

namespace trading {

class MarketDataHandler {
public:
    using TradeCallback = std::function<void(const Trade&)>;
    using QuoteCallback = std::function<void(const Quote&)>;
    
    MarketDataHandler(const std::string& trades_file, const std::string& quotes_file);
    ~MarketDataHandler();
    
    void on_trade(TradeCallback callback);
    void on_quote(QuoteCallback callback);
    
    void start();
    bool process_next();
    
    size_t trades_processed() const { return trades_count_; }
    size_t quotes_processed() const { return quotes_count_; }
    
private:
    std::string trades_file_;
    std::string quotes_file_;
    
    std::ifstream trades_stream_;
    std::ifstream quotes_stream_;
    
    TradeCallback trade_callback_;
    QuoteCallback quote_callback_;
    
    size_t trades_count_;
    size_t quotes_count_;
    
    Trade next_trade_;
    Quote next_quote_;
    bool has_next_trade_;
    bool has_next_quote_;
    
    bool read_next_trade();
    bool read_next_quote();
    Trade parse_trade_line(const std::string& line);
    Quote parse_quote_line(const std::string& line);
    std::vector<std::string> split_csv(const std::string& line);
};

} // namespace trading
#endif // MARKET_DATA_HANDLER_HPP
