#pragma once

#include <string>
#include <fstream>
#include <queue>

class SignalReader {
public:
    SignalReader(const std::string& signal_file);
    
    int get_current_signal();
    bool update();  // Read next signal if available
    
private:
    std::ifstream signal_stream_;
    int current_signal_;
    std::queue<int> signal_buffer_;
};