import os
import requests
import xml.etree.ElementTree as ET
import smtplib
from email.message import EmailMessage

# Configuration
SEC_EMAIL = "rohansofra81@gmail.com" # Identify yourself to SEC
SENDER_EMAIL = "rohansofra81@gmail.com"
SENDER_PASS = os.environ.get('EMAIL_PASSWORD')

def run_free_tracker():
    # 1. Fetch from SEC RSS
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&start=0&count=40&output=atom"
    headers = {"User-Agent": f"InsiderBot ({SEC_EMAIL})"}
    
    response = requests.get(url, headers=headers)
    root = ET.fromstring(response.content)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    signals = []
    for entry in root.findall('atom:entry', ns):
        title = entry.find('atom:title', ns).text
        link = entry.find('atom:link', ns).attrib['href']
        signals.append(f"• {title}\nLink: {link}\n")

    if signals:
        # 2. Send Email
        msg = EmailMessage()
        msg['Subject'] = f"🚨 Eagle Eye: {len(signals)} New Insider Filings"
        msg['From'] = SENDER_EMAIL
        msg['To'] = SENDER_EMAIL
        msg.set_content("The following insiders just filed Form 4s with the SEC:\n\n" + "\n".join(signals))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASS)
            smtp.send_message(msg)
        print("✅ Free SEC Alert Sent!")

if __name__ == "__main__":
    run_free_tracker()
