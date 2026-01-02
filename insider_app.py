import streamlit as st
import pandas as pd
from sec_api import QueryApi

st.set_page_config(page_title="Eagle Eye Dashboard", layout="wide")
st.title("🦅 Eagle Eye: Insider Tracker")

# Hardcoded API Key (Bypassing Streamlit Secrets)
API_KEY = "c2464017fedbe1b038778e4947735d9aeb9ef2b78b9a5ca3e122a6b8f792bf9c"

queryApi = QueryApi(api_key=API_KEY)

@st.cache_data(ttl=3600)
def load_data():
    try:
        query = {
            "query": "formType:\"4\" AND nonDerivativeTable.transactions.coding.code:P AND filedAt:[now-300d TO now]",
            "from": "0", "size": "50", "sort": [{"filedAt": {"order": "desc"}}]
        }
        response = queryApi.get_filings(query)
        return pd.DataFrame(response['filings'])
    except Exception as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

# Show a loading spinner
with st.spinner('Grabbing data from SEC...'):
    df = load_data()

if not df.empty:
    st.success(f"Loaded {len(df)} recent transactions.")
    # Use dataframe for better performance/scrolling
    st.dataframe(df[['ticker', 'reportingName', 'filedAt']], use_container_width=True)
else:
    st.warning("No data found. Check the 'Manage App' logs to see the error.")