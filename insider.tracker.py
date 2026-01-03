import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import smtplib
from email.message import EmailMessage
from collections import defaultdict

# SEC Identity (Required)
SEC_CONTACT = "rohansofra81@gmail.com"
HEADERS = {"User-Agent": f"EagleEye Research ({SEC_CONTACT})"}

def get_trade_value(xml_link):
    """Deep-dives into the XML to find the actual $ amount."""
    try:
        # Convert HTML link to Raw XML link
        xml_url = xml_link.replace("-index.htm", ".xml").replace("ix?doc=/Archives", "/Archives")
        resp = requests.get(xml_url, headers=HEADERS, timeout=5)
        root = ET.fromstring(resp.content)
        total = 0
        for trans in root.findall(".//nonDerivativeTransaction"):
            code = trans.find(".//transactionCode")
            # 'P' = Purchase
            if code is not None and code.text == 'P':
                shares = float(trans.find(".//transactionShares/value").text or 0)
                price = float(trans.find(".//transactionPricePerShare/value").text or 0)
                total += (shares * price)
        return total
    except: return 0

def run_workflow():
    # 1. Fetch Latest 50 Filings
    rss_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&start=0&count=50&output=atom"
    response = requests.get(rss_url, headers=HEADERS)
    root = ET.fromstring(response.content)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}

    ticker_buys = defaultdict(list)
    raw_data = []

    for entry in root.findall('atom:entry', ns):
        title = entry.find('atom:title', ns).text
        link = entry.find('atom:link', ns).attrib['href']
        date = entry.find('atom:updated', ns).text[:10]
        
        try:
            parts = title.split(' - ')
            ticker = parts[1]
            insider = parts[2].split(' (')[0]
            
            value = get_trade_value(link)
            
            trade_info = {
                "Date": date, "Ticker": ticker, "Insider": insider,
                "Value": value, "Link": link
            }
            raw_data.append(trade_info)
            if value > 0:
                ticker_buys[ticker].append(trade_info)
        except: continue

    # 2. Email Prompt Logic (Whales & Clusters)
    email_body = ""
    for ticker, trades in ticker_buys.items():
        total_v = sum(t['Value'] for t in trades)
        is_whale = total_v >= 250000
        is_cluster = len(trades) >= 2
        
        if is_whale or is_cluster:
            tag = "🐋 WHALE " if is_whale else ""
            tag += "🔥 CLUSTER " if is_cluster else ""
            email_body += f"{tag}\nTicker: {ticker}\nTotal: ${total_v:,.0f}\n"
            for t in trades:
                email_body += f"- {t['Insider']} bought ${t['Value']:,.0f}\n"
            email_body += f"View: {trades[0]['Link']}\n\n"

    if email_body:
        send_email(email_body)

    # 3. Save for Dashboard
    pd.DataFrame(raw_data).to_csv("latest_trades.csv", index=False)

def send_email(content):
    msg = EmailMessage()
    msg['Subject'] = "🚨 EAGLE EYE: High-Conviction Trades Detected"
    msg['From'] = SEC_CONTACT
    msg['To'] = SEC_CONTACT
    msg.set_content(content)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SEC_CONTACT, os.environ.get('EMAIL_PASSWORD'))
        smtp.send_message(msg)

if __name__ == "__main__":
    run_workflow()
