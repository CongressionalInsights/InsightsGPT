#!/usr/bin/env python3
import json
import os

import requests

# Federal Register API endpoint for agencies
AGENCIES_URL = "https://www.federalregister.gov/api/v1/agencies"


def main():
    print("Fetching agencies from Federal Register API...")
    response = requests.get(AGENCIES_URL)
    response.raise_for_status()

    agencies_data = response.json()  # should be a list of agencies
    print(f"Received {len(agencies_data)} agencies.")

    # Ensure 'data' directory exists
    os.makedirs("data", exist_ok=True)

    # Write to data/agencies.json with nice formatting
    output_path = os.path.join("data", "agencies.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(agencies_data, f, indent=2, ensure_ascii=False)

    print(f"Agencies data saved to {output_path}")


if __name__ == "__main__":
    main()
