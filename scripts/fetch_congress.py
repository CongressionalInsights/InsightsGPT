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

def fetch_member_data(
    bioguide_id=None,
    congress=None,
    state_code=None,
    district=None,
    sponsorship=None,
    cosponsorship=None,
):
    """Fetches member data from the Congress API based on filters."""
    endpoint = "/member"  # Changed from /member/{bioguideId}
    params = {}
    identifiers = {}

    if bioguide_id:
        params["bioguideId"] = bioguide_id
        identifiers["bioguide_id"] = bioguide_id
    if congress:
        params["congress"] = congress
        identifiers["congress"] = congress
    if state_code:
        params["stateCode"] = state_code
        identifiers["state_code"] = state_code
    if district:
        params["district"] = district
        identifiers["district"] = district
    if sponsorship: # Will be True if --sponsorship is used
        params["sponsorship"] = "true" # API expects string "true" or "false"
        identifiers["sponsorship"] = "true"
    if cosponsorship: # Will be True if --cosponsorship is used
        params["cosponsorship"] = "true"
        identifiers["cosponsorship"] = "true"

    # If bioguide_id is not provided, at least one other filter must be present.
    # If no filters at all, exit.
    if not params:
        logging.error(
            "No filters provided for member command. Please provide at least one filter."
        )
        sys.exit(1)
    
    if not bioguide_id and len(params) == 0 : # This condition is now covered by 'if not params:'
        # This specific check for bioguide_id being None and no other params is slightly redundant
        # if the general 'if not params' check is in place.
        # However, to be explicit about the original requirement:
        # "if bioguide_id is NOT provided, at least one of the other filters MUST be provided"
        # This is equivalent to: if (not bioguide_id) and (all other filters are also None), then error.
        # The current 'if not params:' handles the case where *nothing* is provided.
        # Let's refine to ensure if bioguide_id is None, other params must exist.
        pass # The `if not params` above handles the "no filters at all" case.
             # The prompt's logic is: if bioguide_id is None, then (congress or state_code or district or sponsorship or cosponsorship) must be true.
             # This is equivalent to: if not bioguide_id and not (any other filter), then error.
             # This is also covered by 'if not params' if bioguide_id is the ONLY potential filter that could have been specified.
             # The current structure of adding to params and then checking `if not params` is sufficient.

    data = make_congress_request(endpoint, params=params)
    if data:
        if not identifiers: # Should not happen due to the 'if not params' check above
            identifiers["all_members_unfiltered_should_not_happen"] = "true" 
        save_json(data, "member_data", **identifiers)


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


def fetch_treaty_data(congress=None):
    """Fetches treaty data from the Congress API."""
    endpoint = "/treaty"
    params = {}
    identifiers = {}

    if congress:
        params["congress"] = congress
        identifiers["congress"] = congress

    if not params:
        logging.info("Fetching all treaties as no filters were specified. This might be a large request.")

    data = make_congress_request(endpoint, params=params)
    if data:
        if not identifiers:
            identifiers["all"] = "all"
        save_json(data, "treaty_data", **identifiers)


def fetch_nomination_data(congress):
    """Fetches nomination data for a specific congress from the Congress API."""
    # The /nomination/{congress} endpoint requires congress as part of the path.
    # It does not take additional query parameters according to typical API patterns for this type of endpoint.
    endpoint = f"/nomination/{congress}"
    identifiers = {"congress": congress}

    # Log the action, as this fetches all nominations for a given congress.
    logging.info(f"Fetching all nominations for Congress {congress}.")

    data = make_congress_request(endpoint) # No 'params' needed for this specific endpoint structure
    if data:
        save_json(data, "nomination_data", **identifiers)


def fetch_congressional_record_data(congress=None, date=None):
    """Fetches congressional record data from the Congress API."""
    endpoint = "/congressional-record"
    params = {}
    identifiers = {}

    if congress:
        params["congress"] = congress
        identifiers["congress"] = congress
    if date:
        params["date"] = date # API likely uses 'date' or similar
        identifiers["date"] = date

    if not params:
        logging.info("Fetching all congressional records as no filters were specified. This might be a large request.")

    data = make_congress_request(endpoint, params=params)
    if data:
        if not identifiers:
            identifiers["all"] = "all"
        save_json(data, "congressional_record_data", **identifiers)


def fetch_senate_communication_data(
    congress=None, communication_type=None, from_date=None, to_date=None
):
    """Fetches senate communication data from the Congress API."""
    endpoint = "/senate-communication"
    params = {}
    identifiers = {}

    if congress:
        params["congress"] = congress
        identifiers["congress"] = congress
    if communication_type:
        params["type"] = communication_type  # API uses 'type'
        identifiers["type"] = communication_type
    if from_date:
        params["fromDateTime"] = f"{from_date}T00:00:00Z" # API uses fromDateTime and toDateTime
        identifiers["from_date"] = from_date
    if to_date:
        params["toDateTime"] = f"{to_date}T23:59:59Z"
        identifiers["to_date"] = to_date


    if not params:
        logging.info(
            "Fetching all senate communications as no filters were specified. This might be a large request."
        )

    data = make_congress_request(endpoint, params=params)
    if data:
        if not identifiers:
            identifiers["all"] = "all"
        save_json(data, "senate_communication_data", **identifiers)


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
    member_parser = subparsers.add_parser("member", help="Fetch member data by various filters.")
    member_parser.add_argument(
        "--bioguide-id",
        type=str,
        # required=True, # Changed to optional
        help="Filter by Biographical Directory ID of the member.",
    )
    member_parser.add_argument(
        "--congress", type=int, help="Filter by Congress number (e.g., 117)."
    )
    member_parser.add_argument(
        "--state-code", type=str, help="Filter by state code (e.g., CA, TX)."
    )
    member_parser.add_argument(
        "--district", type=int, help="Filter by congressional district number."
    )
    member_parser.add_argument(
        "--sponsorship",
        action="store_true",
        help="Include member's bill sponsorship information.",
    )
    member_parser.add_argument(
        "--cosponsorship",
        action="store_true",
        help="Include member's bill cosponsorship information.",
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

    # Treaty subcommand
    treaty_parser = subparsers.add_parser("treaty", help="Fetch treaty data.")
    treaty_parser.add_argument(
        "--congress", type=int, help="Filter by Congress number (e.g., 117)."
    )

    # Nomination subcommand
    nomination_parser = subparsers.add_parser(
        "nomination", help="Fetch nomination data for a specific Congress."
    )
    nomination_parser.add_argument(
        "--congress",
        type=int,
        required=True,
        help="Specify the Congress number (e.g., 117). This is required.",
    )

    # Congressional Record subcommand
    congressional_record_parser = subparsers.add_parser(
        "congressional-record", help="Fetch congressional record data."
    )
    congressional_record_parser.add_argument(
        "--congress", type=int, help="Filter by Congress number (e.g., 117)."
    )
    congressional_record_parser.add_argument(
        "--date", type=str, help="Filter by date (YYYY-MM-DD)."
    )

    # Senate Communication subcommand
    senate_communication_parser = subparsers.add_parser(
        "senate-communication", help="Fetch Senate communication data."
    )
    senate_communication_parser.add_argument(
        "--congress", type=int, help="Filter by Congress number (e.g., 117)."
    )
    senate_communication_parser.add_argument(
        "--type",
        type=str,
        choices=["ec", "pm"],
        help="Filter by communication type (ec: Executive Communication, pm: Presidential Message).",
    )
    senate_communication_parser.add_argument(
        "--from-date",
        type=str,
        help="Filter by start date (YYYY-MM-DD).",
    )
    senate_communication_parser.add_argument(
        "--to-date", type=str, help="Filter by end date (YYYY-MM-DD)."
    )


    args = parser.parse_args()

    if args.command == "bill":
        fetch_bill_data(args.congress, args.bill_type, args.bill_number)
    elif args.command == "member":
        fetch_member_data(
            bioguide_id=args.bioguide_id,
            congress=args.congress,
            state_code=args.state_code,
            district=args.district,
            sponsorship=args.sponsorship,
            cosponsorship=args.cosponsorship,
        )
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
    elif args.command == "treaty":
        fetch_treaty_data(congress=args.congress)
    elif args.command == "nomination":
        fetch_nomination_data(congress=args.congress)
    elif args.command == "congressional-record":
        fetch_congressional_record_data(
            congress=args.congress, date=args.date
        )
    elif args.command == "senate-communication":
        fetch_senate_communication_data(
            congress=args.congress,
            communication_type=args.type, # argparse uses 'type'
            from_date=args.from_date,
            to_date=args.to_date,
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
