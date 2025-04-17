import requests
import sqlite3
import hashlib
from datetime import datetime
import time

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

# --- API call setup ---
arr = [24, 48, 72, 96, 120, 144, 168, 192, 216, 240, 264, 288, 312, 336, 360, 384, 408, 432]
current_date = datetime.now().strftime("%Y-%m-%d")


for val in arr: 
    
    #Ale
    #u1 = "https://api.s-kaupat.fi/?operationName=RemoteFilteredProducts&variables=%7B%22facets%22%3A%5B%7B%22key%22%3A%22brandName%22%2C%22order%22%3A%22asc%22%7D%2C%7B%22key%22%3A%22labels%22%7D%5D%2C%22generatedSessionId%22%3A%222381cfa6-4f1e-4f16-bc98-62a0e3b7fd47%22%2C%22includeAgeLimitedByAlcohol%22%3Atrue%2C%22limit%22%3A"
    #u2 = "%2C%22order%22%3A%22desc%22%2C%22orderBy%22%3A%22price%22%2C%22queryString%22%3A%22%22%2C%22slug%22%3A%22juomat-1%2Foluet%2Fale-olut%22%2C%22storeId%22%3A%22726109200%22%2C%22useRandomId%22%3Afalse%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%2229121c3595103a8c4ad58cc195a143f1c8c39789017a8165761d0b251d78da0e%22%7D%7D"
    
    #all
    u1 = "https://api.s-kaupat.fi/?operationName=RemoteFilteredProducts&variables=%7B%22facets%22%3A%5B%7B%22key%22%3A%22brandName%22%2C%22order%22%3A%22asc%22%7D%2C%7B%22key%22%3A%22labels%22%7D%5D%2C%22generatedSessionId%22%3A%222381cfa6-4f1e-4f16-bc98-62a0e3b7fd47%22%2C%22includeAgeLimitedByAlcohol%22%3Atrue%2C%22limit%22%3A24%2C%22queryString%22%3A%22%22%2C%22slug%22%3A%22juomat-1%2Foluet%22%2C%22storeId%22%3A%22726109200%22%2C%22useRandomId%22%3Afalse%2C%22from%22%3A"
    u2 = "%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%2229121c3595103a8c4ad58cc195a143f1c8c39789017a8165761d0b251d78da0e%22%7D%7D"
    
    url = u1 + str(val) + u2
    print(f"{val} - Fetching: {url}")
    time.sleep(1)
    
    response = requests.get(url)
    data = response.json()
    products = data["data"]["store"]["products"]["items"]

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
            print(f"Inserted: {name} - {price} EUR")
        except sqlite3.IntegrityError:
            print(f"Skipped (duplicate): {name} - {price} EUR")

        conn.commit()

conn.close()
print("Done.")