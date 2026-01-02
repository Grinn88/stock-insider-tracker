import os
import pandas as pd
from sec_api import QueryApi
import smtplib
from email.message import EmailMessage
from collections import defaultdict

# 1. Setup (Using GitHub Secrets)
API_KEY = os.environ.get('SEC_API_KEY')
SENDER_PASSWORD = os.environ.get('EMAIL_PASSWORD') 
SENDER_EMAIL = "rohansofra81@gmail.com"
RECEIVER_EMAIL = "rohansofra81@gmail.com"

queryApi = QueryApi(api_key=API_KEY)

def hunt_signals():
    # Query for Form 4 Purchases (Code P) in the last 24 hours
    query = {
        "query": "formType:\"4\" AND filedAt:[now-1d TO now] AND \"Purchase\"",
        "from": "0", "size": "100", "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    response = queryApi.get_filings(query)
    filings = response.get('filings', [])
    
    whale_alerts = []
    ticker_buyers = defaultdict(set) # To track unique buyers per ticker
    ticker_details = {} # To store data for the email

    for f in filings:
        ticker = f.get('ticker')
        insider = f.get('reportingName')
        
        # Navigate to transaction details
        transactions = f.get('nonDerivativeTable', {}).get('transactions', [])
        for t in transactions:
            if t.get('coding', {}).get('code') == 'P':
                qty = float(t.get('amounts', {}).get('shares', 0))
                price = float(t.get('amounts', {}).get('pricePerShare', 0))
                value = qty * price
                
                # Update Cluster tracker
                ticker_buyers[ticker].add(insider)
                ticker_details[ticker] = {"date": f['filedAt'][:10], "value": value}
                
                # Check for Whale ($250k+)
                if value >= 250000:
                    whale_alerts.append(f"🐋 WHALE: {ticker} | {insider} | ${value:,.0f}")

    # Identify Clusters (2+ unique buyers)
    cluster_alerts = []
    for ticker, buyers in ticker_buyers.items():
        if len(buyers) >= 2:
            cluster_alerts.append(f"🔥 CLUSTER: {ticker} ({len(buyers)} insiders buying) | Last buy: {ticker_details[ticker]['date']}")

    # 3. Send Email if any signal found
    if whale_alerts or cluster_alerts:
        msg = EmailMessage()
        msg['Subject'] = f"🚨 Insider Signal: {len(whale_alerts)} Whales | {len(cluster_alerts)} Clusters"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        
        body = "Eagle Eye Alert Report:\n\n"
        if whale_alerts:
            body += "--- WHALES ($250k+) ---\n" + "\n".join(whale_alerts) + "\n\n"
        if cluster_alerts:
            body += "--- CLUSTERS (2+ Insiders) ---\n" + "\n".join(cluster_alerts)
        
        msg.set_content(body)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print("Alert email sent successfully!")
    else:
        print("No significant whales or clusters found.")

if __name__ == "__main__":
    hunt_signals()
