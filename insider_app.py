import streamlit as st
import pandas as pd
from sec_api import QueryApi
from datetime import datetime, timedelta
import pytz
import os

# -------------------------
# 1. APP CONFIG
# -------------------------
st.set_page_config(
    page_title="Eagle Eye: Insider Whales",
    layout="wide"
)

# -------------------------
# 2. API SETUP (SECURE)
# -------------------------
API_KEY = os.getenv("SEC_API_KEY")
if not API_KEY:
    st.error("SEC_API_KEY not found. Set it as an environment variable.")
    st.stop()

queryApi = QueryApi(api_key=API_KEY)

# -------------------------
# 3. CACHE LAYER (CREDIT SHIELD)
# -------------------------
@st.cache_data(ttl=3600)
def fetch_insider_data(days_back: int, min_value: int) -> pd.DataFrame:
    start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    end_date = datetime.utcnow().strftime('%Y-%m-%d')

    lucene_query = (
        'formType:"4" AND '
        'nonDerivativeTable.transactions.coding.code:P AND '
        'filedAt:[{start} TO {end}]'
    ).format(start=start_date, end=end_date)

    payload = {
        "query": lucene_query,
        "from": 0,
        "size": 200,
        "sort": [{"filedAt": {"order": "desc"}}]
    }

    try:
        response = queryApi.get_filings(payload)
    except Exception as e:
        st.error(f"SEC API error: {e}")
        return pd.DataFrame()

    rows = []

    for filing in response.get("filings", []):
        insider_name = filing.get("reportingName")
        ticker = filing.get("ticker")
        filed_date = filing.get("filedAt", "")[:10]

        # Role filtering (HIGH SIGNAL)
        role = filing.get("reportingOwnerRelationship", {})
        if not any([
            role.get("isDirector"),
            role.get("isOfficer")
        ]):
            continue

        title = role.get("officerTitle", "")

        txs = filing.get("nonDerivativeTable", {}).get("transactions", [])
        for tx in txs:
            amounts = tx.get("amounts", {})
            shares = float(amounts.get("shares", 0))
            price = float(amounts.get("pricePerShare", 0))
            value = shares * price

            if value < min_value:
                continue

            rows.append({
                "Date": filed_date,
                "Ticker": ticker,
                "Insider": insider_name,
                "Role": title if title else "Director",
                "Shares": int(shares),
                "Price": round(price, 2),
                "Value ($)": round(value, 0),
                "10b5-1": tx.get("coding", {}).get("footnoteId") is not None
            })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # -------------------------
    # 4. CLUSTER LOGIC (EDGE)
    # -------------------------
    cluster_counts = df.groupby("Ticker")["Insider"].nunique()
    df["Cluster Size"] = df["Ticker"].map(cluster_counts)

    df["Cluster Flag"] = df["Cluster Size"] >= 2

    return df

# -------------------------
# 5. SIDEBAR CONTROLS
# -------------------------
st.sidebar.header("🛡 Insider Filters")

lookback = st.sidebar.selectbox("Lookback Window (days)", [30, 60, 90])
min_trade = st.sidebar.selectbox("Minimum Trade Value ($)", [250_000, 500_000, 1_000_000])

# -------------------------
# 6. EXECUTION
# -------------------------
df = fetch_insider_data(lookback, min_trade)

# -------------------------
# 7. UI OUTPUT
# -------------------------
st.title("🦅 Insider Whale Dashboard")

if df.empty:
    st.warning("No qualifying insider purchases found.")
else:
    st.metric(
        "Unique Tickers",
        df["Ticker"].nunique()
    )
    st.metric(
        "Cluster Buys",
        df[df["Cluster Flag"]]["Ticker"].nunique()
    )

    st.dataframe(
        df.sort_values(["Cluster Flag", "Value ($)"], ascending=[False, False]),
        use_container_width=True,
        hide_index=True
    )
