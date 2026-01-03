import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. Dashboard Configuration
st.set_page_config(page_title="Eagle Eye: FMP Terminal", layout="wide")
st.title("🦅 Eagle Eye: Institutional Alpha Engine (FMP Edition)")

# 2. Setup API
# Replace with your FMP API Key
API_KEY = "YRByZglolMGVabAR6rOWHzeumPey2CBH"

# 3. Sidebar Pro-Filters
st.sidebar.header("🎯 Signal Sensitivity")
# FMP provides recent trades; we'll pull a large batch and filter by date in Python
whale_threshold = st.sidebar.selectbox("Whale Threshold ($)", [100000, 250000, 500000, 1000000], index=1)
lookback_days = st.sidebar.slider("Lookback Period (Days)", 7, 90, 30)

# 4. FMP Data Engine
@st.cache_data(ttl=3600)
def load_fmp_insider_data(days):
    try:
        # FMP 'Latest' endpoint provides a stream of recent Form 4s
        # We use a high limit (400) to ensure we cover the lookback period
        url = f"https://financialmodelingprep.com/api/v4/insider-trading?limit=400&apikey={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        trades = response.json()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        results = []
        
        for t in trades:
            # Parse the date from FMP (usually 'yyyy-mm-dd hh:mm:ss')
            filing_date_str = t.get('filingDate', '').split(' ')[0]
            if not filing_date_str: continue
            filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d').date()
            
            # Filter by Date and Transaction Type (P-Purchase is Open Market Buy)
            if filing_date >= cutoff_date and t.get('transactionType') == 'P-Purchase':
                ticker = t.get('symbol', 'N/A')
                insider = t.get('reportingName', 'N/A')
                qty = float(t.get('securitiesTransacted', 0))
                price = float(t.get('price', 0))
                value = qty * price
                
                # Ownership Delta calculation
                post_shares = float(t.get('securitiesOwned', 0))
                pre_shares = post_shares - qty
                delta = (qty / pre_shares * 100) if pre_shares > 0 else 100

                results.append({
                    "Date": filing_date_str,
                    "Ticker": ticker,
                    "Insider": insider,
                    "Title": t.get('typeOfOwner', 'N/A'),
                    "Value ($)": value,
                    "Price": price,
                    "Qty": qty,
                    "Owned Post": post_shares,
                    "Δ Own": delta
                })
                
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"FMP API Error: {e}")
        return pd.DataFrame()

# 5. Logic & UI
df_raw = load_fmp_insider_data(lookback_days)

if not df_raw.empty:
    # Filter by user-selected whale threshold
    df = df_raw[df_raw['Value ($)'] >= whale_threshold].copy()
    
    if not df.empty:
        # Cluster Detection (2+ unique insiders buying the same ticker)
        clusters = df.groupby('Ticker')['Insider'].nunique()
        df['Signal'] = df['Ticker'].map(lambda x: "🔥 CLUSTER" if clusters[x] >= 2 else "🐋 WHALE")

        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Whale Buys", len(df))
        c2.metric("Total Capital Inflow", f"${df['Value ($)'].sum():,.0f}")
        c3.metric("Avg Buy Size", f"${df['Value ($)'].mean():,.0f}")

        # Visualization
        st.subheader(f"📑 Insider Activity (Last {lookback_days} Days)")
        
        # Style the dataframe
        styled_df = df.sort_values("Value ($)", ascending=False).style.format({
            "Value ($)": "${:,.0f}", 
            "Price": "${:,.2f}", 
            "Qty": "{:,.0f}", 
            "Owned Post": "{:,.0f}", 
            "Δ Own": "{:.1f}%"
        }).applymap(
            lambda x: 'background-color: #ff4b4b; color: white; font-weight: bold' if x == "🔥 CLUSTER" else '', 
            subset=['Signal']
        )
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.warning(f"No buys found above ${whale_threshold:,} in the last {lookback_days} days.")
else:
    st.info("Gathering data from FMP... If this takes too long, check your internet connection or API key.")

# 6. Refresh Button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
