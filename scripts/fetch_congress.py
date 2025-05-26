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


def fetch_bills_list_data(congress=None, bill_type=None, introduced_date=None):
    """Fetches a list of bills based on filters from the Congress API."""
    endpoint = "/bill"
    params = {}
    identifiers = {}

    if congress:
        params["congress"] = congress
        identifiers["congress"] = congress
    if bill_type:
        params["billType"] = bill_type
        identifiers["bill_type"] = bill_type
    if introduced_date:
        params["introducedDate"] = introduced_date
        identifiers["introduced_date"] = introduced_date
    
    # Ensure at least one filter is provided for bills list to avoid overly broad requests
    if not params:
        logging.error("At least one filter (--congress, --bill-type, --introduced-date) must be provided for the bills command.")
        sys.exit(1)

    data = make_congress_request(endpoint, params=params)
    if data:
        save_json(data, "bills_list", **identifiers)


def fetch_committee_data(chamber=None, congress=None, committee_code=None):
    """Fetches committee data from the Congress API."""
    endpoint = "/committee"
    params = {}
    identifiers = {}

    if chamber:
        params["chamber"] = chamber
        identifiers["chamber"] = chamber
    if congress:
        params["congress"] = congress
        identifiers["congress"] = congress
    if committee_code:
        # The API uses /{chamber}/{committeeCode} for specific committees if chamber and code are given
        # or /committee/{committeeCode} if only code is given (less common for specific lookup)
        # For listing with code as filter, it's just a parameter.
        # If we want to fetch a specific committee by its code, the endpoint structure might change.
        # Based on prompt, this is a filter for the /committee list endpoint.
        params["committeeCode"] = committee_code
        identifiers["committee_code"] = committee_code
    
    # Ensure at least one filter for committee data to avoid fetching all committees.
    if not params:
        logging.error("At least one filter (--chamber, --congress, --committee-code) must be provided for the committee command.")
        sys.exit(1)

    data = make_congress_request(endpoint, params=params)
    if data:
        save_json(data, "committee_data", **identifiers)


def fetch_amendment_data(congress=None, amendment_type=None):
    """Fetches amendment data from the Congress API."""
    endpoint = "/amendment"
    params = {}
    identifiers = {}

    if congress:
        params["congress"] = congress
        identifiers["congress"] = congress
    if amendment_type:
        params["amendmentType"] = amendment_type # API uses 'amendmentType'
        identifiers["amendment_type"] = amendment_type

    # Unlike other list endpoints, /amendment can be called without filters.
    # However, it's good practice to log if no filters are applied,
    # as this can result in a very large dataset.
    if not params:
        logging.info("Fetching all amendments as no filters were specified. This might be a large request.")

    data = make_congress_request(endpoint, params=params)
    if data:
        # If no identifiers, save_json will just use the prefix.
        # Create a default identifier if none exist to avoid just "amendment_data.json"
        if not identifiers:
            identifiers["all"] = "all"
        save_json(data, "amendment_data", **identifiers)


def fetch_committee_report_data(congress=None):
    """Fetches committee report data from the Congress API."""
    endpoint = "/committee-report"
    params = {}
    identifiers = {}

    if congress:
        params["congress"] = congress
        identifiers["congress"] = congress

    if not params:
        logging.info("Fetching all committee reports as no filters were specified. This might be a large request.")

    data = make_congress_request(endpoint, params=params)
    if data:
        if not identifiers:
            identifiers["all"] = "all"
        save_json(data, "committee_report_data", **identifiers)


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

    # Bills (list) subcommand
    bills_list_parser = subparsers.add_parser("bills", help="Fetch a list of bills based on filters.")
    bills_list_parser.add_argument(
        "--congress", type=int, help="Filter by Congress number (e.g., 117)."
    )
    bills_list_parser.add_argument(
        "--bill-type", type=str, help="Filter by type of bill (e.g., hr, s)."
    )
    bills_list_parser.add_argument(
        "--introduced-date", type=str, help="Filter by introduced date (YYYY-MM-DD)."
    )

    # Committee subcommand
    committee_parser = subparsers.add_parser("committee", help="Fetch committee data.")
    committee_parser.add_argument(
        "--chamber", type=str, help="Filter by chamber (e.g., house, senate)."
    )
    committee_parser.add_argument(
        "--congress", type=int, help="Filter by Congress number (e.g., 117)."
    )
    committee_parser.add_argument(
        "--committee-code", type=str, help="Filter by committee code (e.g., HSAG)."
    )

    # Amendment subcommand
    amendment_parser = subparsers.add_parser("amendment", help="Fetch amendment data.")
    amendment_parser.add_argument(
        "--congress", type=int, help="Filter by Congress number (e.g., 117)."
    )
    amendment_parser.add_argument(
        "--amendment-type",
        type=str,
        help="Filter by amendment type (e.g., hamdt, samdt).",
    )

    # Committee Report subcommand
    committee_report_parser = subparsers.add_parser(
        "committee-report", help="Fetch committee report data."
    )
    committee_report_parser.add_argument(
        "--congress", type=int, help="Filter by Congress number (e.g., 117)."
    )

    args = parser.parse_args()

    if args.command == "bill":
        fetch_bill_data(args.congress, args.bill_type, args.bill_number)
    elif args.command == "member":
        fetch_member_data(args.bioguide_id)
    elif args.command == "bills":
        fetch_bills_list_data(
            congress=args.congress,
            bill_type=args.bill_type,
            introduced_date=args.introduced_date,
        )
    elif args.command == "committee":
        fetch_committee_data(
            chamber=args.chamber,
            congress=args.congress,
            committee_code=args.committee_code,
        )
    elif args.command == "amendment":
        fetch_amendment_data(
            congress=args.congress, amendment_type=args.amendment_type
        )
    elif args.command == "committee-report":
        fetch_committee_report_data(congress=args.congress)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
