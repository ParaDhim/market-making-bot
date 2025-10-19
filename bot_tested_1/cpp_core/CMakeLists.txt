cmake_minimum_required(VERSION 3.14)
project(HFTTrader)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Manual Boost Linking (Final Version) ---
# We now only look for the components that we know exist.

# 1. Find the Boost include directory
find_path(BOOST_INCLUDE_DIR
          NAMES boost/version.hpp
          HINTS /opt/homebrew/include)

# 2. Find the filesystem library
find_library(BOOST_FILESYSTEM_LIBRARY
             NAMES boost_filesystem
             HINTS /opt/homebrew/lib)

# Check if all parts were found
if(NOT BOOST_INCLUDE_DIR OR NOT BOOST_FILESYSTEM_LIBRARY)
    message(FATAL_ERROR "Could not find all required Boost components manually.")
endif()

# --- Build the Executable ---
add_executable(trader src/main.cpp)

# 3. Tell the executable where to find the headers
target_include_directories(trader PRIVATE ${BOOST_INCLUDE_DIR})

# 4. Link the executable against the libraries
target_link_libraries(trader PRIVATE ${BOOST_FILESYSTEM_LIBRARY})