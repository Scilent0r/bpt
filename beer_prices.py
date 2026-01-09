import requests
import sqlite3
import hashlib
from datetime import datetime
import time
import json
from urllib.parse import quote

# --- Helper: generate a short hash ---
def generate_short_hash(date, name, price, length=8):
    input_str = f"{date}-{name}-{price}"
    full_hash = hashlib.sha256(input_str.encode()).hexdigest()
    return full_hash[:length]

# --- Connect to SQLite database ---
conn = sqlite3.connect('beerprices.db')
cursor = conn.cursor()

# --- Create table with hash column ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS prisma (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hash TEXT UNIQUE,
        date TEXT NOT NULL,
        name TEXT NOT NULL,
        price REAL NOT NULL
    )
''')
conn.commit()

# --- API call setup ---
current_date = datetime.now().strftime("%Y-%m-%d")
offset = 0
limit = 24  # Matches API
has_more_beers = True
base_url = "https://api.s-kaupat.fi/"

# Updated values from your new API URL (Jan 2026)
CURRENT_SHA256 = "ff102bea7318821d5d984b890d0a6322d2e3d9c01ba50e6eed6adb865c63efe1"
STORE_ID = "513971200"  # Critical - must match your store/region

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "fi-FI,fi;q=0.9,en;q=0.8",
    "Referer": "https://www.s-kaupat.fi/",
    "Origin": "https://www.s-kaupat.fi",
}

print(f"Starting API scrape ({current_date}) - Store ID: {STORE_ID}\n")

while has_more_beers:
    variables = {
        "facets": [
            {"key": "brandName", "order": "asc"},
            {"key": "labels"}
        ],
        "generatedSessionId": "0b5cd573-3cfe-4814-9a9f-ac33f5140c37",  # Can be dummy
        "fetchSponsoredContent": True,
        "includeAgeLimitedByAlcohol": True,
        "limit": limit,
        "queryString": "",
        "slug": "alkoholi-ja-virvoitusjuomat/oluet",
        "storeId": STORE_ID,
        "useRandomId": False,
        "marketingId": "e5b2ded0-b696-44f7-afdd-c5dc73ac20f4",
        "from": offset
    }

    extensions = {
        "persistedQuery": {
            "version": 1,
            "sha256Hash": CURRENT_SHA256
        }
    }

    params = {
        'operationName': 'RemoteFilteredProducts',
        'variables': json.dumps(variables),
        'extensions': json.dumps(extensions)
    }

    # GET URL (original style)
    url = f"{base_url}?operationName={params['operationName']}&variables={quote(params['variables'])}&extensions={quote(params['extensions'])}"

    print(f"Fetching offset={offset} | URL: {url[:300]}...")

    time.sleep(1.5)  # Polite delay

    try:
        # First try GET
        response = requests.get(url, headers=HEADERS, timeout=12)

        # If fails with 405/400, try POST (uncomment if needed)
        # response = requests.post(base_url, json={"variables": variables, "extensions": extensions}, headers=HEADERS)

        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print("GraphQL Error:", json.dumps(data["errors"], indent=2))
            has_more_beers = False
            break

        products = data.get("data", {}).get("store", {}).get("products", {}).get("items", [])

        if not products:
            print("No more beers found.")
            has_more_beers = False
            break

        new_beers_count = 0
        for product in products:
            name = product.get("name")
            price = product.get("pricing", {}).get("currentPrice")

            if not name or price is None:
                continue

            short_hash = generate_short_hash(current_date, name, price)

            try:
                cursor.execute('''
                    INSERT INTO prisma (hash, date, name, price)
                    VALUES (?, ?, ?, ?)
                ''', (short_hash, current_date, name, price))
                new_beers_count += 1
                print(f"Inserted: {name} - {price} €")
            except sqlite3.IntegrityError:
                print(f"Skipped (duplicate): {name} - {price} €")

        conn.commit()
        print(f"Added {new_beers_count} new beers this batch\n")

        offset += limit

    except Exception as e:
        print(f"Error: {e}")
        print(f"Status: {response.status_code if 'response' in locals() else 'No response'}")
        print(f"Response snippet: {response.text[:500] if 'response' in locals() else 'No response'}")
        has_more_beers = False

conn.close()
print("Done. Total beers processed:", offset)
