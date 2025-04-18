import os
import sqlite3
import pandas as pd
import streamlit as st
import requests
from datetime import datetime

# Streamlit page config
st.set_page_config(page_title="Beer Prices", layout="wide")
st.title("🍺 Beer Prices Table")
st.caption("Latest data pulled from GitHub every time you load this app.")

# URL of the .db file on GitHub
db_url = "https://github.com/Scilent0r/bpt/raw/refs/heads/main/beerprices.db"
db_path = "./sqlite-tools/beerprices.db"

# Create folder if it doesn't exist
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Rename old DB if it exists
if os.path.isfile(db_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path.rstrip('.db')}_{timestamp}.db"
    os.rename(db_path, backup_path)
    st.info(f"Old database backed up as `{os.path.basename(backup_path)}`")

# Download the new database
st.write("🔄 Downloading the latest database...")
response = requests.get(db_url)
if response.status_code == 200:
    with open(db_path, "wb") as f:
        f.write(response.content)
    st.success("✅ Database downloaded successfully.")
else:
    st.error(f"❌ Failed to download database. Status code: {response.status_code}")
    st.stop()

# Connect and load data
conn = sqlite3.connect(db_path)
df = pd.read_sql_query("SELECT date, name, price FROM prisma", conn)
conn.close()

# Pivot the DataFrame
pivot = df.pivot_table(index="name", columns="date", values="price", aggfunc="first")

# Display with optional missing data highlight
highlight_missing = st.checkbox("🔴 Highlight missing prices?", value=True)

def highlight_missing_vals(val):
    if pd.isna(val):
        return 'background-color: #ffcccc; color: red' if highlight_missing else ''
    else:
        return ''

styled_df = pivot.style.format("{:.2f}").applymap(highlight_missing_vals)

st.dataframe(styled_df, use_container_width=True)