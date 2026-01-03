import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. Dashboard Configuration
st.set_page_config(page_title="Eagle Eye: FMP Terminal", layout="wide")
st.title("🦅 Eagle Eye: Institutional Alpha Engine")

# 2. Setup API
# Using the key you provided
API_KEY = "YRByZglolMGVabAR6rOWHzeumPey2CBH"

# 3. Sidebar Pro-Filters
st.sidebar.header("🎯 Signal Sensitivity")
whale_threshold = st.sidebar.selectbox("Whale Threshold ($)", [100000, 250000, 500000, 1000000], index=1)
lookback_days = st.sidebar.slider("Lookback Period (Days)", 7, 90, 30)

# 4. Data Engine (Updated URL and Headers)
@st.cache_data(ttl=3600)
def load_fmp_insider_data(days):
    try:
        # FIX 1: Using the 'stable' path which is more reliable for new keys
        # URL: /stable/insider-trading/latest
        url = "https://financialmodelingprep.com/stable/insider-trading/latest"
        
        params = {
            "limit": 500,
            "apikey": API_KEY
        }
        
        # FIX 2: Added User-Agent header to prevent 403 Forbidden blocks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        # Detailed error handling for the 403
        if response.status_code == 403:
            st.error("🚫 403 Forbidden: Your API key may not have access to this endpoint or FMP is blocking the request. Verify your plan at site.financialmodelingprep.com")
            return pd.DataFrame()
            
        response.raise_for_status()
        trades = response.json()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        results = []
        
        for t in trades:
            # FMP Date parsing
            f_date_str = t.get('filingDate', '').split(' ')[0]
            if not f_date_str: continue
            f_date = datetime.strptime(f_date_str, '%Y-%m-%d').date()
            
            if f_date >= cutoff_date and t.get('transactionType') == 'P-Purchase':
                qty = float(t.get('securitiesTransacted', 0))
                price = float(t.get('price', 0))
                value = qty * price
                
                # Ownership Delta calculation
                post = float(t.get('securitiesOwned', 0))
                pre = post - qty
                delta = (qty / pre * 100) if pre > 0 else 100

                results.append({
                    "Date": f_date_str,
                    "Ticker": t.get('symbol', 'N/A'),
                    "Insider": t.get('reportingName', 'N/A'),
                    "Title": t.get('typeOfOwner', 'N/A'),
                    "Value ($)": value,
                    "Price": price,
                    "Qty": qty,
                    "Owned Post": post,
                    "Δ Own": delta
                })
                
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"Engine Error: {e}")
        return pd.DataFrame()

# 5. UI Presentation
df_raw = load_fmp_insider_data(lookback_days)

if not df_raw.empty:
    df = df_raw[df_raw['Value ($)'] >= whale_threshold].copy()
    
    if not df.empty:
        # Cluster Detection
        clusters = df.groupby('Ticker')['Insider'].nunique()
        df['Signal'] = df['Ticker'].map(lambda x: "🔥 CLUSTER" if clusters[x] >= 2 else "🐋 WHALE")

        # Top Level Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Whale Trades", len(df))
        m2.metric("Total Capital Inflow", f"${df['Value ($)'].sum():,.0f}")
        m3.metric("Max Position Increase", f"{df['Δ Own'].max():.1f}%")

        # Data Table
        st.subheader(f"📑 High-Conviction Buys (Last {lookback_days} Days)")
        st.dataframe(
            df.sort_values("Value ($)", ascending=False).style.format({
                "Value ($)": "${:,.0f}", "Price": "${:,.2f}", 
                "Qty": "{:,.0f}", "Owned Post": "{:,.0f}", "Δ Own": "{:.1f}%"
            }).applymap(lambda x: 'background-color: #ff4b4b; color: white' if x == "🔥 CLUSTER" else '', subset=['Signal']),
            use_container_width=True, hide_index=True
        )
    else:
        st.warning(f"No buys found above ${whale_threshold:,}. Try a lower threshold.")
else:
    st.info("No data returned. If the 403 error persists, check your FMP dashboard for plan restrictions.")

# 6. Refresh
if st.sidebar.button("🔄 Force Refresh"):
    st.cache_data.clear()
    st.rerun()
