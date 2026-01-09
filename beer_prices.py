import requests
from bs4 import BeautifulSoup
import sqlite3
import hashlib
from datetime import datetime
import time
from urllib.parse import urljoin

# ================= CONFIG =================
BASE_URL = "https://www.s-kaupat.fi/tuotteet/alkoholi-ja-virvoitusjuomat/oluet"
DB_FILE = "beerprices.db"
CHAIN = "S-kaupat"  # optional, can be used later if you want

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fi-FI,fi;q=0.9,en;q=0.8",
    "Referer": "https://www.s-kaupat.fi/",
}

# Possible product card selectors – most likely one will work (Jan 2026)
CARD_SELECTORS = [
    "div[data-testid='product-card']",
    "article[class*='product']",
    "div[class*='ProductCard']",
    "div[class*='productCard']",
    ".product-item",
    "li[class*='product']",
]

# ================= HELPERS =================
def generate_short_hash(date, name, price, length=8):
    input_str = f"{date}-{name}-{price}"
    full_hash = hashlib.sha256(input_str.encode()).hexdigest()
    return full_hash[:length]


def parse_price(price_text: str) -> float | None:
    if not price_text:
        return None
    cleaned = price_text.replace("€", "").replace("EUR", "").replace(" ", "").strip()
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


# ================= DB =================
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

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

# ================= SCRAPING =================
current_date = datetime.now().strftime("%Y-%m-%d")
page = 1
total_inserted = 0
max_pages = 25  # safety limit

print(f"Starting scrape - {BASE_URL}  ({current_date})\n")

while page <= max_pages:
    url = BASE_URL if page == 1 else f"{BASE_URL}?page={page}"
    print(f"Page {page:2d} | {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Most reliable selector right now: articles with data-test-id="product-card"
        product_cards = soup.select('article[data-test-id="product-card"]')
        
        if not product_cards:
            print(" !!! No product cards found - site structure changed again !!!")
            print("First 2000 chars of response:\n", str(soup)[:2000])
            break

        print(f" → Found {len(product_cards)} product cards")

        new_beers_count = 0

        for card in product_cards:
            try:
                # Name: very reliable - span with title attribute inside the link
                name_span = card.select_one('span[title][class*="fdLJWj"]')  # or just 'span[title]'
                name = name_span.get_text(strip=True) if name_span else ""
                
                # Fallback: if title attr is missing, take from the link text
                if not name:
                    name_link = card.select_one('a.product-link')
                    name = name_link.get_text(strip=True) if name_link else ""
                
                if not name:
                    continue

                # Price: extremely stable attribute
                price_span = card.select_one('span[data-test-id="display-price"]')
                price_str = price_span.get_text(strip=True) if price_span else ""
                price = parse_price(price_str)
                
                if price is None:
                    continue

                short_hash = generate_short_hash(current_date, name, price)

                cursor.execute('''
                    INSERT INTO prisma (hash, date, name, price)
                    VALUES (?, ?, ?, ?)
                ''', (short_hash, current_date, name, price))

                new_beers_count += 1
                print(f" Inserted: {name} - {price} €")

            except sqlite3.IntegrityError:
                print(f" Skipped (duplicate): {name} - {price} €")
            except Exception as e:
                print(f" Item error: {e}")

        conn.commit()
        print(f" → Added {new_beers_count} new beers this page\n")

        if new_beers_count == 0 and page > 1:
            print(" No new items on page >1 → probably reached the end")
            break

        # Polite delay
        time.sleep(3.2)  # slightly randomized feel

        # Better last page detection (site shows "Sivu X / Y" or total products)
        page_info = soup.find(string=lambda t: t and ('Sivu ' in t or 'tuotetta' in t))
        if page_info and ' / ' in page_info:
            print(f" → Pagination info: {page_info.strip()}")
        
        # Optional: check for disabled next or no more links
        next_link = soup.select_one('a[href*="page="][aria-disabled="true"], button:disabled[class*="next"]')
        if next_link:
            print(" → Next button disabled → last page")
            break

        page += 1

    except Exception as e:
        print(f"Request/page error: {e}")
        break

conn.close()
print(f"\nDone! Total new beers this run: {total_inserted}")
print(f"Database: {DB_FILE}")

