import streamlit as st
import pandas as pd
import time

# --- CONFIGURATION ---
# These must match your GitHub account exactly
USER = "Grinn88"
REPO = "stock-insider-tracker"

# CORRECT RAW URL: Pointing to the data file, not the code file
RAW_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/latest_trades.csv"

st.set_page_config(page_title="Eagle Eye Dashboard", layout="wide")
st.title("🦅 Eagle Eye: Insider Terminal")

@st.cache_data(ttl=60)
def load_data():
    try:
        # The '?t=' forces a fresh download so you don't see old data
        pull_url = f"{RAW_URL}?t={int(time.time())}"
        df = pd.read_csv(pull_url)
        return df
    except Exception as e:
        return None

# --- DASHBOARD UI ---
df = load_data()

if df is not None:
    st.success("✅ Dashboard Connected to Live SEC Data")
    
    # Calculate Whale and Cluster Metrics
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
    whales = df[df['Value'] >= 250000]
    clusters = df.groupby('Ticker').filter(lambda x: len(x) >= 2)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Filings", len(df))
    c2.metric("Whales ($250k+)", len(whales))
    c3.metric("Clusters Detected", len(clusters['Ticker'].unique()))

    st.subheader("🔥 High-Conviction Activity")
    st.dataframe(df.sort_values(by="Value", ascending=False), use_container_width=True)
else:
    st.error("🚨 Data Link Broken")
    st.info(f"The dashboard is looking for the file `latest_trades.csv` at this link:\n\n`{RAW_URL}`")
    st.warning("If the link above leads to a '404: Not Found' page, your GitHub Action hasn't created the CSV file yet. Go to your GitHub Actions tab and click 'Run workflow'.")
