import requests
import time

SEC_ENDPOINT = "https://data.sec.gov/submissions/CIK0000000000.json"
HEADERS = {
    "User-Agent": "YourName your@email.com"
}

def fetch_insider_filings(query_url, max_results=200):
    results = []
    size = 50  # HARD LIMIT
    offset = 0

    while offset < max_results:
        params = {
            "size": size,
            "from": offset
        }

        response = requests.get(query_url, headers=HEADERS, params=params)

        if response.status_code != 200:
            raise Exception(f"SEC API error {response.status_code}: {response.text}")

        data = response.json()

        filings = data.get("hits", {}).get("hits", [])
        if not filings:
            break

        results.extend(filings)
        offset += size

        # SEC rate-limit protection
        time.sleep(0.2)

    return results


# 🔹 Example OpenInsider-style query
QUERY_URL = (
    "https://efts.sec.gov/LATEST/search-index"
    "?q=formType:\"4\" AND transactionCode:\"P\""
)

insider_buys = fetch_insider_filings(QUERY_URL, max_results=200)

print(f"Pulled {len(insider_buys)} insider buy filings")
