#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
CONGRESS_API_BASE_URL = "https://api.congress.gov/v3"
REQUEST_TIMEOUT = 10
CONGRESS_API_KEY = os.environ.get("CONGRESS_API_KEY")

# --- Helper Functions ---

def save_json(data, file_prefix, **identifiers):
    """
    Saves the given data as a JSON file.

    The filename is constructed using the file_prefix and identifiers.
    Example: save_json(data, "bill", congress=117, bill_type="hr", bill_number=2617)
             will save to "data/congress/bill_117_hr_2617.json"
    """
    if not CONGRESS_API_KEY:
        logging.error("CONGRESS_API_KEY environment variable not set.")
        sys.exit(1)

    # Create the data/congress directory if it doesn't exist
    data_dir = "data/congress"
    os.makedirs(data_dir, exist_ok=True)

    # Construct the filename
    identifier_str = "_".join(str(value) for value in identifiers.values())
    filename = f"{file_prefix}_{identifier_str}.json"
    filepath = os.path.join(data_dir, filename)

    # Save the data
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        logging.info(f"Successfully saved data to {filepath}")
    except IOError as e:
        logging.error(f"Error saving data to {filepath}: {e}")
        sys.exit(1)


def make_congress_request(endpoint, params=None):
    """Makes a GET request to the Congress API."""
    if not CONGRESS_API_KEY:
        logging.error("CONGRESS_API_KEY environment variable not set.")
        sys.exit(1)

    headers = {"x-api-key": CONGRESS_API_KEY}
    url = f"{CONGRESS_API_BASE_URL}{endpoint}"
    logging.info(f"Fetching data from {url} with params {params}")

    try:
        response = requests.get(
            url, headers=headers, params=params, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data from {url}: {e}")
        sys.exit(1)

# --- API Call Functions ---

def fetch_bill_data(congress, bill_type, bill_number):
    """Fetches bill data from the Congress API."""
    endpoint = f"/bill/{congress}/{bill_type}/{bill_number}"
    data = make_congress_request(endpoint)
    if data:
        save_json(
            data,
            "bill",
            congress=congress,
            bill_type=bill_type,
            bill_number=bill_number,
        )

def fetch_member_data(bioguide_id):
    """Fetches member data from the Congress API."""
    endpoint = f"/member/{bioguide_id}"
    data = make_congress_request(endpoint)
    if data:
        save_json(data, "member", bioguide_id=bioguide_id)


# --- Main Function ---
def main():
    """Main function to parse arguments and call the appropriate functions."""
    parser = argparse.ArgumentParser(description="Fetch data from the Congress API.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Bill subcommand
    bill_parser = subparsers.add_parser("bill", help="Fetch bill data.")
    bill_parser.add_argument(
        "--congress", type=int, required=True, help="Congress number (e.g., 117)."
    )
    bill_parser.add_argument(
        "--bill-type",
        type=str,
        required=True,
        help="Type of bill (e.g., hr, s, hres).",
    )
    bill_parser.add_argument(
        "--bill-number", type=int, required=True, help="Bill number."
    )

    # Member subcommand
    member_parser = subparsers.add_parser("member", help="Fetch member data.")
    member_parser.add_argument(
        "--bioguide-id",
        type=str,
        required=True,
        help="Biographical Directory ID of the member.",
    )

    args = parser.parse_args()

    if args.command == "bill":
        fetch_bill_data(args.congress, args.bill_type, args.bill_number)
    elif args.command == "member":
        fetch_member_data(args.bioguide_id)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
