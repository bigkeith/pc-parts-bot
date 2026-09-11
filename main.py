"""
main.py
The main entry point for the PC Parts Price Bot.

This script:
  1. Searches eBay for each product you're tracking, using the real
     eBay Browse API (via ebay_client.py)
  2. Filters out junk listings (accessories, "for parts", wrong specs)
  3. Checks each result against your target price
  4. If it's a new listing under your target price, saves it to the
     database and emails you an alert

Run this file directly to do one "pass" - later we'll add scheduling
so it runs automatically every so often.
"""

from database import init_db, is_new_listing, save_listing
from notifier import send_email_alert
from ebay_client import search_ebay

# -----------------------------------------------------------------
# SEARCH CONFIG
# -----------------------------------------------------------------
# Add one dictionary per product you want to track.
# - "query": the search term to send to eBay
# - "max_price": the highest price (in USD) you're willing to pay
# - "category_id": (optional) restricts results to a specific eBay
#   category - this is what keeps accessories/parts out of your
#   results. Common ones:
#     27386  = Graphics/Video Cards
#     177808 = Bicycle Brakes
#   Leave it out (or set to None) to search all categories.
TRACKED_PRODUCTS = [
    {
        "query": "RX 580 8GB",
        "max_price": 80.00,
        "category_id": 27386,  # Graphics/Video Cards
    },
    {
        "query": "shimano xt 4 piston brake",
        "max_price": 280.00,
        "category_id": 177808,  # Bicycle Brakes
    },
]


def run_search_pass():
    """
    Runs one full pass: search every tracked product, check for new
    listings under the target price, alert on anything new.
    """
    for product in TRACKED_PRODUCTS:
        query = product["query"]
        max_price = product["max_price"]
        category_id = product.get("category_id")  # None if not set

        print(f"\nSearching for: {query} (under ${max_price})")

        # search_ebay already applies category filtering and the
        # default junk-title exclusion (see ebay_client.py) before
        # returning results, so what comes back here should already
        # be clean, real listings under budget
        results = search_ebay(query, max_price, category_id=category_id)

        for item in results:
            # Skip anything over budget, just in case
            if item["price"] > max_price:
                continue

            # Skip listings we've already alerted on before
            if not is_new_listing(item["item_id"]):
                continue

            # New match under budget - alert and remember it
            print(f"NEW MATCH: {item['title']} - ${item['price']}")

            send_email_alert(
                subject=f"Price Alert: {item['title']} - ${item['price']}",
                body=(
                    f"Found a match for '{query}'!\n\n"
                    f"Title: {item['title']}\n"
                    f"Price: ${item['price']}\n"
                    f"Link: {item['url']}\n"
                ),
                to_address=["ksavage31@gmail.com", "brandij.love8@gmail.com"],
            )

            save_listing(
                item_id=item["item_id"],
                title=item["title"],
                price=item["price"],
                url=item["url"],
            )


if __name__ == "__main__":
    # Make sure the database exists before we start
    init_db()

    # Do one search pass right now
    run_search_pass()

    print("\nDone with this pass.")