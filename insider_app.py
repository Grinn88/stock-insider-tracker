import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

st.set_page_config(page_title="Eagle Eye: Free Terminal", layout="wide")
st.title("🦅 Eagle Eye: Institutional Alpha Engine")
st.caption("Direct SEC EDGAR Feed (100% Free & Unlimited)")

# 1. Sidebar - SEC Compliance Requirement
st.sidebar.header("🛡️ SEC Access Identity")
user_email = st.sidebar.text_input("Your Email (Required by SEC)", "rohansofra81@gmail.com")

# 2. Free Data Engine
@st.cache_data(ttl=600) # Refresh every 10 mins
def fetch_sec_feed(email):
    # Public SEC feed for all Form 4s (Insider Trades)
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&start=0&count=100&output=atom"
    headers = {"User-Agent": f"EagleEye Tracker ({email})"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        data = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text
            # Format: "4 - TICKER - Insider Name"
            parts = title.split(' - ')
            if len(parts) >= 3:
                ticker = parts[1]
                insider = parts[2].split(' (')[0]
                date = entry.find('atom:updated', ns).text[:10]
                link = entry.find('atom:link', ns).attrib['href']
                
                data.append({
                    "Date": date,
                    "Ticker": ticker,
                    "Insider": insider,
                    "Link": link
                })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"SEC Feed Error: {e}")
        return pd.DataFrame()

# 3. UI logic
if user_email:
    df = fetch_sec_feed(user_email)
    if not df.empty:
        st.subheader("🔥 Latest Insider Filings (Real-Time)")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Quick filter
        search = st.text_input("🔍 Filter by Ticker (e.g. TSLA, NVDA)")
        if search:
            st.write(df[df['Ticker'].str.contains(search.upper())])
    else:
        st.warning("No data found or SEC blocked the request. Ensure email is valid.")
