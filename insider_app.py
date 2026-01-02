import streamlit as st
import pandas as pd
import plotly.express as px
from sec_api import QueryApi

# 1. Page Configuration
st.set_page_config(page_title="Eagle Eye: Alpha Hunter", layout="wide")
st.title("🦅 Eagle Eye: Institutional Insider Terminal")

# 2. Config & API
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Sidebar: Advanced Controls
st.sidebar.header("🎯 Signal Sensitivity")
min_val = st.sidebar.number_input("Whale Threshold ($)", value=250000)
min_delta = st.sidebar.slider("Min % Position Change", 0, 100, 5)
lookback_days = st.sidebar.selectbox("Analysis Horizon", [30, 60, 90, 180], index=2)

# 4. Data Engine (Expanded for Heatmap & Pro Columns)
@st.cache_data(ttl=3600)
def load_alpha_data():
    try:
        query = {
            "query": f'formType:"4" AND filedAt:[now-{lookback_days}d TO now] AND "Purchase"',
            "from": "0", "size": "150", "sort": [{"filedAt": {"order": "desc"}}]
        }
        response = queryApi.get_filings(query)
        if not response.get('filings'): return pd.DataFrame()

        rows = []
        for f in response['filings']:
            # Industry/Sector data is often in the 'companyNames' or 'sic' fields
            # For this dashboard, we map Tickers to Sectors (Mock mapping for demo, 
            # in production use a Ticker-to-Sector API or CSV)
            sector_map = {"TSLA": "Tech", "AAPL": "Tech", "XOM": "Energy", "JPM": "Finance"} # Example
            
            txs = f.get('nonDerivativeTable', {}).get('transactions', [])
            for t in txs:
                if t.get('coding', {}).get('code') != 'P': continue
                
                qty = float(t.get('amounts', {}).get('shares', 0))
                price = float(t.get('amounts', {}).get('pricePerShare', 0))
                val = qty * price
                post_hold = float(t.get('postTransactionAmounts', {}).get('sharesOwnedFollowingTransaction', 0))
                
                # Pro Metric: Ownership Delta
                prev_hold = post_hold - qty
                delta_own = (qty / prev_hold * 100) if prev_hold > 0 else 100
                
                rows.append({
                    "Filing Date": f.get('filedAt', '')[:10],
                    "Trade Date": t.get('transactionDate', ''),
                    "Ticker": f.get('ticker'),
                    "Insider": f.get('reportingName'),
                    "Title": f.get('reportingOwnerRelationship', {}).get('officerTitle', 'Director'),
                    "Price": price,
                    "Qty": qty,
                    "Total Value": val,
                    "Shares Owned": post_hold,
                    "Δ Own": delta_own,
                    "Sector": sector_map.get(f.get('ticker'), "Other") # Sector Logic
                })

        df = pd.DataFrame(rows)
        if df.empty: return df

        # Cluster Detection (The Multi-Buyer Signal)
        counts = df.groupby('Ticker')['Insider'].nunique()
        df['Signal'] = df.apply(lambda x: "🔥 CLUSTER" if counts.get(x['Ticker'], 0) >= 2 else 
                                         ("🐋 WHALE" if x['Total Value'] >= min_val else "Normal"), axis=1)
        
        return df

    except Exception as e:
        st.error(f"Logic Error: {e}")
        return pd.DataFrame()

# 5. Dashboard Layout
df = load_alpha_data()

if not df.empty:
    # --- SECTION 1: SECTOR HEATMAP ---
    st.subheader("🌐 Insider Sector Heatmap")
    st.caption("Visualizing where the most money is flowing by Industry")
    
    heatmap_df = df.groupby('Sector').agg({'Total Value': 'sum', 'Ticker': 'count'}).reset_index()
    fig = px.treemap(heatmap_df, path=['Sector'], values='Total Value',
                     color='Total Value', color_continuous_scale='RdYlGn',
                     hover_data=['Ticker'])
    st.plotly_chart(fig, use_container_width=True)

    # --- SECTION 2: THE LEGIT TABLE ---
    st.divider()
    st.subheader("📑 The Institutional Master Table")
    
    # Filter for quality based on your sidebar inputs
    display_df = df[(df['Total Value'] >= 10000) & (df['Δ Own'] >= min_delta)]
    
    st.dataframe(
        display_df.sort_values("Total Value", ascending=False).style.format({
            "Price": "${:,.2f}", "Qty": "{:,.0f}", "Total Value": "${:,.0f}",
            "Shares Owned": "{:,.0f}", "Δ Own": "{:.1f}%"
        }).background_gradient(subset=['Δ Own'], cmap='Greens'),
        use_container_width=True, hide_index=True
    )
else:
    st.warning("No data found for the current filters.")

# --- SECTION 3: THE CHECKLIST FOR 90% SUCCESS ---
st.info("""
### 💡 How to Outperform the Market:
1. **The Delta Rule:** Ignore $1M buys from billionaires. Look for $100k buys from CFOs where **Δ Own is > 20%**.
2. **The Cluster Rule:** If you see 3+ insiders buying the same ticker on the Heatmap, the sector is likely reaching a bottom.
3. **The Date Gap:** Check 'Trade Date' vs 'Filing Date'. If they file within 1 hour of the trade, they want the public to see it—potentially a 'pump' signal. If they wait 2 days, they are trying to hide their accumulation.
""")
