import streamlit as st
import pandas as pd
from sec_api import QueryApi
from datetime import datetime, timedelta
import os

# --------------------------------------------------
# 1. APP CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Eagle Eye – Insider Whale Tracker",
    layout="wide"
)

st.title("🦅 Eagle Eye: Insider Whale Tracker")

# --------------------------------------------------
# 2. API SETUP (SECURE)
# --------------------------------------------------
API_KEY = os.getenv("SEC_API_KEY")

if not API_KEY:
    st.error("❌ SEC_API_KEY not found. Set it as an environment variable.")
    st.stop()

queryApi = QueryApi(api_key=API_KEY)

# --------------------------------------------------
# 3. DATA FETCH (CACHED)
# --------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_insider_buys(days_back: int, min_value: int) -> pd.DataFrame:
    start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end_date = datetime.utcnow().strftime("%Y-%m-%d")

    lucene_query = f'''
        formType:"4"
        AND filedAt:[{start_date} TO {end_date}]
    '''

    payload = {
        "query": lucene_query,
        "from": 0,
        "size": 300,
        "sort": [{"filedAt": {"order": "desc"}}]
    }

    try:
        response = queryApi.get_filings(payload)
    except Exception as e:
        st.error(f"SEC API error: {e}")
        return pd.DataFrame()

    filings = response.get("filings", [])
    rows = []

    for filing in filings:
        ticker = filing.get("ticker")
        insider = filing.get("reportingName")
        filed_date = filing.get("filedAt", "")[:10]

        role_info = filing.get("reportingOwnerRelationship", {})
        role = (
            role_info.get("officerTitle")
            if role_info.get("isOfficer")
            else "Director" if role_info.get("isDirector") else "Other"
        )

        transactions = filing.get("nonDerivativeTable", {}).get("transactions", [])
        if not transactions:
            continue

        for tx in transactions:
            if tx.get("coding", {}).get("code") != "P":
                continue

            amounts = tx.get("amounts", {})
            shares = float(amounts.get("shares", 0))
            price = float(amounts.get("pricePerShare", 0))
            value = shares * price

            if value < min_value:
                continue

            rows.append({
                "Date": filed_date,
                "Ticker": ticker,
                "Insider": insider,
                "Role": role,
                "Shares": int(shares),
                "Price": round(price, 2),
                "Value ($)": round(value, 0)
            })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # --------------------------------------------------
    # 4. CLUSTER LOGIC (REAL SIGNAL)
    # --------------------------------------------------
    df["Cluster Size"] = df.groupby("Ticker")["Insider"].transform("nunique")
    df["Cluster Buy"] = df["Cluster Size"] >= 2

    return df

# --------------------------------------------------
# 5. SIDEBAR CONTROLS
# --------------------------------------------------
st.sidebar.header("🎯 Insider Filters")

lookback = st.sidebar.selectbox("Lookback (days)", [30, 60, 90], index=0)
min_trade = st.sidebar.selectbox(
    "Minimum Trade Value ($)",
    [150_000, 250_000, 500_000, 1_000_000],
    index=1
)

# --------------------------------------------------
# 6. EXECUTION
# --------------------------------------------------
df = fetch_insider_buys(lookback, min_trade)

# --------------------------------------------------
# 7. OUTPUT
# --------------------------------------------------
if df.empty:
    st.warning("No qualifying insider purchases found. This is normal for high-signal filters.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Total Buys", len(df))
col2.metric("Unique Tickers", df["Ticker"].nunique())
col3.metric("Cluster Buys", df[df["Cluster Buy"]]["Ticker"].nunique())

st.subheader("📊 Insider Purchases (Sorted by Conviction)")

st.dataframe(
    df.sort_values(
        by=["Cluster Buy", "Value ($)"],
        ascending=[False, False]
    ),
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Note: Empty periods are expected. Insider conviction events are rare by design."
)
