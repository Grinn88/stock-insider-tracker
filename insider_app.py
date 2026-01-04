import streamlit as st
import pandas as pd
import time

# --- FINAL CONFIGURATION ---
USER = "Grinn88"
REPO = "stock-insider-tracker"
# Ensure this matches the EXACT filename your tracker script saves
FILENAME = "latest_trades.csv" 

RAW_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/{FILENAME}"

st.set_page_config(page_title="Eagle Eye Terminal", layout="wide")
st.title("🦅 Eagle Eye: Insider Terminal")

@st.cache_data(ttl=60)
def load_data():
    try:
        # The '?cache=' forces GitHub to give us the absolute latest version
        cache_buster_url = f"{RAW_URL}?cache={int(time.time())}"
        df = pd.read_csv(cache_buster_url)
        return df
    except Exception as e:
        return None

df = load_data()

if df is not None:
    st.success(f"✅ Connection Stable | {len(df)} Trades in Feed")
    
    # Simple Whale/Cluster Logic
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
    
    st.subheader("🔥 High-Conviction Dashboard")
    st.dataframe(df.sort_values(by="Value", ascending=False), use_container_width=True)
else:
    st.error("🚨 Data Link Broken")
    st.write(f"I am looking for your data at this link: `{RAW_URL}`")
    st.info("💡 **Final Fix:** Go to your GitHub Code tab. If you don't see 'latest_trades.csv' in the file list, your Action ran but failed to 'Push' the file. Check your 'Workflow Permissions' in Settings.")
