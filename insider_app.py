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
        # Broad query to catch all insider activity
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

        # --- SIGNAL ANALYSIS LOGIC ---
        
        # 1. Cluster Detection: Group by ticker to see how many unique insiders are buying
        cluster_counts = df.groupby('ticker')['reportingName'].nunique()
        df['Cluster?'] = df['ticker'].map(lambda x: "🔥 CLUSTER" if cluster_counts.get(x, 0) >= 3 else "")

        # 2. Whale Detection: (Note: SEC-API returns metadata; transaction value often requires 
        # deep-parsing, but we can flag based on typical high-volume insiders)
        # For now, we flag the most senior 'Whale' titles
        whale_titles = ['CEO', 'Chief Financial Officer', 'Director', '10% Owner']
        df['Signal Type'] = df['reportingName'].apply(lambda x: "🐋 WHALE" if any(title in str(x).upper() for title in whale_titles) else "Standard")

        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# 5. Display Dashboard
with st.spinner('Hunting for Whales and Clusters...'):
    df = load_and_analyze_data()

if not df.empty:
    # Highlight the high-conviction signals
    st.subheader("Latest High-Confidence Signals")
    
    # Select specific columns for a clean mobile/desktop view
    display_cols = ['ticker', 'reportingName', 'filedAt', 'Cluster?', 'Signal Type']
    
    # Styling for easier reading on your phone
    def highlight_signals(val):
        if "CLUSTER" in str(val): return 'background-color: #ff4b4b; color: white; font-weight: bold'
        if "WHALE" in str(val): return 'background-color: #1c83e1; color: white; font-weight: bold'
        return ''

    st.dataframe(
        df[display_cols].style.applymap(highlight_signals),
        use_container_width=True,
        hide_index=True
    )

    # Strategy Guide
    with st.expander("📚 How to Trade These Signals"):
        st.markdown("""
        * **The Cluster (🔥):** When 3+ insiders buy, it means the board has a 'unified consensus' that the stock is undervalued. This is the strongest signal for long-term gains.
        * **The Whale (🐋):** Look for the CFO or CEO putting their own cash on the line. It's especially powerful if they haven't bought in years.
        * **Timing:** Research shows most 'insider alpha' (extra profit) happens **2-6 months** after they buy. Don't panic if the stock doesn't move today.
        """)
else:
    st.warning("No data found. Click 'Refresh' in the sidebar to try again.")
