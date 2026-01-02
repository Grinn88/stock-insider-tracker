import streamlit as st
import pandas as pd
from sec_api import QueryApi
from datetime import datetime, timedelta
import time
import traceback

# ---------------------------------
# STREAMLIT SETUP
# ---------------------------------
st.set_page_config(page_title="Insider Buy Dashboard", layout="wide")
st.title("🦅 Insider Buying Dashboard")

# ---------------------------------
# HARDCODED API KEY (AS REQUESTED)
# ---------------------------------
SEC_API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"
queryApi = QueryApi(api_key=SEC_API_KEY)

# ---------------------------------
# DATA FETCHER (SAFE + PAGINATED)
# ---------------------------------
@st.cache_data(ttl=3600)
def fetch_insider_buys(days_back=30, min_value=250000, max_results=200):
    start = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end = datetime.utcnow().strftime("%Y-%m-%d")

    rows = []
    offset = 0
    size = 50

    while offset < max_results:
        query = {
            "query": {
                "query_string": {
                    "query": f'formType:"4" AND filedAt:[{start} TO {end}]'
                }
            },
            "from": offset,
            "size": size,
            "sort": [{"filedAt": {"order": "desc"}}]
