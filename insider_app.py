import streamlit as st
import pandas as pd
from sec_api import QueryApi
from datetime import datetime, timedelta

# 1. Dashboard Configuration
st.set_page_config(page_title="Eagle Eye: Alpha Terminal", layout="wide")
st.title("🦅 Eagle Eye: Institutional Alpha Engine")

# 2. Setup API
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Sidebar Pro-Filters
st.sidebar.header("🎯 Signal Sensitivity")
lookback_period = st.sidebar.selectbox("Analysis Horizon", [30, 60, 90], index=2)
whale_threshold = st.sidebar.selectbox("Whale Threshold ($)", [250000, 500000, 1000000], index=0)

# 4. Deep Search Engine
@st.cache_data(ttl=3600)
def load_alpha_data(days):
    try:
        # Calculate precise dates
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # The most reliable Query String for the SEC-API
        # We search specifically for the 'P' code (Open Market Purchase)
        lucene_query = f'formType:"4" AND filedAt:[{start_date} TO {end_date}] AND nonDerivativeTable.transactions.coding.code:P'
        
        payload = {
            "query": lucene_query,
            "from": "0",
            "size": "200", # Pulled 200 to ensure we capture clusters
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        response = queryApi.get_filings(payload)
        filings = response.get('filings', [])
        
        results = []
        for f in filings:
            filed_date = f.get('filedAt', 'N/A')[:10]
            ticker = f.get('ticker', 'N/A')
            insider = f.get('reportingName', 'N/A')
            title = f.get('reportingOwnerRelationship', {}).get('officerTitle', 'Director')
            
            # Deep parse the transaction tables
            txs = f.get('nonDerivativeTable', {}).get('transactions', [])
            for t in txs:
                # Only include actual cash buys
                if t.get('coding', {}).get('code') == 'P':
                    qty = float(t.get('amounts', {}).get('shares', 0))
                    price = float(t.get('amounts', {}).get('pricePerShare', 0))
                    val = qty * price
                    trade_date = t.get('transactionDate', filed_date)
                    
                    # Ownership Delta (Position Increase %)
                    post_shares = float(t.get('postTransactionAmounts', {}).get('sharesOwnedFollowingTransaction', 0))
                    pre_shares = post_shares - qty
                    delta = (qty / pre_shares * 100) if pre_shares > 0 else 100

                    results.append({
                        "Filed": filed_date,
                        "Traded": trade_date,
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
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"Engine Error: {e}")
        return pd.DataFrame()

# 5. UI Presentation
df_raw = load_alpha_data(lookback_period)

if not df_raw.empty:
    # Filter by whale threshold
    df = df_raw[df_raw['Value ($)'] >= whale_threshold].copy()
    
    if not df.empty:
        # Top Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Whale Trades Found", len(df))
        c2.metric("Total Capital Inflow", f"${df['Value ($)'].sum():,.0f}")
        c3.metric("Highest Conviction (Δ)", f"{df['Δ Own'].max():.1f}%")

        # Cluster Detection Logic
        clusters = df.groupby('Ticker')['Insider'].nunique()
        df['Signal'] = df.apply(lambda x: "🔥 CLUSTER" if clusters.get(x['Ticker'], 0) >= 2 else "🐋 WHALE", axis=1)

        # Master Table with 11 Professional Columns
        st.subheader(f"📑 Top High-Conviction Trades (Last {lookback_period} Days)")
        st.dataframe(
            df.sort_values("Value ($)", ascending=False).style.format({
                "Value ($)": "${:,.0f}", "Price": "${:,.2f}", 
                "Qty": "{:,.0f}", "Owned Post": "{:,.0f}", "Δ Own": "{:.1f}%"
            }).applymap(lambda x: 'background-color: #ff4b4b; color: white' if x == "🔥 CLUSTER" else '', subset=['Signal']),
            use_container_width=True, hide_index=True
        )
    else:
        st.warning(f"No trades over ${whale_threshold:,} found in this window. Try lowering the threshold.")
else:
    st.info("Searching the SEC database... If this persists, check your credit balance.")

# 6. Manual Control
if st.sidebar.button("🔄 Force Data Refresh"):
    st.cache_data.clear()
    st.rerun()
