import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime

SEC_CONTACT = "rohansofra81@gmail.com"

def fetch_and_save():
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&start=0&count=100&output=atom"
    headers = {"User-Agent": f"EagleEye Research ({SEC_CONTACT})"}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        data = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text
            parts = title.split(' - ')
            if len(parts) >= 3:
                data.append({
                    "Date": entry.find('atom:updated', ns).text[:10],
                    "Ticker": parts[1],
                    "Insider": parts[2].split(' (')[0],
                    "Link": entry.find('atom:link', ns).attrib['href']
                })
        
        # Save to CSV in the repo
        df = pd.DataFrame(data)
        df.to_csv("latest_trades.csv", index=False)
        print(f"✅ Saved {len(df)} trades to CSV.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fetch_and_save()
