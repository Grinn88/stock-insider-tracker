import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION ---
SEC_CONTACT = "rohansofra81@gmail.com" # Required by SEC for fair access
WHALE_LIMIT = 250000

st.set_page_config(page_title="Eagle Eye Free", layout="wide")
st.title("🦅 Eagle Eye: Whale & Cluster Tracker")

# --- DATA ENGINE ---
@st.cache_data(ttl=600)
def get_sec_data():
    # Direct Atom Feed (Always Free)
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&start=0&count=100&output=atom"
    
    # CRITICAL: These specific headers prevent the "403 Forbidden" error
    headers = {
        "User-Agent": f"EagleEye Research ({SEC_CONTACT})",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        results = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text
            # Format usually: "4 - TICKER - NAME (CIK)"
            try:
                parts = title.split(' - ')
                ticker = parts[1]
                insider = parts[2].split(' (')[0]
                link = entry.find('atom:link', ns).attrib['href']
                date = entry.find('atom:updated', ns).text[:10]
                
                results.append({
                    "Date": date,
                    "Ticker": ticker,
                    "Insider": insider,
                    "Link": link
                })
            except: continue
            
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"SEC Access Error: {e}")
        return pd.DataFrame()

# --- DASHBOARD UI ---
df = get_sec_data()

if not df.empty:
    # 1. Cluster Detection
    ticker_counts = df.groupby('Ticker').size()
    clusters = ticker_counts[ticker_counts >= 2].index.tolist()
    
    st.sidebar.header("Filter Results")
    show_clusters = st.sidebar.toggle("Show Only Clusters 🔥", value=False)
    
    display_df = df.copy()
    if show_clusters:
        display_df = display_df[display_df['Ticker'].isin(clusters)]

    # 2. Key Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Filings", len(df))
    c2.metric("Clusters Detected", len(clusters))
    c3.metric("Last Update", datetime.now().strftime("%H:%M"))

    # 3. Data Table
    st.subheader("Live Insider Feed")
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("No data returned. The SEC might be rate-limiting the Streamlit Cloud IP. Try refreshing in 5 minutes.")
