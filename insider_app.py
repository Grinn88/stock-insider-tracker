import streamlit as st
import pandas as pd
from sec_api import QueryApi

st.set_page_config(page_title="Eagle Eye Dashboard", layout="wide")
st.title("🦅 Eagle Eye: Insider Tracker")

# Use Streamlit Secrets for the API Key
if "SEC_API_KEY" in st.secrets:
    API_KEY = st.secrets["SEC_API_KEY"]
else:
    st.error("Please add SEC_API_KEY to Streamlit Secrets.")
    st.stop()

queryApi = QueryApi(api_key=API_KEY)

@st.cache_data(ttl=3600)
def load_data():
    query = {
        "query": "formType:\"4\" AND nonDerivativeTable.transactions.coding.code:P AND filedAt:[now-300d TO now]",
        "from": "0", "size": "50", "sort": [{"filedAt": {"order": "desc"}}]
    }
    response = queryApi.get_filings(query)
    return pd.DataFrame(response['filings'])

df = load_data()
if not df.empty:
    st.success(f"Loaded {len(df)} recent transactions.")
    st.dataframe(df[['ticker', 'reportingName', 'filedAt']], use_container_width=True)