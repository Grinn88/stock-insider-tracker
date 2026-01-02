import streamlit as st
import pandas as pd
from sec_api import QueryApi

# 1. Page Configuration
st.set_page_config(page_title="High Conviction Insider Tracker", layout="wide")
st.title("🦅 Eagle Eye: Whale & Cluster Tracker")

# 2. API Key Setup
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Sidebar for Quick Action
st.sidebar.header("Filter Controls")
if st.sidebar.button('🔄 Refresh Real-Time Data'):
    st.cache_data.clear()
    st.rerun()

# 4. Smart Data Loader
@st.cache_data(ttl=3600)
def load_and_analyze_data():
    try:
        # Search for Form 4 purchases in the last 300 days
        search_query = 'formType:"4" AND filedAt:[now-300d TO now] AND "Purchase"'
        query = {
            "query": search_query,
            "from": "0", "size": "100",
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        response = queryApi.get_filings(query)
        if not response.get('filings'):
            return pd.DataFrame()

        df = pd.DataFrame(response['filings'])

        # --- FIX: Column Normalization ---
        # The SEC sometimes calls the person 'reportingName' and sometimes 'companyName'
        if 'reportingName' not in df.columns:
            if 'companyName' in df.columns:
                df['reportingName'] = df['companyName']
            else:
                df['reportingName'] = "Unknown Insider"

        # --- SIGNAL ANALYSIS LOGIC ---
        
        # 1. Cluster Detection
        cluster_counts = df.groupby('ticker')['reportingName'].nunique()
        df['Cluster?'] = df['ticker'].map(lambda x: "🔥 CLUSTER" if cluster_counts.get(x, 0) >= 3 else "")

        # 2. Whale Detection (Flagging key titles)
        whale_titles = ['CEO', 'CHIEF FINANCIAL OFFICER', 'CFO', 'DIRECTOR', '10% OWNER']
        df['Signal Type'] = df['reportingName'].apply(
            lambda x: "🐋 WHALE" if any(title in str(x).upper() for title in whale_titles) else "Standard"
        )

        return df
    except Exception as e:
        st.error(f"Analysis Error: {e}")
        return pd.DataFrame()

# 5. Main Dashboard View
with st.spinner('Hunting for Whales and Clusters...'):
    df = load_and_analyze_data()

if not df.empty:
    st.subheader("Latest Insider Signals")
    
    # Selecting the best columns for mobile viewing
    display_cols = ['ticker', 'reportingName', 'filedAt', 'Cluster?', 'Signal Type']
    
    # Ensure all display columns actually exist before showing the table
    final_cols = [c for c in display_cols if c in df.columns]

    # Apply color styling
    def style_rows(val):
        if "CLUSTER" in str(val): return 'background-color: #ff4b4b; color: white'
        if "WHALE" in str(val): return 'background-color: #1c83e1; color: white'
        return ''

    st.dataframe(
        df[final_cols].style.applymap(style_rows),
        use_container_width=True,
        hide_index=True
    )
    
    # Strategy Guide
    st.info("💡 **WHALE:** A heavy hitter (CEO/CFO) is buying. **CLUSTER:** 3+ different people are buying the same stock.")
else:
    st.warning("No data found. Try clicking 'Refresh' in the sidebar.")
