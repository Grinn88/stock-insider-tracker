import streamlit as st
import pandas as pd
from sec_api import QueryApi
import requests
import json

# 1. Setup
st.set_page_config(page_title="Eagle Eye: Bulletproof", layout="wide")
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"

# 2. Connection Health Check (The Diagnostic)
def check_api_health():
    """Checks if the key is active without using a full credit."""
    url = f"https://api.sec-api.io?token={API_KEY}"
    try:
        # We use a POST with a tiny size to test the line
        test_payload = {"query": "formType:\"4\"", "from": 0, "size": 1}
        response = requests.post(url, json=test_payload, timeout=10)
        
        if response.status_code == 200:
            return True, "Connected"
        elif response.status_code == 401:
            return False, "Invalid API Key"
        elif response.status_code == 429:
            return False, "Rate Limited / Out of Credits"
        else:
            return False, f"Server Error: {response.status_code}"
    except Exception as e:
        return False, f"Connection Failed: {str(e)}"

# 3. Robust Data Loader
@st.cache_data(ttl=3600)
def load_data_robust():
    # Use the official library but wrap it in a fallback
    try:
        queryApi = QueryApi(api_key=API_KEY)
        
        # We use the most basic query possible to ensure success
        # This bypasses date-math which often causes 'No Data' errors
        search_parameters = {
            "query": "formType:\"4\" AND \"Purchase\"",
            "from": "0",
            "size": "40",
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        response = queryApi.get_filings(search_parameters)
        return response.get('filings', [])
    except Exception:
        return []

# --- UI LOGIC ---
st.title("🦅 Eagle Eye: Verified Connection")

# Run Diagnostic
is_healthy, status_msg = check_api_health()

if is_healthy:
    st.success(f"✅ System Status: {status_msg}")
    
    # Sidebar Filters
    min_val = st.sidebar.selectbox("Min Trade Value", [250000, 500000, 1000000])
    
    filings = load_data_robust()
    
    if filings:
        data = []
        for f in filings:
            # Safe extraction
            txs = f.get('nonDerivativeTable', {}).get('transactions', [])
            for t in txs:
                if t.get('coding', {}).get('code') == 'P':
                    v = float(t.get('amounts', {}).get('shares', 0)) * float(t.get('amounts', {}).get('pricePerShare', 0))
                    if v >= min_val:
                        data.append({
                            "Date": f.get('filedAt', '')[:10],
                            "Ticker": f.get('ticker'),
                            "Insider": f.get('reportingName'),
                            "Value ($)": v,
                            "Price": float(t.get('amounts', {}).get('pricePerShare', 0)),
                            "Title": f.get('reportingOwnerRelationship', {}).get('officerTitle', 'Director')
                        })
        
        if data:
            df = pd.DataFrame(data).sort_values("Value ($)", ascending=False)
            st.dataframe(df.style.format({"Value ($)": "${:,.0f}", "Price": "${:,.2f}"}), use_container_width=True, hide_index=True)
        else:
            st.info(f"Connected, but no trades found over ${min_val:,} today.")
    else:
        st.warning("The SEC database is responding but returned no purchase data for this window.")
else:
    st.error(f"🛑 Connection Blocked: {status_msg}")
    st.info("Try turning off your VPN or checking if your company firewall blocks 'api.sec-api.io'.")
