import streamlit as st
import pandas as pd
from sec_api import QueryApi
from datetime import datetime, timedelta
import pytz

# 1. Setup & Configuration
st.set_page_config(page_title="Eagle Eye: Credit-Safe", layout="wide")

API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 2. CREDIT GUARD: Check if the SEC is even open
def is_sec_open():
    # SEC EDGAR usually operates Mon-Fri, 6:00 AM - 10:00 PM ET
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    if now.weekday() >= 5: # Saturday or Sunday
        return False
    return True

# 3. INTELLIGENT CACHING: Save credits by storing results for 1 hour
@st.cache_data(ttl=3600) # 3600 seconds = 1 Hour. This is your "Credit Shield"
def fetch_data_with_cache(days_back, min_threshold):
    # Only calculate the start date once
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    lucene_query = f'formType:"4" AND filedAt:[{start_date} TO {end_date}] AND nonDerivativeTable.transactions.coding.code:P'
    
    payload = {
        "query": lucene_query,
        "from": "0", "size": "100",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    response = queryApi.get_filings(payload)
    filings = response.get('filings', [])
    
    data = []
    for f in filings:
        txs = f.get('nonDerivativeTable', {}).get('transactions', [])
        for t in txs:
            if t.get('coding', {}).get('code') == 'P':
                val = float(t.get('amounts', {}).get('shares', 0)) * float(t.get('amounts', {}).get('pricePerShare', 0))
                if val >= min_threshold:
                    data.append({
                        "Date": f.get('filedAt', '')[:10],
                        "Ticker": f.get('ticker'),
                        "Insider": f.get('reportingName'),
                        "Value ($)": val,
                        "Price": float(t.get('amounts', {}).get('pricePerShare', 0)),
                        "10b5-1": "Yes" if "10b5-1" in str(f).lower() else "No"
                    })
    return pd.DataFrame(data)

# 4. Sidebar Strategy
st.sidebar.header("🛡️ Credit Management")
st.sidebar.info(f"Cache active: Data refreshes every 60 mins to save credits.")

lookback = st.sidebar.selectbox("Horizon", [30, 60, 90])
whale_limit = st.sidebar.selectbox("Min Trade Value", [250000, 500000, 1000000])

# 5. Execution Logic
if not is_sec_open():
    st.sidebar.warning("🌙 SEC is currently closed. Using last cached data.")

df = fetch_data_with_cache(lookback, whale_limit)

# 6. UI Output
if not df.empty:
    st.title(f"🦅 Insider Whales over ${whale_limit:,}")
    st.dataframe(df.sort_values("Value ($)", ascending=False), use_container_width=True, hide_index=True)
else:
    st.warning("No new data found. Your credits are safe.")
