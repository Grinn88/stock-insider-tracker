import streamlit as st
import pandas as pd
from sec_api import QueryApi

# 1. Dashboard Configuration
st.set_page_config(page_title="Eagle Eye Dashboard", layout="wide")
st.title("🦅 Eagle Eye: High-Conviction Insider Tracker")

# 2. Secure API Key Setup
# Replace the string below with your actual key
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Data Loading Function (with 300-day window for testing)
@st.cache_data(ttl=3600)  # Refresh cache every hour
def load_insider_data():
    query = {
        "query": "formType:\"4\" AND nonDerivativeTable.transactions.coding.code:P AND filedAt:[now-300d TO now]",
        "from": "0", 
        "size": "50", 
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    try:
        response = queryApi.get_filings(query)
        return pd.DataFrame(response['filings'])
    except Exception as e:
        st.error(f"⚠️ API Error: {e}")
        return pd.DataFrame()

# 4. Main App Logic
with st.spinner("Fetching data from SEC..."):
    df = load_insider_data()

if not df.empty:
    # Summary Metrics
    st.success(f"Successfully loaded {len(df)} transactions from the last 300 days.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Filings", len(df))
    
    # 5. Cluster Detection Logic
    # Tickers where 2+ unique individuals bought
    ticker_counts = df.groupby('ticker')['reportingName'].nunique()
    cluster_tickers = ticker_counts[ticker_counts >= 2].index.tolist()
    col2.metric("Active Clusters", len(cluster_tickers))

    # 6. Dashboard Sections
    st.divider()
    
    tab1, tab2 = st.tabs(["🔥 Cluster Alerts", "🐋 All Whale Buys"])

    with tab1:
        st.subheader("High-Conviction Clusters")
        st.write("Multiple insiders buying the same stock simultaneously:")
        if cluster_tickers:
            cluster_df = df[df['ticker'].isin(cluster_tickers)]
            st.dataframe(cluster_df[['ticker', 'reportingName', 'filedAt', 'type']], use_container_width=True)
        else:
            st.info("No clusters found in this timeframe.")

    with tab2:
        st.subheader("Recent Open-Market Purchases")
        st.write("The 50 most recent 'Buy' transactions recorded by the SEC:")
        st.dataframe(df[['ticker', 'reportingName', 'filedAt', 'type']], use_container_width=True)

else:
    st.warning("📡 No data found. Check the Debug section below for details.")

# 7. Hidden Debug Section (Click to expand)
with st.expander("🛠️ Debug System Status"):
    st.write(f"**API Key:** `{API_KEY[:5]}...{API_KEY[-5:]}`")
    st.write(f"**Dataframe Shape:** {df.shape}")
    if st.button("Clear Cache & Retry"):
        st.cache_data.clear()
        st.rerun()