import json

REQUEST_TIMEOUT = 10  # seconds
import os

REQUEST_TIMEOUT = 10  # seconds

import requests

REQUEST_TIMEOUT = 10  # seconds


def fetch_executive_orders(date):
    BASE_URL = "https://www.federalregister.gov/api/v1/documents"
    params = {
        "conditions[type]": "Executive Order",
        "conditions[publication_date]": date,
        "per_page": 100,
        "order": "relevance",
        "fields[]": ["title", "document_number", "url", "publication_date"],
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)

        # Enhanced logging for debugging
        print(f"Request URL: {response.url}")
        print(f"Status Code: {response.status_code}")

        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()

        # Log the full response for debugging
        print("API Response:", json.dumps(data, indent=2))

        # Save data to file if results are found
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
    test_date = "2023-01-01"  # Replace with a relevant test date
    fetch_executive_orders(test_date)
