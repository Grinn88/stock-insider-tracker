import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import smtplib
from email.message import EmailMessage
from collections import defaultdict
from datetime import datetime

# CONFIGURATION
SEC_CONTACT = "rohansofra81@gmail.com"
HEADERS = {"User-Agent": f"EagleEye Research ({SEC_CONTACT})"}

def get_trade_value(xml_link):
    """Parses the actual SEC XML for the dollar amount."""
    try:
        xml_url = xml_link.replace("-index.htm", ".xml").replace("ix?doc=/Archives", "/Archives")
        resp = requests.get(xml_url, headers=HEADERS, timeout=5)
        root = ET.fromstring(resp.content)
        total = 0
        for trans in root.findall(".//nonDerivativeTransaction"):
            code = trans.find(".//transactionCode")
            if code is not None and code.text == 'P': # 'P' for Purchase
                shares = float(trans.find(".//transactionShares/value").text or 0)
                price = float(trans.find(".//transactionPricePerShare/value").text or 0)
                total += (shares * price)
        return total
    except: return 0

def run_tracker():
    # 1. Fetch from SEC Atom Feed
    rss_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&start=0&count=100&output=atom"
    response = requests.get(rss_url, headers=HEADERS)
    root = ET.fromstring(response.content)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}

    all_trades = []
    ticker_groups = defaultdict(list)

    for entry in root.findall('atom:entry', ns):
        title = entry.find('atom:title', ns).text
        link = entry.find('atom:link', ns).attrib['href']
        try:
            parts = title.split(' - ')
            ticker = parts[1]
            insider = parts[2].split(' (')[0]
            val = get_trade_value(link)
            
            trade = {"Date": datetime.now().strftime("%Y-%m-%d"), "Ticker": ticker, "Insider": insider, "Value": val, "Link": link}
            all_trades.append(trade)
            ticker_groups[ticker].append(trade)
        except: continue

    # 2. Whale & Cluster Email Prompt
    email_content = ""
    for ticker, trades in ticker_groups.items():
        total_ticker_value = sum(t['Value'] for t in trades)
        is_whale = total_ticker_value >= 250000
        is_cluster = len(trades) >= 2
        
        if is_whale or is_cluster:
            header = "🐋 WHALE ALERT " if is_whale else ""
            header += "🔥 CLUSTER " if is_cluster else ""
            email_content += f"{header}\nTicker: {ticker}\nTotal Value: ${total_ticker_value:,.0f}\n"
            for t in trades:
                email_content += f"- {t['Insider']} (${t['Value']:,.0f})\n"
            email_content += f"Link: {trades[0]['Link']}\n\n"

    if email_content:
        send_email(email_content)

    # 3. Save to CSV for the Dashboard
    pd.DataFrame(all_trades).to_csv("latest_trades.csv", index=False)

def send_email(body):
    msg = EmailMessage()
    msg['Subject'] = "🚨 Eagle Eye: High-Conviction Signal"
    msg['From'] = SEC_CONTACT
    msg['To'] = SEC_CONTACT
    msg.set_content(body)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SEC_CONTACT, os.environ.get('EMAIL_PASSWORD'))
        smtp.send_message(msg)

if __name__ == "__main__":
    run_tracker()
