import streamlit as st
import pandas as pd
from sec_api import QueryApi

# 1. Page Configuration
st.set_page_config(page_title="Eagle Eye: Insider Tracker", layout="wide")
st.title("🦅 Eagle Eye: Live Insider Feed")

# 2. Setup API
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Simple Search Logic (The "Working" Query)
@st.cache_data(ttl=600)
def load_data():
    try:
        # Simplified query to avoid date-range errors
        # This searches for the 50 most recent "Purchase" Form 4s
        query = {
            "query": "formType:\"4\" AND \"Purchase\"", 
            "from": "0", 
            "size": "50", 
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        response = queryApi.get_filings(query)
        filings = response.get('filings', [])
        
        extracted = []
        for f in filings:
            # Basic info
            filed_at = f.get('filedAt', 'N/A')[:10]
            ticker = f.get('ticker', 'N/A')
            insider = f.get('reportingName', 'N/A')
            
            # Transaction logic
            txs = f.get('nonDerivativeTable', {}).get('transactions', [])
            for t in txs:
                # Ensure we only show actual buys ('P')
                if t.get('coding', {}).get('code') == 'P':
                    shares = float(t.get('amounts', {}).get('shares', 0))
                    price = float(t.get('amounts', {}).get('pricePerShare', 0))
                    value = shares * price
                    
                    extracted.append({
                        "Date": filed_at,
                        "Ticker": ticker,
                        "Insider": insider,
                        "Value ($)": value,
                        "Price": price,
                        "Shares": shares
                    })
        return pd.DataFrame(extracted)
    except Exception as e:
        st.error(f"Error connecting to SEC: {e}")
        return pd.DataFrame()

# 4. Run & Display
df = load_data()

if not df.empty:
    st.success(f"Found {len(df)} recent trades!")
    
    # Simple, reliable table display
    st.dataframe(
        df.sort_values("Date", ascending=False).style.format({
            "Value ($)": "${:,.0f}",
            "Price": "${:,.2f}",
            "Shares": "{:,.0f}"
        }),
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("Still no trades found. Check if your SEC-API key has reached its limit or try refreshing.")

# 5. Manual Refresh Button
if st.button("🔄 Refresh Data Now"):
    st.cache_data.clear()
    st.rerun()
