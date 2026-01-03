import streamlit as st
import pandas as pd

st.set_page_config(page_title="Eagle Eye Dashboard", layout="wide")
st.title("🦅 Eagle Eye: Insider Terminal")

# SECURE DATA LINK: Use your actual GitHub username/repo
GITHUB_USER = "YOUR_USERNAME" 
REPO_NAME = "YOUR_REPO"
URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/latest_trades.csv"

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(URL)

try:
    df = load_data()
    df['Value'] = pd.to_numeric(df['Value'])
    
    # Whale & Cluster Highlights
    whales = df[df['Value'] >= 250000]
    clusters = df.groupby('Ticker').filter(lambda x: len(x) >= 2)

    st.subheader("🐋 Whales & 🔥 Clusters")
    st.dataframe(pd.concat([whales, clusters]).drop_duplicates(), use_container_width=True)
    
    st.divider()
    st.subheader("All Recent Filings")
    st.dataframe(df, use_container_width=True)

except:
    st.warning("Dashboard is syncing... check GitHub Actions for status.")
