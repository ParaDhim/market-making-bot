#include "signal_reader.hpp"
#include <iostream>

SignalReader::SignalReader(const std::string& signal_file)
    : current_signal_(0) {
    
    signal_stream_.open(signal_file);
    if (!signal_stream_.is_open()) {
        std::cerr << "Warning: Cannot open signal file: " << signal_file 
                  << ". Using neutral signals.\n";
    }
}

int SignalReader::get_current_signal() {
    return current_signal_;
}

bool SignalReader::update() {
    if (!signal_stream_.is_open() || signal_stream_.eof()) {
        return false;
    }
    
    std::string line;
    if (std::getline(signal_stream_, line)) {
        try {
            current_signal_ = std::stoi(line);
            // Clamp signal to valid range
            if (current_signal_ < -1) current_signal_ = -1;
            if (current_signal_ > 1) current_signal_ = 1;
            return true;
        } catch (...) {
            current_signal_ = 0;
        }
    }
    
    return false;
}