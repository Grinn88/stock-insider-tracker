import os
import pandas as pd
from sec_api import QueryApi
import smtplib
from email.message import EmailMessage

# 1. Setup (Secrets from GitHub, Email hard-coded)
API_KEY = os.environ.get('SEC_API_KEY')
SENDER_PASSWORD = os.environ.get('EMAIL_PASSWORD')
SENDER_EMAIL = "rohansofra81@gmail.com"
RECEIVER_EMAIL = "rohansofra81@gmail.com"

queryApi = QueryApi(api_key=API_KEY)

def check_insiders():
    # Query for Form 4 (Purchases) in the last 24 hours
    query = {
        "query": "formType:\"4\" AND nonDerivativeTable.transactions.coding.code:P AND filedAt:[now-1d TO now]",
        "from": "0", "size": "10", "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    response = queryApi.get_filings(query)
    filings = response.get('filings', [])

    if filings:
        msg = EmailMessage()
        msg['Subject'] = f"🚨 {len(filings)} New Insider Trades Detected"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        
        content = "Recent Insider Purchases:\n\n"
        for f in filings:
            content += f"Ticker: {f['ticker']} | Insider: {f['reportingName']} | Date: {f['filedAt']}\n"
        
        msg.set_content(content)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print("Email sent successfully!")
    else:
        print("No new trades found.")

if __name__ == "__main__":
    check_insiders()