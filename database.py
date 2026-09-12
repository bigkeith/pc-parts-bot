"""
database.py
Handles storing and checking PC parts listings so we don't
send duplicate alerts for the same item.
"""

import os
import sqlite3

# DB_PATH can be overridden with an environment variable - this lets
# the Docker setup point it at a mounted volume (/app/data/listings.db)
# while local development just uses a file in the current folder.
DB_FILE = os.getenv("DB_PATH", "listings.db")


def init_db():
    """Create the listings table if it doesn't already exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            item_id TEXT PRIMARY KEY,
            title TEXT,
            price REAL,
            url TEXT,
            seen_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("Database ready.")


def is_new_listing(item_id):
    """Return True if we haven't seen this item_id before."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM listings WHERE item_id = ?", (item_id,))
    result = cursor.fetchone()
    conn.close()
    return result is None


def save_listing(item_id, title, price, url):
    """Save a new listing so we recognize it next time."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO listings (item_id, title, price, url) VALUES (?, ?, ?, ?)",
        (item_id, title, price, url)
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Running this file directly just sets up the database.
    init_db()