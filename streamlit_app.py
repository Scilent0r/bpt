import os
import sqlite3
import pandas as pd
import streamlit as st
import requests
from datetime import datetime, timedelta

# Streamlit page config
st.set_page_config(page_title="Beer Prices", layout="wide")
st.title("🍺 Beer Prices Table")
st.caption("Latest data pulled from GitHub every time you load this app.")

# URL of the .db file on GitHub
db_url = "https://github.com/Scilent0r/bpt/raw/refs/heads/main/beerprices.db"
db_path = "./sqlite-tools/beerprices.db"

# Ensure folder exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Rename old DB
if os.path.isfile(db_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path.rstrip('.db')}_{timestamp}.db"
    os.rename(db_path, backup_path)
    st.info(f"Old database backed up as `{os.path.basename(backup_path)}`")

# Download new DB
st.write("🔄 Ladataan uusin tietokanta...")
response = requests.get(db_url)
if response.status_code == 200:
    with open(db_path, "wb") as f:
        f.write(response.content)
    st.success("✅ Tietokanta ladattu.")
else:
    st.error(f"❌ Ongelma kannan latauksessa. Status code: {response.status_code}")
    st.stop()

# Connect and load data
conn = sqlite3.connect(db_path)
df = pd.read_sql_query("SELECT date, name, price FROM prisma", conn)
conn.close()

# Convert date column to datetime
df['date'] = pd.to_datetime(df['date'])

# Filter last 4 days
latest_dates = sorted(df['date'].unique())[-4:]
df = df[df['date'].isin(latest_dates)]

# Pivot table
pivot = df.pivot_table(index="name", columns="date", values="price", aggfunc="first")

# Drop rows where all values are NaN
pivot.dropna(how='all', inplace=True)

# Identify rows with changes or missing values
def has_changes_or_missing(row):
    values = row.values
    if pd.isnull(values).any():
        return True
    return len(set(values)) > 1

filtered = pivot[pivot.apply(has_changes_or_missing, axis=1)]

# If no data to display
if filtered.empty:
    st.info("Ei muutoksia olut valikoimassa")
else:
    # Style rows
    def highlight_row(row):
        if row.isnull().any():
            return ['background-color: #ffcccc; color: red'] * len(row)
        elif len(set(row.values)) > 1:
            return ['background-color: #fff3cd'] * len(row)  # Yellow for change
        else:
            return [''] * len(row)

    styled_df = filtered.style.apply(highlight_row, axis=1).format("{:.2f}")
    st.dataframe(styled_df, use_container_width=True)