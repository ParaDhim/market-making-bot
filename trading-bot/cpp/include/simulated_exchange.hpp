#pragma once

#include "strategy.hpp"
#include "market_data.hpp"
#include <fstream>
#include <memory>

class SimulatedExchange {
public:
    SimulatedExchange(const std::string& results_file);
    ~SimulatedExchange();
    
    void process_trade(const Trade& trade, Strategy& strategy);
    void log_state(double timestamp, const Strategy& strategy, double current_price);
    
    int get_total_fills() const { return total_fills_; }
    
private:
    std::ofstream results_file_;
    int total_fills_;
};