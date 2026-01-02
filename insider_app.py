import streamlit as st
import pandas as pd
from sec_api import QueryApi

# 1. Page Configuration
st.set_page_config(page_title="Eagle Eye Dashboard", layout="wide")
st.title("🦅 Eagle Eye: Insider Tracker")

# 2. Setup API Key (Hardcoded as requested)
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Sidebar Diagnostics & Controls
st.sidebar.header("Dashboard Controls")
if st.sidebar.button('🔄 Refresh Data'):
    st.cache_data.clear()
    st.rerun()

# 4. Data Loading Function
@st.cache_data(ttl=3600)
def load_data():
    try:
        # We use a broad Lucene query to ensure results are found
        # Matches Form 4 AND the word "Purchase" in the last 300 days
        search_query = 'formType:"4" AND filedAt:[now-300d TO now] AND "Purchase"'
        
        query = {
            "query": search_query,
            "from": "0", 
            "size": "50", 
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        response = queryApi.get_filings(query)
        
        # Log total results to the sidebar for verification
        total_results = response.get('total', {}).get('value', 0)
        st.sidebar.metric("Total Matches", total_results)
        
        if 'filings' in response and len(response['filings']) > 0:
            return pd.DataFrame(response['filings'])
        return pd.DataFrame()
        
    except Exception as e:
        st.sidebar.error(f"API Connection Error: {e}")
        return pd.DataFrame()

# 5. Main Dashboard Logic
with st.spinner('Scanning SEC database...'):
    df = load_data()

if not df.empty:
    st.success(f"Successfully loaded {len(df)} recent insider purchases.")
    
    # Cleaning up the view for mobile/desktop
    # We display Ticker, Reporting Name, and Filing Date
    display_df = df[['ticker', 'reportingName', 'filedAt']].copy()
    display_df.columns = ['Ticker', 'Insider Name', 'Date Filed']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Optional: Raw data toggle for debugging
    if st.checkbox("Show raw filing data"):
        st.write(df)
else:
    st.warning("No data found for the current filters.")
    st.info("💡 Try clicking 'Refresh Data' in the sidebar if you just updated your code.")
