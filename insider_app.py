import streamlit as st
import pandas as pd
from sec_api import QueryApi

# 1. Page Configuration
st.set_page_config(page_title="Pro Insider Screener", layout="wide")
st.title("🦅 Eagle Eye: Full-Screener Dashboard")

# 2. API Key Setup
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=API_KEY)

# 3. Sidebar Filtering
st.sidebar.header("Advanced Filters")
min_val = st.sidebar.slider("Min Trade Value ($)", 0, 1000000, 50000, step=50000)
if st.sidebar.button('🔄 Sync with SEC'):
    st.cache_data.clear()
    st.rerun()

# 4. Data Loader with OpenInsider Mapping
@st.cache_data(ttl=3600)
def load_and_map_data():
    try:
        # Querying for Open Market Purchases (Code P)
        search_query = 'formType:"4" AND filedAt:[now-300d TO now] AND "Purchase"'
        query = {"query": search_query, "from": "0", "size": "50", "sort": [{"filedAt": {"order": "desc"}}]}
        
        response = queryApi.get_filings(query)
        if not response.get('filings'): return pd.DataFrame()

        rows = []
        for f in response['filings']:
            ticker = f.get('ticker', 'N/A')
            insider = f.get('reportingName', 'Unknown')
            filed_date = f.get('filedAt', '')[:10]
            
            # Navigating to transaction table (Table I of Form 4)
            transactions = f.get('nonDerivativeTable', {}).get('transactions', [])
            for t in transactions:
                if t.get('coding', {}).get('code') != 'P': continue
                
                # Calculations
                shares = float(t.get('amounts', {}).get('shares', 0))
                price = float(t.get('amounts', {}).get('pricePerShare', 0))
                value = shares * price
                
                # Shares remaining (Post-transaction holdings)
                post_holdings = float(t.get('postTransactionAmounts', {}).get('sharesOwnedFollowingTransaction', 0))
                
                # Change % (How much did they increase their position?)
                prev_holdings = post_holdings - shares
                own_change = (shares / prev_holdings * 100) if prev_holdings > 0 else 100
                
                # Check for 10b5-1 (Pre-planned)
                is_planned = "Yes" if "10b5-1" in str(f.get('remarks', '')).lower() else "No"

                rows.append({
                    "Filing Date": filed_date,
                    "Ticker": ticker,
                    "Insider Name": insider,
                    "Shares": f"{shares:,.0f}",
                    "Price": f"${price:,.2f}",
                    "Value ($)": value,
                    "Owned Post": f"{post_holdings:,.0f}",
                    "ΔOwn": f"{own_change:.1f}%",
                    "10b5-1": is_planned
                })

        df = pd.DataFrame(rows)
        if df.empty: return df
        
        # Add Cluster Logic
        cluster_counts = df.groupby('Ticker')['Insider Name'].nunique()
        df['Signal'] = df['Ticker'].apply(lambda x: "🔥 CLUSTER" if cluster_counts.get(x, 0) >= 3 else "")
        
        return df[df['Value ($)'] >= min_val].sort_values('Value ($)', ascending=False)

    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# 5. Dashboard View
df_final = load_and_map_data()
if not df_final.empty:
    # Formatting Value for display
    display_df = df_final.copy()
    display_df['Value ($)'] = display_df['Value ($)'].apply(lambda x: f"${x:,.0f}")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.warning("No data matches your current 'Min Trade Value' filter.")
