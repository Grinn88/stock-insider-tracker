import streamlit as st
import pandas as pd
from sec_api import QueryApi
from datetime import datetime, timedelta

# 1. Dashboard Config
st.set_page_config(page_title="Eagle Eye: Time Machine", layout="wide")
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 2. Sidebar Time Controls
st.sidebar.header("⏳ Time Horizon")
days_to_lookback = st.sidebar.radio("Select Lookback Period", [30, 60, 90], index=0)
min_value = st.sidebar.slider("Minimum Buy Value ($)", 50000, 1000000, 250000, step=50000)

@st.cache_data(ttl=3600)
def fetch_historical_whales(days):
    # Calculate the date range for the query
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Advanced Query: Form 4 + Purchases + Specific Date Range
    query_str = f'formType:"4" AND filedAt:[{start_date} TO {end_date}] AND "Purchase"'
    
    try:
        query = {
            "query": query_str,
            "from": "0", "size": "100", 
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        response = queryApi.get_filings(query)
        return response.get('filings', [])
    except Exception as e:
        st.error(f"API Error: {e}")
        return []

# 3. Process & Display
st.title(f"🐋 Insider Whales: Last {days_to_lookback} Days")

raw_filings = fetch_historical_whales(days_to_lookback)

if raw_filings:
    processed_data = []
    for f in raw_filings:
        ticker = f.get('ticker', 'N/A')
        insider = f.get('reportingName', 'N/A')
        date = f.get('filedAt', '')[:10]
        
        # Extract specific transaction amounts
        transactions = f.get('nonDerivativeTable', {}).get('transactions', [])
        for t in transactions:
            if t.get('coding', {}).get('code') == 'P':
                qty = float(t.get('amounts', {}).get('shares', 0))
                price = float(t.get('amounts', {}).get('pricePerShare', 0))
                val = qty * price
                
                if val >= min_value:
                    processed_data.append({
                        "Date": date,
                        "Ticker": ticker,
                        "Insider": insider,
                        "Value ($)": val,
                        "Price": price,
                        "Shares": qty
                    })

    if processed_data:
        df = pd.DataFrame(processed_data)
        
        # Summary Metrics
        m1, m2 = st.columns(2)
        m1.metric("Total High-Value Buys", len(df))
        m2.metric("Total Capital Flow", f"${df['Value ($)'].sum():,.0f}")
        
        # Data Table
        st.dataframe(
            df.sort_values("Value ($)", ascending=False).style.format({
                "Value ($)": "${:,.0f}", "Price": "${:,.2f}", "Shares": "{:,.0f}"
            }), 
            use_container_width=True, hide_index=True
        )
    else:
        st.warning(f"No buys over ${min_value:,} found in the last {days_to_lookback} days.")
else:
    st.info("No filings found for this period. Try increasing the lookback or lowering the minimum value.")
