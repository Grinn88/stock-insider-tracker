import streamlit as st
import pandas as pd
import time

# --- CONFIGURATION ---
# We use the RAW URL to bypass the GitHub "webpage" and get just the data
URL = "https://raw.githubusercontent.com/Grinn88/stock-insider-tracker/main/latest_trades.csv"

st.set_page_config(page_title="Eagle Eye: Whale Tracker", layout="wide")

# --- DATA LOADING ---
@st.cache_data(ttl=60) # Automatically refreshes every 60 seconds
def load_data(url):
    # The 'v=' part trick GitHub into sending a fresh file, fixing the "Broken Link"
    fresh_url = f"{url}?v={time.time()}"
    return pd.read_csv(fresh_url)

# --- DASHBOARD UI ---
st.title("🦅 Eagle Eye Insider Terminal")
st.markdown("---")

try:
    df = load_data(URL)
    
    # KPIs for Monday
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Whale Trades", len(df))
    with col2:
        top_ticker = df['Ticker'].iloc[0] if 'Ticker' in df.columns else "N/A"
        st.metric("Top Conviction", top_ticker)
    with col3:
        st.metric("Sync Status", "LIVE ✅")

    # Whale Alert for FGBI or others
    if 'Ticker' in df.columns:
        whales = df[df['Value'] > 250000] if 'Value' in df.columns else df
        if not whales.empty:
            st.warning("🚨 MAJOR WHALE DETECTED: Check your Limit Buys!")
            st.dataframe(whales, use_container_width=True)

    st.subheader("All Recent Insider Activity")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("🚨 Data Link Broken")
    st.info("The file exists on GitHub, but Streamlit is waiting for a refresh.")
    st.write(f"Direct Data Link: [Click here to verify]({URL})")
    if st.button("Force Hard Refresh"):
        st.rerun()

# --- MONDAY PLAN ---
st.sidebar.header("📝 Monday Strategy")
st.sidebar.info("""
**Priority Buys:**
1. FGBI: Limit $5.42
2. NVDA: Limit $187.50
3. GOOGL: Limit $313.80
""")
