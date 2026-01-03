import os
import requests
import xml.etree.ElementTree as ET
import smtplib
from email.message import EmailMessage
from collections import defaultdict

# SEC Identity (Required)
SEC_HEADERS = {"User-Agent": "EagleEye Tracker (rohansofra81@gmail.com)"}

def get_transaction_value(xml_url):
    """Parses the actual Form 4 XML to find the dollar value."""
    try:
        resp = requests.get(xml_url, headers=SEC_HEADERS)
        root = ET.fromstring(resp.content)
        
        total_value = 0
        # Search for non-derivative transactions (Open Market Buys)
        for trans in root.findall(".//nonDerivativeTransaction"):
            # 'P' stands for Purchase
            code = trans.find(".//transactionCode")
            if code is not None and code.text == 'P':
                shares = float(trans.find(".//transactionShares/value").text or 0)
                price = float(trans.find(".//transactionPricePerShare/value").text or 0)
                total_value += (shares * price)
        return total_value
    except:
        return 0

def run_whale_tracker():
    rss_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&start=0&count=40&output=atom"
    feed = requests.get(rss_url, headers=SEC_HEADERS).text
    root = ET.fromstring(feed)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}

    ticker_buys = defaultdict(list)
    
    for entry in root.findall('atom:entry', ns):
        title = entry.find('atom:title', ns).text
        # Extract Ticker from: "4 - AAPL - Cook Tim"
        ticker = title.split(' - ')[1]
        link = entry.find('atom:link', ns).attrib['href']
        
        # Form 4 links to a landing page; we need the .xml file link
        # Simplified for this example: convert HTML link to XML link
        xml_link = link.replace("-index.htm", ".xml").replace("ix?doc=/Archives", "/Archives")
        
        value = get_transaction_value(xml_link)
        if value > 0:
            ticker_buys[ticker].append({
                "insider": title.split(' - ')[2].split(' (')[0],
                "value": value,
                "link": link
            })

    # Prepare Alert Body
    email_body = ""
    for ticker, trades in ticker_buys.items():
        is_cluster = len(trades) >= 2
        total_ticker_value = sum(t['value'] for t in trades)
        
        prefix = ""
        if is_cluster: prefix += "🔥 CLUSTER "
        if total_ticker_value > 250000: prefix += "🐋 WHALE ALERT "
        
        if prefix:
            email_body += f"{prefix}\nTicker: {ticker}\nTotal Value: ${total_ticker_value:,.20f}\n"
            for t in trades:
                email_body += f"- {t['insider']} bought ${t['value']:,.0f}\n"
            email_body += f"Link: {trades[0]['link']}\n\n"

    if email_body:
        send_email(email_body)

def send_email(content):
    msg = EmailMessage()
    msg['Subject'] = "🚨 HIGH CONVICTION: Insider Whale/Cluster Detected"
    msg['From'] = "rohansofra81@gmail.com"
    msg['To'] = "rohansofra81@gmail.com"
    msg.set_content(content)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login("rohansofra81@gmail.com", os.environ.get('EMAIL_PASSWORD'))
        smtp.send_message(msg)

if __name__ == "__main__":
    run_whale_tracker()
