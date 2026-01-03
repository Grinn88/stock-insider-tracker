import os
import requests
import smtplib
from email.message import EmailMessage
from collections import defaultdict

# 1. Setup (Using GitHub Secrets)
API_KEY = os.environ.get('FMP_API_KEY') # Updated name for clarity
SENDER_PASSWORD = os.environ.get('EMAIL_PASSWORD') 
SENDER_EMAIL = "rohansofra81@gmail.com"
RECEIVER_EMAIL = "rohansofra81@gmail.com"

def hunt_signals():
    # FMP Endpoint for latest insider trades
    # We pull the last 100 trades to ensure coverage between runs
    url = f"https://financialmodelingprep.com/api/v4/insider-trading?limit=100&apikey={API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        trades = response.json()
    except Exception as e:
        print(f"❌ API Error: {e}")
        return

    whale_alerts = []
    ticker_buyers = defaultdict(set)
    ticker_details = {}

    for t in trades:
        # FMP uses 'P-Purchase' for open market buys
        if t.get('transactionType') == 'P-Purchase':
            ticker = t.get('symbol')
            insider = t.get('reportingName')
            qty = float(t.get('securitiesTransacted', 0))
            price = float(t.get('price', 0))
            value = qty * price
            date = t.get('filingDate', '')[:10]
            
            # Track Clusters (Unique buyers per ticker)
            ticker_buyers[ticker].add(insider)
            ticker_details[ticker] = {"date": date, "value": value}
            
            # Identify Whales ($250k+)
            if value >= 250000:
                whale_alerts.append(f"🐋 WHALE: {ticker} | {insider} | ${value:,.0f} (at ${price:.2f})")

    # Filter for Clusters (2+ unique buyers)
    cluster_alerts = []
    for ticker, buyers in ticker_buyers.items():
        if len(buyers) >= 2:
            cluster_alerts.append(f"🔥 CLUSTER: {ticker} ({len(buyers)} insiders buying) | Latest: {ticker_details[ticker]['date']}")

    # 3. Send Email
    if whale_alerts or cluster_alerts:
        msg = EmailMessage()
        msg['Subject'] = f"🚨 Insider Signal: {len(whale_alerts)} Whales | {len(cluster_alerts)} Clusters"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        
        body = "Eagle Eye FMP Alert Report:\n\n"
        if whale_alerts:
            body += "--- WHALES ($250k+) ---\n" + "\n".join(whale_alerts) + "\n\n"
        if cluster_alerts:
            body += "--- CLUSTERS (2+ Insiders) ---\n" + "\n".join(cluster_alerts)
        
        msg.set_content(body)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print("✅ Alert email sent successfully via FMP!")
    else:
        print("No significant activity found in this run.")

if __name__ == "__main__":
    hunt_signals()
