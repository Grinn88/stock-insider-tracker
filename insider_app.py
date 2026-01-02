import streamlit as st
import pandas as pd
from sec_api import QueryApi

# 1. Page Configuration
st.set_page_config(page_title="Eagle Eye: Master Terminal", layout="wide")
st.title("🦅 Eagle Eye: Master Insider Terminal")

# 2. API Key Setup
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Sidebar: Pro Filters
st.sidebar.header("Decision Filters")
# Quick-toggle for your $250k request
if st.sidebar.button('🐋 Show Only $250k+ Whales'):
    st.session_state.min_val = 250000
elif 'min_val' not in st.session_state:
    st.session_state.min_val = 50000

min_val = st.sidebar.number_input("Min Transaction Value ($)", value=st.session_state.min_val)
lookback = st.sidebar.slider("Lookback (Days)", 30, 365, 180)

if st.sidebar.button('🔄 Refresh Real-Time Feed'):
    st.cache_data.clear()
    st.rerun()

# 4. Master Data Engine
@st.cache_data(ttl=3600)
def load_master_data(min_val_filter, days):
    try:
        # Query: Form 4 Purchases (Code P)
        search_query = f'formType:"4" AND filedAt:[now-{days}d TO now] AND "Purchase"'
        query = {"query": search_query, "from": "0", "size": "100", "sort": [{"filedAt": {"order": "desc"}}]}
        
        response = queryApi.get_filings(query)
        if not response.get('filings'): return pd.DataFrame()

        master_list = []
        for f in response['filings']:
            ticker = f.get('ticker', 'N/A')
            insider = f.get('reportingName', 'Unknown')
            title = f.get('reportingOwnerRelationship', {}).get('officerTitle', 'Director/Owner')
            filed_date = f.get('filedAt', 'N/A')[:10]
            
            transactions = f.get('nonDerivativeTable', {}).get('transactions', [])
            for t in transactions:
                if t.get('coding', {}).get('code') != 'P': continue
                
                # Data Extraction
                trade_date = t.get('transactionDate', 'N/A')
                qty = float(t.get('amounts', {}).get('shares', 0))
                price = float(t.get('amounts', {}).get('pricePerShare', 0))
                value = qty * price
                
                # Ownership Context
                owned_post = float(t.get('postTransactionAmounts', {}).get('sharesOwnedFollowingTransaction', 0))
                # % Position Increase
                prev_owned = owned_post - qty
                own_delta = (qty / prev_owned * 100) if prev_owned > 0 else 100
                
                # Signal Logic
                sig = "Standard"
                if value >= 500000: sig = "🐋 WHALE"
                if "10b5-1" in str(f.get('remarks', '')).lower(): sig = "📅 PLANNED"

                master_list.append({
                    "Ticker": ticker,
                    "Insider": insider,
                    "Title": title,
                    "Trade Date": trade_date,
                    "Filed Date": filed_date,
                    "Qty": qty,
                    "Price": price,
                    "Total Value": value,
                    "Owned Post": owned_post,
                    "ΔOwn": own_delta,
                    "Signal": sig
                })

        df = pd.DataFrame(master_list)
        if df.empty: return df

        # Cluster Detection
        clusters = df.groupby('Ticker')['Insider'].nunique()
        df['Signal'] = df.apply(lambda x: "🔥 CLUSTER" if clusters.get(x['Ticker'], 0) >= 3 else x['Signal'], axis=1)

        return df[df['Total Value'] >= min_val_filter].sort_values('Total Value', ascending=False)

    except Exception as e:
        st.error(f"Engine Error: {e}")
        return pd.DataFrame()

# 5. UI Layout
with st.spinner('Scanning the Boardroom...'):
    df = load_master_data(min_val, lookback)

if not df.empty:
    st.success(f"Found {len(df)} High-Conviction Trades above ${min_val:,}")
    
    # Professional Styling
    st.dataframe(
        df.style.format({
            "Qty": "{:,.0f}", "Price": "${:,.2f}", 
            "Total Value": "${:,.0f}", "Owned Post": "{:,.0f}", "ΔOwn": "+{:.1f}%"
        }).applymap(lambda x: 'background-color: #ff4b4b; color: white' if "CLUSTER" in str(x) else 
                             'background-color: #1c83e1; color: white' if "WHALE" in str(x) else 
                             'color: #888' if "PLANNED" in str(x) else '', subset=['Signal']),
        use_container_width=True, hide_index=True
    )
else:
    st.warning(f"No buys found over ${min_val:,}. Suggestion: Lower filter to $10,000 or increase 'Lookback' to 365 days.")

# 6. Deep Research Tools
if not df.empty:
    st.divider()
    selected_ticker = st.selectbox("Select a Ticker for Deep Research:", df['Ticker'].unique())
    col1, col2, col3 = st.columns(3)
    col1.link_button(f"📈 {selected_ticker} Chart", f"https://www.tradingview.com/symbols/{selected_ticker}/")
    col2.link_button(f"💰 {selected_ticker} Revenue", f"https://finance.yahoo.com/quote/{selected_ticker}/financials")
    col3.link_button(f"🔍 OpenInsider Detail", f"http://openinsider.com/search?q={selected_ticker}")
