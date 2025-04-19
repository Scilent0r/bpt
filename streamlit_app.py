import os
import sqlite3
import pandas as pd
import requests
import streamlit as st
from datetime import datetime
import numpy as np

# Page config
st.set_page_config(page_title="🍺 Beer Prices", layout="wide")
st.title("🍺 Beer Prices Table")
st.caption("Latest data pulled from GitHub every time you load this app.")

# URL and path
db_url = "https://github.com/Scilent0r/bpt/raw/refs/heads/main/beerprices.db"
db_path = "./sqlite-tools/beerprices.db"

# Ensure directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Rename existing DB
if os.path.isfile(db_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path.rstrip('.db')}_{timestamp}.db"
    os.rename(db_path, backup_path)
    st.info(f"Old DB backed up as `{os.path.basename(backup_path)}`")

# Download DB
st.write("🔄 Downloading the latest Prisma beer prices database...")
response = requests.get(db_url)
if response.status_code == 200:
    with open(db_path, "wb") as f:
        f.write(response.content)
    st.success("✅ Database downloaded successfully.")
else:
    st.error(f"❌ Failed to download database. Status code: {response.status_code}")
    st.stop()

# Load data
conn = sqlite3.connect(db_path)
df = pd.read_sql_query("SELECT date, name, price FROM prisma", conn)
conn.close()

# Prepare dates
df['date'] = pd.to_datetime(df['date'])
latest_dates = sorted(df['date'].unique())[-4:]
df = df[df['date'].isin(latest_dates)]

# Pivot table
pivot = df.pivot_table(index="name", columns="date", values="price", aggfunc="first")
pivot.dropna(how='all', inplace=True)

# Filter to only changed or missing
def has_changes_or_missing(row):
    if row.isnull().any():
        return True
    return len(set(row.values)) > 1

filtered = pivot[pivot.apply(has_changes_or_missing, axis=1)]

# Show message if empty
if filtered.empty:
    st.success("✅ Ei muutoksia olut valikoimassa")
else:
    # Replace NaNs with "-"
    display_df = filtered.copy()
    display_df = display_df.applymap(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    display_df.insert(0, "name", display_df.index)

    # Define row-level highlight logic
    def highlight_rows(row):
        if "-" in row.values:
            return ['background-color: #ffcccc; color: red'] * len(row)
        elif len(set(v for v in row.values[1:] if v != "-")) > 1:
            return ['background-color: #fff3cd; color: black'] * len(row)
        else:
            return [''] * len(row)

    styled = display_df.style.apply(highlight_rows, axis=1)
    st.dataframe(styled, use_container_width=True)
