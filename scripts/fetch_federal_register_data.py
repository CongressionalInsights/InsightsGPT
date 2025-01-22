
import requests
import json

def fetch_executive_orders(date):
    BASE_URL = "https://www.federalregister.gov/api/v1/documents"
    params = {
        "conditions[type]": "Executive Order",
        "conditions[publication_date]": date,
        "per_page": 100,
        "order": "relevance",
        "fields[]": ["title", "document_number", "url", "publication_date"]
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching data:", response.status_code, response.text)
        return {}

if __name__ == "__main__":
    date = "2023-01-01"  # Specify the date here
    data = fetch_executive_orders(date)
    with open(f"executive_orders_{date}.json", "w") as file:
        json.dump(data, file, indent=2)
    print(f"Data for {date} saved to executive_orders_{date}.json")
