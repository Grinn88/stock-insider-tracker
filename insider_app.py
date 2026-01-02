import streamlit as st
import pandas as pd
from sec_api import QueryApi
from datetime import datetime, timedelta
import time
import traceback

# -------------------------------
# STREAMLIT CONFIG
# -------------------------------
st.set_page_config(page_title="Insider Buy Tracker", layout="wide")
st.title("🦅 Insider Buying Dashboard")

# -------------------------------
# HARDCODED API KEY
# -------------------------------
SEC_API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=SEC_API_KEY)

# -------------------------------
# DATA FETCH FUNCTION
# -------------------------------
@st.cache_data(ttl=3600)
def fetch_insider_buys(days_back, min_value, max_results=200):

    now = datetime.utcnow()
    start_dt = now - timedelta(days=days_back)

    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")

    results = []
    offset = 0
    size = 50

    while offset < max_results:

        query_string = (
            'formType:"4" '
            f'AND filedAt:[{start_date} TO {end_date}]'
        )

        payload = {
            "query": {
                "query_string": {
                    "query": query_string
                }
            },
            "from": offset,
            "size": size,
            "sort": [{"filedAt": {"order": "desc"}}]
        }

        response = queryApi.get_filings(payload)
        filings = response.get("filings", [])

        if not filings:
