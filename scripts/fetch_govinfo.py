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
API_BASE = "https://api.govinfo.gov"
REQUEST_TIMEOUT = 10
DATA_DIR = "data/govinfo"
GOVINFO_API_KEY = os.environ.get("GOVINFO_API_KEY")

def save_json(data, file_prefix, sub_dir=None, **identifiers):
    """
    Saves the given data as a JSON file.

    The filename is constructed using the file_prefix and identifiers.
    Example: save_json(data, "collection_details", sub_dir="collections", collectionCode="BILLS")
             will save to "data/govinfo/collections/collection_details_BILLS.json"
    """
    current_data_dir = DATA_DIR
    if sub_dir:
        current_data_dir = os.path.join(DATA_DIR, sub_dir)

    os.makedirs(current_data_dir, exist_ok=True)

    # Construct the filename
    identifier_str = "_".join(str(value) for value in identifiers.values() if value is not None)
    if not identifier_str: # Handle case where no identifiers are provided beyond prefix
        filename = f"{file_prefix}.json"
    else:
        filename = f"{file_prefix}_{identifier_str}.json"
    
    filepath = os.path.join(current_data_dir, filename)

    # Save the data
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        logging.info(f"Successfully saved data to {filepath}")
    except IOError as e:
        logging.error(f"Error saving data to {filepath}: {e}")
        # Consider if sys.exit(1) is appropriate here or if errors should be propagated
        # For now, adhering to the pattern in fetch_congress.py which does exit.
        sys.exit(1)


def make_govinfo_request(endpoint_path, params=None):
    """Makes a GET request to the GovInfo API."""
    if not GOVINFO_API_KEY:
        logging.error("GOVINFO_API_KEY environment variable not set.")
        sys.exit(1)

    request_params = params.copy() if params else {}
    request_params['api_key'] = GOVINFO_API_KEY

    url = f"{API_BASE}{endpoint_path}"
    logging.info(f"Fetching data from {url} with params {request_params}") # Log with api_key for debugging, consider redacting in prod

    try:
        response = requests.get(
            url, params=request_params, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        # GovInfo API sometimes returns non-JSON content for errors even with 200,
        # or might return 200 but with an internal error structure.
        # For now, assuming direct JSON or raise_for_status handles it.
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error fetching data from {url}: {e}")
        logging.error(f"Response status: {e.response.status_code}")
        try:
            logging.error(f"Response content: {e.response.text}")
        except Exception:
            logging.error("Could not retrieve response content for HTTPError.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data from {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response from {url}: {e}")
        logging.error(f"Response content that failed to parse: {response.text if 'response' in locals() else 'N/A'}")
        return None

# --- API Call Functions ---

def fetch_collections_data(args=None): # args is unused for this specific function but good for consistency
    """Fetches the list of all available GovInfo collections."""
    logging.info("Fetching list of all GovInfo collections.")
    data = make_govinfo_request("/collections")
    if data:
        save_json(data, "collections_list") # Filename will be collections_list.json
    else:
        logging.error("Failed to fetch collections list.")


def fetch_packages_data(args):
    """Fetches packages from GovInfo API based on provided filters."""
    logging.info(f"Fetching packages with filters: {args}")
    params = {}
    identifiers = {}

    if args.collection:
        params["collection"] = args.collection
        identifiers["collection"] = args.collection.replace(",", "_") # Make filename friendly
    if args.start_date:
        params["dateIssuedStartDate"] = args.start_date
        identifiers["start_date"] = args.start_date
    if args.end_date:
        params["dateIssuedEndDate"] = args.end_date
        identifiers["end_date"] = args.end_date
    if args.modified_since:
        params["modifiedSince"] = args.modified_since
        identifiers["modified_since"] = args.modified_since.replace(":", "").replace("-","") # Filename friendly
    if args.page_size is not None: # Check for None as 0 is a valid page size in some APIs (though not here)
        params["pageSize"] = args.page_size
        # identifiers["page_size"] = args.page_size # Often not needed in filename for list results
    if args.offset_mark:
        params["offsetMark"] = args.offset_mark
        # identifiers["offset_mark"] = args.offset_mark # Often not needed in filename

    data = make_govinfo_request("/packages", params=params)
    if data:
        # Use a specific sub-directory for packages if desired, or save to DATA_DIR
        save_json(data, "packages_list", sub_dir="packages", **identifiers)
    else:
        logging.error(f"Failed to fetch packages for filters: {identifiers}")


def fetch_package_summary_data(args):
    """Fetches the summary for a specific package from GovInfo API."""
    if not args.package_id:
        logging.error("Package ID is required for fetching a package summary.")
        sys.exit(1)

    package_id = args.package_id
    logging.info(f"Fetching summary for package ID: {package_id}")
    
    endpoint_path = f"/packages/{package_id}/summary"
    
    data = make_govinfo_request(endpoint_path)
    if data:
        # Construct a filename-friendly version of package_id for the identifier key
        # and for the subdirectory name.
        safe_package_id_for_filename = package_id.replace("-", "_").replace(".", "_")
        sub_dir_name = package_id # Use original package_id for subdir to match intent
        
        save_json(
            data, 
            "package_summary", 
            sub_dir=f"summaries/{sub_dir_name}", 
            package_id=safe_package_id_for_filename # Identifier for the JSON filename itself
        )
    else:
        logging.error(f"Failed to fetch summary for package ID: {package_id}")


def main():
    """Main function to parse arguments and call the appropriate functions."""
    parser = argparse.ArgumentParser(description="Fetch data from the GovInfo API.")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    # Ensure subparsers are required if using Python < 3.7, but 'required=True' in add_subparsers is for 3.7+
    # For broader compatibility, one might check sys.version_info or rely on the default behavior 
    # which makes a subcommand required if no default is set for the parser itself.
    # Setting dest and making it required is a common pattern.
    subparsers.required = True


    # Collections subcommand
    collections_parser = subparsers.add_parser(
        "collections", help="Fetch the list of all available GovInfo collections."
    )
    collections_parser.set_defaults(func=fetch_collections_data)

    # Packages subcommand
    packages_parser = subparsers.add_parser(
        "packages", help="Fetch packages from GovInfo, with optional filters."
    )
    packages_parser.add_argument(
        "--collection",
        type=str,
        help="Filter by collection code(s), comma-separated for multiple (e.g., BILLS,FR)."
    )
    packages_parser.add_argument(
        "--start-date",
        type=str,
        help="Filter by start date for dateIssued (YYYY-MM-DD)."
    )
    packages_parser.add_argument(
        "--end-date",
        type=str,
        help="Filter by end date for dateIssued (YYYY-MM-DD)."
    )
    packages_parser.add_argument(
        "--modified-since",
        type=str,
        help="Filter by modified date (ISO8601 format, e.g., 2023-01-01T00:00:00Z)."
    )
    packages_parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Number of results per page (default: 100, max: 1000)."
    )
    packages_parser.add_argument(
        "--offset-mark",
        type=str,
        default="*",
        help="Offset mark for pagination (default: '*')."
    )
    packages_parser.set_defaults(func=fetch_packages_data)

    # Package Summary subcommand
    summary_parser = subparsers.add_parser(
        "package-summary", help="Fetch the summary for a specific GovInfo package."
    )
    summary_parser.add_argument(
        "--package-id",
        type=str,
        required=True,
        help="The ID of the package (e.g., FR-2023-01-03-0001)."
    )
    summary_parser.set_defaults(func=fetch_package_summary_data)


    args = parser.parse_args()

    logging.info(f"Command: {args.command}")
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        # This case should ideally not be reached if subparsers.required = True and subcommands define set_defaults
        # or if a default function is set for the main parser.
        # However, as a fallback or for commands not yet using set_defaults:
        logging.warning(f"No function associated with command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
