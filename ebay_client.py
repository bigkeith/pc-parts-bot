"""
ebay_client.py
Handles talking to eBay's Browse API: getting an OAuth token and
searching for listings.
"""

import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")

# eBay's OAuth and search endpoints (Production, not Sandbox)
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

# We keep the token in memory so we don't fetch a new one on every
# single search - eBay tokens are valid for ~2 hours.
_cached_token = None


def get_access_token():
    """
    Get an OAuth token from eBay using our Client ID and Secret.
    This is required before we can call the search API.
    """
    global _cached_token
    if _cached_token:
        return _cached_token

    # eBay wants the Client ID and Secret combined and base64-encoded
    # for this request - this is standard OAuth "client credentials" flow
    credentials = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}",
    }
    data = {
        "grant_type": "client_credentials",
        # This "scope" tells eBay we only want read access to public listings
        "scope": "https://api.ebay.com/oauth/api_scope",
    }

    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()  # raises an error if the request failed

    token_data = response.json()
    _cached_token = token_data["access_token"]
    return _cached_token


# Titles containing any of these words (case-insensitive) get filtered
# out by default - these are the words that show up on accessories,
# empty boxes, and non-working "for parts" listings rather than an
# actual complete, working product.
DEFAULT_EXCLUDE_KEYWORDS = [
    "for parts", "not working", "no core", "no vram", "box only",
    "empty box", "bracket", "backplate", "shroud", "adapter",
    "cable", "holder", "stabilizer", "bundle", "read read",
    "defective", "as-is", "as is", "4gb",
]


def _title_is_clean(title, exclude_keywords):
    """Return True if the title does NOT contain any excluded word."""
    lowered = title.lower()
    return not any(bad_word in lowered for bad_word in exclude_keywords)


def search_ebay(query, max_price, category_id=None, limit=20,
                 exclude_keywords=None):
    """
    Search eBay for a product under a given price.

    category_id (optional) restricts results to a specific eBay
    category - this is the key to filtering out junk like brackets,
    fans, and water blocks that just happen to mention your search
    term in the title. Some useful ones:
        27386  = Graphics/Video Cards
        177808 = Bicycle Brakes
    You can find others by browsing eBay and checking the URL - the
    category ID is the number right before "bn_" in the URL.

    exclude_keywords (optional) is a list of words/phrases - any
    listing whose title contains one of these (case-insensitive) gets
    dropped from the results. If not provided, DEFAULT_EXCLUDE_KEYWORDS
    is used, which filters out common junk like "for parts", "box
    only", "no core", brackets, backplates, etc. Pass an empty list
    ([]) if you want no filtering at all.

    Returns a list of dictionaries shaped like:
        {
            "item_id": "...",
            "title": "...",
            "price": 123.45,
            "url": "...",
        }
    """
    if exclude_keywords is None:
        exclude_keywords = DEFAULT_EXCLUDE_KEYWORDS

    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        # Ship-to location affects what's shown as available - US here
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
    }

    # Build the filter string piece by piece - price is always included,
    # category only gets added if one was provided
    filter_parts = [f"price:[..{max_price}]", "priceCurrency:USD"]

    params = {
        "q": query,
        "filter": ",".join(filter_parts),
        "limit": limit,
    }

    # category_id is its own separate parameter, not part of "filter"
    if category_id:
        params["category_ids"] = str(category_id)

    response = requests.get(SEARCH_URL, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    results = []

    # itemSummaries might be missing entirely if there are zero matches
    for item in data.get("itemSummaries", []):
        title = item["title"]

        # Skip anything that looks like junk based on its title
        if not _title_is_clean(title, exclude_keywords):
            continue

        results.append({
            "item_id": item["itemId"],
            "title": title,
            "price": float(item["price"]["value"]),
            "url": item["itemWebUrl"],
        })

    return results


if __name__ == "__main__":
    # Quick manual test - RTX 4070 restricted to the Graphics/Video
    # Cards category, with the default junk-title filter applied
    test_results = search_ebay("RTX 4070", 300.00, category_id=27386)
    print(f"Found {len(test_results)} results:\n")
    for r in test_results:
        print(f"  {r['title']} - ${r['price']} - {r['url']}")