import streamlit as st
import pandas as pd
from sec_api import QueryApi
from datetime import datetime, timedelta

# 1. Dashboard Config
st.set_page_config(page_title="Eagle Eye Terminal", layout="wide")
st.title("🦅 Eagle Eye: Absolute Conviction Feed")

# 2. Setup API (Using your key)
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Sidebar Filters
st.sidebar.header("🎯 Filter Signals")
lookback = st.sidebar.selectbox("Analysis Horizon", [30, 60, 90], index=0)
min_whale = st.sidebar.selectbox("Minimum Buy Value", [250000, 500000, 1000000], format_func=lambda x: f"${x:,}")

# 4. The "Never-Fail" Data Engine
@st.cache_data(ttl=3600) # Prevents credit burn (saves data for 1 hour)
def load_reliable_data():
    try:
        # Step 1: Query only for 'P' (Open Market Purchase) - The most reliable query
        # We pull 100 to ensure we have enough data to fill your filters
        query = {
            "query": "formType:\"4\" AND nonDerivativeTable.transactions.coding.code:P",
            "from": "0", "size": "100", 
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        response = queryApi.get_filings(query)
        filings = response.get('filings', [])
        
        if not filings:
            return pd.DataFrame()

        rows = []
        for f in filings:
            filed_at = f.get('filedAt', '')[:10]
            ticker = f.get('ticker', 'N/A')
            insider = f.get('reportingName', 'N/A')
            title = f.get('reportingOwnerRelationship', {}).get('officerTitle', 'Director')
            
            # Extract transactions safely
            txs = f.get('nonDerivativeTable', {}).get('transactions', [])
            for t in txs:
                if t.get('coding', {}).get('code') == 'P':
                    qty = float(t.get('amounts', {}).get('shares', 0))
                    price = float(t.get('amounts', {}).get('pricePerShare', 0))
                    val = qty * price
                    traded_on = t.get('transactionDate', filed_at)
                    
                    # Pro Metric: Ownership change
                    post_shares = float(t.get('postTransactionAmounts', {}).get('sharesOwnedFollowingTransaction', 0))
                    prev_shares = post_shares - qty
                    delta = (qty / prev_shares * 100) if prev_shares > 0 else 100

                    rows.append({
                        "Filed": filed_at,
                        "Traded": traded_on,
                        "Ticker": ticker,
                        "Insider": insider,
                        "Title": title,
                        "Value ($)": val,
                        "Price": price,
                        "Qty": qty,
                        "Owned Post": post_shares,
                        "Δ Own": delta,
                        "10b5-1": "Yes" if "10b5-1" in str(f).lower() else "No"
                    })
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Logic Error: {e}")
        return pd.DataFrame()

# 5. UI Logic
raw_df = load_reliable_data()

if not raw_df.empty:
    # Python-side filtering (Avoids API query errors)
    cutoff_date = (datetime.now() - timedelta(days=lookback)).strftime('%Y-%m-%d')
    df = raw_df[
        (raw_df['Filed'] >= cutoff_date) & 
        (raw_df['Value ($)'] >= min_whale)
    ].copy()

    if not df.empty:
        # Metrics Row
        c1, c2, c3 = st.columns(3)
        c1.metric("Signals Found", len(df))
        c2.metric("Total Whale Capital", f"${df['Value ($)'].sum():,.0f}")
        c3.metric("Avg Buy Price", f"${df['Price'].mean():.2f}")

        # The Master Table
        st.subheader(f"📑 Top High-Conviction Buys (Over ${min_whale:,})")
        st.dataframe(
            df.sort_values("Value ($)", ascending=False).style.format({
                "Value ($)": "${:,.0f}", "Price": "${:,.2f}", 
                "Qty": "{:,.0f}", "Owned Post": "{:,.0f}", "Δ Own": "{:.1f}%"
            }).background_gradient(subset=['Δ Own'], cmap='YlGn'),
            use_container_width=True, hide_index=True
        )
    else:
        st.warning(f"No trades over ${min_whale:,} found in the last {lookback} days.")
else:
    st.error("Could not connect to SEC. Check your API Key or Credit balance at sec-api.io.")

if st.button("🔄 Clear Cache & Update"):
    st.cache_data.clear()
    st.rerun()
