import streamlit as st
import pandas as pd
import plotly.express as px
from sec_api import QueryApi

# 1. Page Config
st.set_page_config(page_title="Eagle Eye Pro", layout="wide")
st.title("🦅 Eagle Eye: Institutional Terminal")

# 2. API Setup
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Sidebar
st.sidebar.header("🎯 Filters")
min_val = st.sidebar.number_input("Min Value ($)", value=100000)
lookback = st.sidebar.slider("Days Lookback", 7, 365, 90)

@st.cache_data(ttl=3600)
def load_fixed_data():
    try:
        # Search for Form 4 Purchases
        query = {
            "query": f'formType:"4" AND filedAt:[now-{lookback}d TO now] AND "Purchase"',
            "from": "0", "size": "100", "sort": [{"filedAt": {"order": "desc"}}]
        }
        response = queryApi.get_filings(query)
        filings = response.get('filings', [])
        
        extracted_data = []
        for f in filings:
            # RELIABLE FILING DATE
            filed_date = f.get('filedAt', 'N/A')[:10]
            ticker = f.get('ticker', 'N/A')
            insider = f.get('reportingName', 'N/A')
            
            # Navigate to transactions
            txs = f.get('nonDerivativeTable', {}).get('transactions', [])
            for t in txs:
                if t.get('coding', {}).get('code') != 'P': continue
                
                # RELIABLE TRADE DATE (Found inside transactionDate)
                trade_date = t.get('transactionDate', filed_date) 
                
                qty = float(t.get('amounts', {}).get('shares', 0))
                price = float(t.get('amounts', {}).get('pricePerShare', 0))
                total_val = qty * price
                post_shares = float(t.get('postTransactionAmounts', {}).get('sharesOwnedFollowingTransaction', 0))
                
                # Ownership Change Calculation
                pre_shares = post_shares - qty
                pct_change = (qty / pre_shares * 100) if pre_shares > 0 else 100
                
                # Industry Mapping (SEC SIC Codes)
                sic = str(f.get('sic', '0000'))
                sector = "Tech" if sic.startswith('35') else "Finance" if sic.startswith('6') else "Healthcare" if sic.startswith('28') else "Energy" if sic.startswith('13') else "Misc"

                extracted_data.append({
                    "Filed": filed_date,
                    "Traded": trade_date,
                    "Ticker": ticker,
                    "Insider": insider,
                    "Title": f.get('reportingOwnerRelationship', {}).get('officerTitle', 'Director'),
                    "Qty": qty,
                    "Price": price,
                    "Value ($)": total_val,
                    "Owned Post": post_shares,
                    "Δ Own": pct_change,
                    "Sector": sector,
                    "10b5-1": "Yes" if "10b5-1" in str(f).lower() else "No"
                })
        
        return pd.DataFrame(extracted_data)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# 4. Dashboard UI
df = load_fixed_data()

if not df.empty:
    # --- SECTOR HEATMAP ---
    st.subheader("🌐 Capital Flow by Sector")
    fig = px.treemap(df, path=['Sector', 'Ticker'], values='Value ($)', 
                     color='Value ($)', color_continuous_scale='RdYlGn')
    st.plotly_chart(fig, use_container_width=True)

    # --- THE TABLE ---
    st.subheader("📑 The Master Feed")
    # Filter by value
    final_df = df[df['Value ($)'] >= min_val].sort_values("Value ($)", ascending=False)
    
    st.dataframe(
        final_df.style.format({
            "Qty": "{:,.0f}", "Price": "${:,.2f}", "Value ($)": "${:,.0f}",
            "Owned Post": "{:,.0f}", "Δ Own": "{:.1f}%"
        }).background_gradient(subset=['Δ Own'], cmap='YlGn'),
        use_container_width=True, hide_index=True
    )
    
    # --- SMART ANALYSIS ---
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.success("🔥 **CLUSTER ALERT**")
        clusters = final_df['Ticker'].value_counts()
        st.write(clusters[clusters >= 2])
    with col2:
        st.info("🐋 **WHALE ALERT**")
        st.write(final_df[final_df['Value ($)'] >= 500000][['Ticker', 'Insider', 'Value ($)']])

else:
    st.warning("No trades found. Lower the 'Min Value' in the sidebar.")
