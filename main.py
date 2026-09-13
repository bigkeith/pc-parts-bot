"""
main.py
The main entry point for the PC Parts Price Bot.

This script:
  1. Searches eBay for each product you're tracking, using the real
     eBay Browse API (via ebay_client.py)
  2. Filters out junk listings (accessories, "for parts", wrong specs)
  3. Checks each result against your target price
  4. If it's a new listing under your target price, saves it to the
     database
  5. Sends ONE digest email summarizing all new matches (if any)

Running this file starts a continuous loop: it does one search pass
immediately, then repeats automatically every CHECK_INTERVAL_MINUTES.
Leave it running in a terminal (or eventually, a Docker container) and
it'll keep checking on its own - no need to run it by hand each time.

Press Ctrl+C to stop it.
"""

import time
import schedule

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

# -----------------------------------------------------------------
# EMAIL RECIPIENTS
# -----------------------------------------------------------------
# Who should get the digest email. Leave as None to just send to
# yourself (the GMAIL_ADDRESS in your .env file), or add more emails
# as a list, e.g.:
#   ALERT_RECIPIENTS = ["you@gmail.com", "friend@example.com"]
ALERT_RECIPIENTS = ["ksavage31@gmail.com", "brandijlove8@gmail.com"]

# -----------------------------------------------------------------
# SCHEDULE
# -----------------------------------------------------------------
# How often (in minutes) to run a search pass automatically.
CHECK_INTERVAL_MINUTES = 31


def run_search_pass():
    """
    Runs one full pass: search every tracked product, check for new
    listings under the target price, and collect anything new.

    Instead of sending one email per match (which gets spammy fast),
    we collect all new matches from every product into one list, then
    send a single digest email at the end summarizing everything.
    """
    # Collects every new match across all tracked products, so we can
    # send ONE email at the end instead of one per listing
    new_matches = []

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

            # New match under budget - remember it for the digest,
            # and record which search query it matched (useful in
            # the email body since multiple products share one email)
            print(f"NEW MATCH: {item['title']} - ${item['price']}")
            new_matches.append({**item, "query": query})

            save_listing(
                item_id=item["item_id"],
                title=item["title"],
                price=item["price"],
                url=item["url"],
            )

    # Only send an email if we actually found something new - no
    # point emailing an empty "nothing found" digest every run
    if new_matches:
        send_digest_email(new_matches)
    else:
        print("\nNo new matches this pass - no email sent.")


def send_digest_email(matches):
    """
    Sends a single email summarizing every new match found in this
    pass, instead of one email per listing.
    """
    subject = f"Price Bot: {len(matches)} new match(es) found"

    # Build the email body by listing each match on its own block
    lines = [f"Found {len(matches)} new listing(s):\n"]
    for item in matches:
        lines.append(
            f"- {item['title']}\n"
            f"  Price: ${item['price']}\n"
            f"  Matched search: {item['query']}\n"
            f"  Link: {item['url']}\n"
        )
    body = "\n".join(lines)

    send_email_alert(subject=subject, body=body, to_address=ALERT_RECIPIENTS)


if __name__ == "__main__":
    # Make sure the database exists before we start
    init_db()

    # Do one search pass immediately on startup, rather than waiting
    # the full interval before the first check
    print("Running initial search pass...")
    run_search_pass()
    print("\nInitial pass done.")

    # Schedule run_search_pass() to repeat automatically going forward
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(run_search_pass)
    print(f"\nScheduled to check every {CHECK_INTERVAL_MINUTES} minutes. "
          f"Press Ctrl+C to stop.")

    # This loop just waits for scheduled jobs to become due and runs
    # them - it checks once per second, which is cheap and responsive
    # without hammering the CPU
    while True:
        schedule.run_pending()
        time.sleep(1)