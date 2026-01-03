import streamlit as st
import pandas as pd

st.set_page_config(page_title="Eagle Eye Dashboard", layout="wide")
st.title("🦅 Eagle Eye: Insider Terminal")

# 🛑 REPLACE THESE WITH YOUR INFO
USER = "Grinn88"
REPO = "stock-insider-tracker"
URL = f"https://github.com/Grinn88/stock-insider-tracker/edit/main/insider_app.py"

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(URL)

try:
    df = load_data()
    st.success(f"Connected to SEC Relay (Last Update: {df['Date'].iloc[0]})")
    
    # Logic for filters
    whales = df[df['Value'] >= 250000]
    clusters = df.groupby('Ticker').filter(lambda x: len(x) >= 2)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🐋 Whales ($250k+)")
        st.dataframe(whales, use_container_width=True)
    with c2:
        st.subheader("🔥 Insider Clusters")
        st.dataframe(clusters, use_container_width=True)

    st.divider()
    st.subheader("All Recent Activity")
    st.dataframe(df, use_container_width=True)

except:
    st.error("Waiting for Data... Ensure your GitHub Action has run successfully at least once.")
