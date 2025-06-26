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
conn = sqlite3.connect('./sqlite-tools/beerprices.db')
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

# --- API call setup ---
current_date = datetime.now().strftime("%Y-%m-%d")
offset = 0
limit = 24  # Number of items to fetch per request
has_more_beers = True

base_url = "https://api.s-kaupat.fi/"

while has_more_beers:
    # Construct the parameters
    variables = {
        "includeStoreEdgePricing": True,
        "storeEdgeId": "726109200",
        "facets": [
            {"key": "brandName", "order": "asc"},
            {"key": "labels"}
        ],
        "generatedSessionId": "2381cfa6-4f1e-4f16-bc98-62a0e3b7fd47",
        "includeAgeLimitedByAlcohol": True,
        "limit": limit,
        "queryString": "",
        "slug": "alkoholi-ja-virvoitusjuomat/oluet",
        "storeId": "726109200",
        "useRandomId": False,
        "from": offset
    }
    
    extensions = {
        "persistedQuery": {
            "version": 1,
            "sha256Hash": "abbeaf3143217630082d1c0ba36033999b196679bff4b310a0418e290c141426"
        }
    }
    
    # Construct the query parameters
    params = {
        'operationName': 'RemoteFilteredProducts',
        'variables': json.dumps(variables),
        'extensions': json.dumps(extensions)
    }
    
    # Construct the URL
    url = f"{base_url}?operationName={params['operationName']}&variables={quote(params['variables'])}&extensions={quote(params['extensions'])}"
    
    print(f"Fetching: offset={offset}")
    print(f"URL: {url}")  # For debugging
    time.sleep(1)  # Be polite with the API
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        products = data["data"]["store"]["products"]["items"]
        
        if not products:
            has_more_beers = False
            print("No more beers found, ending collection.")
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
                print(f"Inserted: {name} - {price} EUR")
            except sqlite3.IntegrityError:
                print(f"Skipped (duplicate): {name} - {price} EUR")

        conn.commit()
        print(f"Added {new_beers_count} new beers from this batch")
        
        # Increment offset for next batch
        offset += limit
        
    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"Response content: {response.content if 'response' in locals() else 'No response'}")
        has_more_beers = False

conn.close()
print("Done. Total beers processed:", offset)
