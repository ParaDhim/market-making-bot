// FILE 3: cpp/include/order_book.hpp
// ============================================================================
#ifndef ORDER_BOOK_HPP
#define ORDER_BOOK_HPP

#include "types.hpp"
#include <map>
#include <optional>

namespace trading {

class OrderBook {
public:
    OrderBook();
    
    void update(const Quote& quote);
    
    std::optional<Price> best_bid() const;
    std::optional<Price> best_ask() const;
    std::optional<Price> mid_price() const;
    
    Quantity bid_volume_at(Price price) const;
    Quantity ask_volume_at(Price price) const;
    
    Quantity total_bid_volume(size_t levels = 5) const;
    Quantity total_ask_volume(size_t levels = 5) const;
    
    double imbalance() const;
    void clear();
    
    size_t bid_levels() const { return bids_.size(); }
    size_t ask_levels() const { return asks_.size(); }
    
private:
    std::map<Price, Quantity, std::greater<Price>> bids_;
    std::map<Price, Quantity, std::less<Price>> asks_;
    
    mutable std::optional<Price> cached_best_bid_;
    mutable std::optional<Price> cached_best_ask_;
    mutable bool cache_valid_;
    
    void invalidate_cache();
};

} // namespace trading
#endif // ORDER_BOOK_HPP
