import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# -------------------------------
# STREAMLIT SETUP
# -------------------------------
st.set_page_config(page_title="Insider Buy Dashboard", layout="wide")
st.title("🦅 Insider Buying Dashboard (SEC EDGAR)")

SEC_URL = "https://efts.sec.gov/LATEST/search-index"

HEADERS = {
    "User-Agent": "Rohan Sofra rohan@email.com"
}

# -------------------------------
# FETCH FILINGS (SAFE PAGINATION)
# -------------------------------
@st.cache_data(ttl=3600)
def fetch_insider_buys(days=30, min_value=250000, max_results=200):
    size = 50
    offset = 0
    rows = []

    while offset < max_results:
        payload = {
            "q": 'formType:"4" AND transactionCode:"P"',
            "from": offset,
            "size": size,
            "sort": [{"filedAt": {"order": "desc"}}]
        }

        r = requests.post(SEC_URL, headers=HEADERS, json=payload)
        if r.status_code != 200:
            st.error(f"SEC API error: {r.text}")
            break

        data = r.json()
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            break

        for h in hits:
            src = h["_source"]

            try:
                shares = float(src.get("transactionShares", 0))
                price = float(src.get("transactionPricePerShare", 0))
                value = shares * price
            except:
                continue

            if value < min_value:
                continue

            rows.append({
                "Filed Date": src.get("filedAt", "")[:10],
                "Ticker": src.get("ticker"),
                "Company": src.get("companyName"),
                "Insider Name": src.get("insiderName"),
                "Insider Title": src.get("insiderTitle"),
                "Transaction Type": src.get("transactionCode"),
                "Shares Bought": int(shares),
                "Price ($)": round(price, 2),
                "Value ($)": round(value, 0),
                "Ownership Type": src.get("ownershipType"),
                "10b5-1 Plan": "Yes" if "10b5" in str(src).lower() else "No"
            })

        offset += size
        time.sleep(0.15)

    return pd.DataFrame(rows)


# -------------------------------
# SIDEBAR CONTROLS
# -------------------------------
st.sidebar.header("Filters")

days = st.sidebar.selectbox("Lookback Window", [7, 30, 60, 90])
min_trade = st.sidebar.selectbox(
    "Minimum Buy Value",
    [100000, 250000, 500000, 1000000]
)

if st.sidebar.button("Load Insider Buys"):
    with st.spinner("Fetching insider buys from SEC…"):
        df = fetch_insider_buys(days, min_trade)

    if df.empty:
        st.warning("No qualifying insider buys found.")
    else:
        st.success(f"Found {len(df)} insider buys")

        st.dataframe(
            df.sort_values("Value ($)", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        # Summary
        st.subheader("Quick Signals")
        st.write(
            df.groupby("Ticker")
              .agg(
                  Total_Value=("Value ($)", "sum"),
                  Buy_Count=("Ticker", "count")
              )
              .sort_values("Total_Value", ascending=False)
        )
