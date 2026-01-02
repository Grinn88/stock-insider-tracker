import streamlit as st
import pandas as pd
from sec_api import QueryApi

# 1. Page Configuration
st.set_page_config(page_title="Eagle Eye: Pro Screener", layout="wide")
st.title("🦅 Eagle Eye: High-Conviction Insider Screener")

# 2. API Key Setup
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Sidebar Filtering & Settings
st.sidebar.header("Advanced Screener Filters")
min_trade_val = st.sidebar.slider("Minimum Trade Value ($)", 0, 1000000, 100000, step=50000)
lookback_days = st.sidebar.selectbox("Lookback Period", ["30d", "60d", "90d", "300d"], index=2)

if st.sidebar.button('🔄 Sync with SEC Live Feed'):
    st.cache_data.clear()
    st.rerun()

# 4. Professional Data Loader
@st.cache_data(ttl=3600)
def load_and_parse_insider_data():
    try:
        # Strict Query: Open Market Purchases (Code P) only
        search_query = f'formType:"4" AND filedAt:[now-{lookback_days} TO now] AND "Purchase"'
        query = {"query": search_query, "from": "0", "size": "50", "sort": [{"filedAt": {"order": "desc"}}]}
        
        response = queryApi.get_filings(query)
        if not response.get('filings'): return pd.DataFrame()

        screener_data = []
        for filing in response['filings']:
            ticker = filing.get('ticker', 'N/A')
            insider = filing.get('reportingName', 'Unknown')
            filed_date = filing.get('filedAt', '')[:10]
            
            # Navigating Table I: Non-Derivative Transactions
            nd_table = filing.get('nonDerivativeTable', {})
            txns = nd_table.get('transactions', [])
            
            for t in txns:
                # Filter for 'P' (Open Market Purchase)
                if t.get('coding', {}).get('code') != 'P': continue
                
                # Transaction Core Details
                qty = float(t.get('amounts', {}).get('shares', 0))
                price = float(t.get('amounts', {}).get('pricePerShare', 0))
                total_val = qty * price
                
                # Ownership Change Analysis
                post_shares = float(t.get('postTransactionAmounts', {}).get('sharesOwnedFollowingTransaction', 0))
                pre_shares = post_shares - qty
                pct_change = (qty / pre_shares * 100) if pre_shares > 0 else 100
                
                # Strategy Flags
                signal = "Standard"
                if total_val >= 500000: signal = "🐋 WHALE"
                
                screener_data.append({
                    "Date": filed_date,
                    "Ticker": ticker,
                    "Insider": insider,
                    "Qty": qty,
                    "Price": price,
                    "Value ($)": total_val,
                    "Owned Post": post_shares,
                    "ΔOwn": pct_change,
                    "Signal": signal
                })

        df = pd.DataFrame(screener_data)
        if df.empty: return df

        # Cluster Detection (3+ insiders buying the same ticker)
        clusters = df.groupby('Ticker')['Insider'].nunique()
        df['Signal'] = df.apply(lambda x: "🔥 CLUSTER" if clusters.get(x['Ticker'], 0) >= 3 else x['Signal'], axis=1)

        return df[df['Value ($)'] >= min_trade_val].sort_values('Value ($)', ascending=False)

    except Exception as e:
        st.error(f"Screener Error: {e}")
        return pd.DataFrame()

# 5. Main UI
with st.spinner('Scanning for Alpha...'):
    df = load_and_parse_insider_data()

if not df.empty:
    st.info(f"Showing {len(df)} High-Conviction trades. Sorted by Total Value.")
    
    # Format columns for professional display
    st.dataframe(
        df.style.format({
            "Qty": "{:,.0f}",
            "Price": "${:,.2f}",
            "Value ($)": "${:,.0f}",
            "Owned Post": "{:,.0f}",
            "ΔOwn": "{:.1f}%"
        }).applymap(lambda x: 'background-color: #ff4b4b; color: white; font-weight: bold' if "CLUSTER" in str(x) else 
                             'background-color: #1c83e1; color: white; font-weight: bold' if "WHALE" in str(x) else '', subset=['Signal']),
        use_container_width=True, hide_index=True
    )
    
    # Decision Matrix
    st.markdown("---")
    st.subheader("💡 Investor's Decision Matrix")
    cols = st.columns(3)
    with cols[0]:
        st.write("**High conviction:** ΔOwn > 20%")
        st.caption("Insider significantly increased their skin in the game.")
    with cols[1]:
        st.write("**Smart Money:** Cluster 🔥")
        st.caption("Boardroom consensus. Usually precedes a major catalyst.")
    with cols[2]:
        st.write("**Due Diligence:** Check Financials")
        ticker_list = df['Ticker'].unique()
        selected = st.selectbox("Quick Check Revenue/Financials:", ticker_list)
        st.link_button(f"View {selected} Revenue on Yahoo Finance", f"https://finance.yahoo.com/quote/{selected}/financials")

else:
    st.warning("No trades found matching your filters. Try lowering 'Min Trade Value' in the sidebar.")
