import streamlit as st
import pandas as pd
from sec_api import QueryApi

# 1. Page Configuration
st.set_page_config(page_title="Eagle Eye Dashboard", layout="wide")
st.title("🦅 Eagle Eye: Insider Tracker")

# 2. Setup API Key
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Sidebar Controls
st.sidebar.header("Dashboard Controls")
if st.sidebar.button('🔄 Refresh Data'):
    st.cache_data.clear()
    st.rerun()

# 4. Data Loading Function
@st.cache_data(ttl=3600)
def load_data():
    try:
        # Broad query for Form 4 (Insider Trades) with "Purchase" keyword
        search_query = 'formType:"4" AND filedAt:[now-300d TO now] AND "Purchase"'
        
        query = {
            "query": search_query,
            "from": "0", 
            "size": "50", 
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        response = queryApi.get_filings(query)
        total_results = response.get('total', {}).get('value', 0)
        st.sidebar.metric("Total Matches Found", total_results)
        
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
    st.success(f"Successfully loaded {len(df)} transactions.")
    
    # --- AUTO-COLUMN DETECTION ---
    # We look for common SEC field names so the table is never empty
    potential_cols = ['ticker', 'companyName', 'reportingName', 'filedAt', 'formType']
    # Only use columns that actually exist in the data
    available_cols = [c for c in potential_cols if c in df.columns]
    
    if not available_cols:
        # If none of our preferred columns exist, show the first 5 columns found
        available_cols = df.columns[:5].tolist()

    # Display the cleaned table
    st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
    
    # Debugging: Toggle to see all hidden data fields
    with st.expander("🛠️ Advanced: See Raw Data Fields"):
        st.write("All available data fields:", list(df.columns))
        st.write(df)
else:
    st.warning("No data found. Check your API quota or try 'Refresh' in the sidebar.")
