
import requests
import json
import os

def fetch_executive_orders(date):
    BASE_URL = "https://www.federalregister.gov/api/v1/documents"
    params = {
        "conditions[type]": "Executive Order",
        "conditions[publication_date]": date,
        "per_page": 100,
        "order": "relevance",
        "fields[]": ["title", "document_number", "url", "publication_date"]
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # Log API response for debugging
        print("API Response:", data)

        # Save to data folder if results exist
        if data.get("results"):
            os.makedirs("data", exist_ok=True)
            file_name = f"data/executive_orders_{date}.json"
            with open(file_name, "w") as file:
                json.dump(data, file, indent=2)
            print(f"Data saved to {file_name}")
        else:
            print("No results found for the specified date.")

    except requests.exceptions.RequestException as e:
        print(f"API error: {e}")

if __name__ == "__main__":
    test_date = "2023-01-01"  # Example test date
    fetch_executive_orders(test_date)
