cmake_minimum_required(VERSION 3.15)
project(TradingEngine CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=native -Wall -Wextra")

# Include FetchContent module
include(FetchContent)

# Find required packages
find_package(Boost REQUIRED COMPONENTS system filesystem)

# --- Add this block to fetch spdlog ---
FetchContent_Declare(
  spdlog
  GIT_REPOSITORY https://github.com/gabime/spdlog.git
  GIT_TAG        v1.14.1 # Or another recent version
)
FetchContent_MakeAvailable(spdlog)
# ------------------------------------

# find_package(spdlog REQUIRED) # This line is no longer needed

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${Boost_INCLUDE_DIRS}
)

# Source files
set(SOURCES
    src/market_data.cpp
    src/order_book.cpp
    src/strategy.cpp
    src/simulated_exchange.cpp
    src/signal_reader.cpp
    src/main.cpp
)

# Executable
add_executable(trading_engine ${SOURCES})

# Link libraries
target_link_libraries(trading_engine
    ${Boost_LIBRARIES}
    spdlog::spdlog # This will now work
)

# Set output directory
set_target_properties(trading_engine PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
)