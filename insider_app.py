import streamlit as st
import pandas as pd

# 🛑 CONFIGURATION - PLEASE VERIFY THESE CAREFULLY
USER = "GRIN88"
REPO = "stock-insider-tracker"  # <--- Change this if your repo folder name is different!

# This URL uses the "Raw" format which is the ONLY way Streamlit can read the file
RAW_URL = f"https://github.com/Grinn88/stock-insider-tracker/edit/main/insider_app.py"

st.set_page_config(page_title="Eagle Eye Dashboard", layout="wide")
st.title("🦅 Eagle Eye: Insider Terminal")

@st.cache_data(ttl=60)
def load_data():
    try:
        # We add a random number to the URL to force GitHub to send the newest version
        timestamp_url = f"{RAW_URL}?nocache={pd.Timestamp.now().timestamp()}"
        return pd.read_csv(timestamp_url)
    except Exception as e:
        return None

df = load_data()

if df is not None:
    st.success("✅ Dashboard Connected!")
    
    # Simple formatting: Highlight big trades
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    st.dataframe(df.sort_values(by="Value", ascending=False), use_container_width=True)
else:
    st.error("🚨 Data Link Broken")
    st.write(f"Streamlit is trying to find the data here: `{RAW_URL}`")
    st.info("If that link looks wrong, please check your REPO name in the code above.")
