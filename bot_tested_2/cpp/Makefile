# Makefile for Low-Latency Trading Engine

CXX = g++
CXXFLAGS = -std=c++17 -O3 -Wall -Wextra -Wpedantic -I./include
LDFLAGS = 

# Directories
SRC_DIR = src
INC_DIR = include
BUILD_DIR = build
BIN_DIR = .

# Source files
SOURCES = main.cpp \
          $(SRC_DIR)/market_data_handler.cpp \
          $(SRC_DIR)/order_book.cpp \
          $(SRC_DIR)/strategy.cpp \
          $(SRC_DIR)/execution_handler.cpp \
          $(SRC_DIR)/simulated_exchange.cpp

# Object files
OBJECTS = $(patsubst %.cpp,$(BUILD_DIR)/%.o,$(notdir $(SOURCES)))

# Target executable
TARGET = $(BIN_DIR)/main

# Default target
all: $(TARGET)

# Link object files to create executable
$(TARGET): $(OBJECTS) | $(BIN_DIR)
	$(CXX) $(OBJECTS) -o $@ $(LDFLAGS)
	@echo "Build complete: $(TARGET)"

# Compile main.cpp
$(BUILD_DIR)/main.o: main.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Compile source files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Create build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Create bin directory
$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) $(TARGET)
	@echo "Clean complete"

# Run the trading engine
run: $(TARGET)
	./$(TARGET)

# Debug build
debug: CXXFLAGS += -g -DDEBUG -O0
debug: clean $(TARGET)

# Check if all required files exist
check:
	@echo "Checking required files..."
	@for file in $(SOURCES); do \
		if [ ! -f $$file ]; then \
			echo "Missing: $$file"; \
		else \
			echo "Found: $$file"; \
		fi \
	done

.PHONY: all clean run debug check