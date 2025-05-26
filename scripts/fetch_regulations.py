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
API_BASE = "https://api.regulations.gov/v4"
REQUEST_TIMEOUT = 10
DATA_DIR = "data/regulations"

REGULATIONS_API_KEY = os.environ.get("REGULATIONS_API_KEY")

if not REGULATIONS_API_KEY:
    logging.error("REGULATIONS_API_KEY environment variable not set. Please set it in your .env file or environment.")
    sys.exit(1)

def save_json(data, file_prefix, sub_dir=None, **identifiers):
    """
    Saves the given data as a JSON file.

    The filename is constructed using the file_prefix and identifiers.
    Example: save_json(data, "document_details", sub_dir="documents", documentId="XYZ-123")
             will save to "data/regulations/documents/document_details_XYZ-123.json"
    """
    current_data_dir = DATA_DIR
    if sub_dir:
        current_data_dir = os.path.join(DATA_DIR, sub_dir)

    os.makedirs(current_data_dir, exist_ok=True)

    # Construct the filename from identifiers, filtering out None values
    identifier_parts = [f"{key}_{value}" for key, value in identifiers.items() if value is not None]
    if identifier_parts:
        identifier_str = "_".join(identifier_parts)
        filename = f"{file_prefix}_{identifier_str}.json"
    else: # Handle case where no identifiers are provided beyond prefix
        filename = f"{file_prefix}.json"
    
    filepath = os.path.join(current_data_dir, filename)

    # Save the data
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        logging.info(f"Successfully saved data to {filepath}")
    except IOError as e:
        logging.error(f"Error saving data to {filepath}: {e}")
        sys.exit(1)


def make_regulations_request(endpoint_path, params=None):
    """Makes a GET request to the Regulations.gov API."""
    # Redundant check as it's checked at module load, but good for defense in depth
    if not REGULATIONS_API_KEY:
        logging.error("REGULATIONS_API_KEY is not available. Cannot make API request.")
        sys.exit(1)

    headers = {
        "X-Api-Key": REGULATIONS_API_KEY,
        "Accept": "application/vnd.api+json" # Common for JSON:API
    }
    
    url = f"{API_BASE}{endpoint_path}"
    # Log request without headers for security (API key in header)
    logging.info(f"Fetching data from {url} with params {params}")

    try:
        response = requests.get(
            url, params=params, headers=headers, timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code != 200:
            logging.error(f"API request failed with status {response.status_code}: {response.text}")
            return None
            
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during API request to {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response from {url}: {e}")
        logging.error(f"Response content that failed to parse: {response.text if 'response' in locals() else 'N/A'}")
        return None

# --- API Call Functions ---

def fetch_documents_data(args):
    """Fetches documents from Regulations.gov API based on provided filters."""
    logging.info(f"Fetching documents with filters: {args}")
    params = {}
    identifiers = {}

    if args.search_term:
        params["filter[searchTerm]"] = args.search_term
        identifiers["searchTerm"] = args.search_term.replace(" ", "_") # Filename friendly
    if args.docket_id:
        params["filter[docketId]"] = args.docket_id
        identifiers["docketId"] = args.docket_id
    if args.title_filter:
        params["filter[title]"] = args.title_filter
        identifiers["title"] = args.title_filter.replace(" ", "_")
    
    # Page size and number
    if args.page_size is not None:
        # Basic validation, though argparse could do more with custom types/choices
        if not 1 <= args.page_size <= 100:
            logging.warning("Page size must be between 1 and 100. Using default of 25.")
            params["page[size]"] = 25
        else:
            params["page[size]"] = args.page_size
        # identifiers["pageSize"] = params["page[size]"] # Often not needed for list results filenames
    
    if args.page_number is not None:
        if args.page_number < 1:
            logging.warning("Page number must be 1 or greater. Using default of 1.")
            params["page[number]"] = 1
        else:
            params["page[number]"] = args.page_number
        # identifiers["pageNumber"] = params["page[number]"] # Often not needed for list results filenames

    data = make_regulations_request("/documents", params=params)
    if data:
        save_json(data, "documents_list", sub_dir="documents", **identifiers)
    else:
        logging.error(f"Failed to fetch documents for filters: {identifiers}")


def fetch_single_document_data(args):
    """Fetches a single document by its ID from Regulations.gov API."""
    if not args.document_id: # Should be caught by argparse 'required=True'
        logging.error("Document ID is required for fetching a single document.")
        sys.exit(1)

    document_id = args.document_id
    logging.info(f"Fetching document: {document_id}")
    
    endpoint_path = f"/documents/{document_id}"
    params = {}
    identifiers = {"documentId": document_id} # Primary identifier for filename

    if args.include_attachments:
        params["include"] = "attachments"
        identifiers["attachments"] = "true" # Add to filename if attachments are included

    data = make_regulations_request(endpoint_path, params=params if params else None)
    
    if data:
        # Create a filename-safe version of document_id.
        # Regulations.gov document IDs can contain hyphens, which are fine for filenames.
        # If they could contain slashes or other problematic chars, more cleaning would be needed.
        # For now, assuming hyphens are okay and no other special chars are typical.
        safe_document_id_for_path = document_id 
        
        # Save in a subdirectory named after the document_id itself for organization
        save_json(
            data, 
            "document_details", 
            sub_dir=f"documents/{safe_document_id_for_path}", 
            **identifiers # Pass all identifiers for filename construction
        )
    else:
        logging.error(f"Failed to fetch document: {document_id}")


def fetch_dockets_data(args):
    """Fetches dockets from Regulations.gov API based on provided filters."""
    logging.info(f"Fetching dockets with filters: {args}")
    params = {}
    identifiers = {}

    if args.search_term:
        params["filter[searchTerm]"] = args.search_term
        identifiers["searchTerm"] = args.search_term.replace(" ", "_") # Filename friendly
    
    # Page size and number for dockets (1-250)
    if args.page_size is not None:
        if not 1 <= args.page_size <= 250:
            logging.warning("Page size for dockets must be between 1 and 250. Using default of 25.")
            params["page[size]"] = 25
        else:
            params["page[size]"] = args.page_size
        # identifiers["pageSize"] = params["page[size]"] # Often not needed for list results filenames
    
    if args.page_number is not None:
        if args.page_number < 1:
            logging.warning("Page number must be 1 or greater. Using default of 1.")
            params["page[number]"] = 1
        else:
            params["page[number]"] = args.page_number
        # identifiers["pageNumber"] = params["page[number]"] # Often not needed for list results filenames

    data = make_regulations_request("/dockets", params=params)
    if data:
        save_json(data, "dockets_list", sub_dir="dockets", **identifiers)
    else:
        logging.error(f"Failed to fetch dockets for filters: {identifiers}")


def fetch_single_docket_data(args):
    """Fetches a single docket by its ID from Regulations.gov API."""
    if not args.docket_id: # Should be caught by argparse 'required=True'
        logging.error("Docket ID is required for fetching a single docket.")
        sys.exit(1)

    docket_id = args.docket_id
    logging.info(f"Fetching docket: {docket_id}")
    
    endpoint_path = f"/dockets/{docket_id}"
    # No additional query parameters are typically needed for fetching a specific resource by ID
    
    data = make_regulations_request(endpoint_path)
    
    if data:
        # Create a filename-safe version of docket_id.
        # Regulations.gov docket IDs can contain hyphens, which are fine for filenames.
        # If they could contain slashes or other problematic chars, more cleaning would be needed.
        safe_docket_id_for_path_and_filename = docket_id 
        
        # Save in a subdirectory named after the docket_id itself for organization
        save_json(
            data, 
            "docket_details", 
            sub_dir=f"dockets/{safe_docket_id_for_path_and_filename}", 
            docket_id=safe_docket_id_for_path_and_filename 
        )
    else:
        logging.error(f"Failed to fetch docket: {docket_id}")


def fetch_comments_data(args):
    """Fetches comments from Regulations.gov API based on provided filters."""
    logging.info(f"Fetching comments with filters: {args}")
    params = {}
    identifiers = {}

    if args.search_term:
        params["filter[searchTerm]"] = args.search_term
        identifiers["searchTerm"] = args.search_term.replace(" ", "_")
    
    # Page size for comments (1-100)
    if args.page_size is not None:
        if not 1 <= args.page_size <= 100:
            logging.warning("Page size for comments must be between 1 and 100. Using default of 10.")
            params["page[size]"] = 10
        else:
            params["page[size]"] = args.page_size
        # identifiers["pageSize"] = params["page[size]"] # Optional for filename
    
    if args.page_after:
        params["page[after]"] = args.page_after
        # Clean page_after for filename if it's too long or has special chars
        # For now, using a simple replacement, but a more robust slugify might be needed
        identifiers["pageAfter"] = args.page_after.replace("=", "").replace("+", "").replace("/", "")[-20:]


    data = make_regulations_request("/comments", params=params)
    if data:
        save_json(data, "comments_list", sub_dir="comments", **identifiers)
    else:
        logging.error(f"Failed to fetch comments for filters: {identifiers}")


def fetch_single_comment_data(args):
    """Fetches a single comment by its ID from Regulations.gov API."""
    if not args.comment_id: # Should be caught by argparse 'required=True'
        logging.error("Comment ID is required for fetching a single comment.")
        sys.exit(1)

    comment_id = args.comment_id
    logging.info(f"Fetching comment: {comment_id}")
    
    endpoint_path = f"/comments/{comment_id}"
    params = {}
    identifiers = {"commentId": comment_id} # Primary identifier for filename

    if args.include_attachments:
        params["include"] = "attachments"
        identifiers["attachments"] = "true" # Add to filename if attachments are included

    data = make_regulations_request(endpoint_path, params=params if params else None)
    
    if data:
        # Create a filename-safe version of comment_id.
        safe_comment_id_for_path = comment_id 
        
        # Save in a subdirectory named after the comment_id itself for organization
        save_json(
            data, 
            "comment_details", 
            sub_dir=f"comments/{safe_comment_id_for_path}", 
            **identifiers # Pass all identifiers for filename construction
        )
    else:
        logging.error(f"Failed to fetch comment: {comment_id}")


def main():
    """Main function to parse arguments and call the appropriate functions."""
    parser = argparse.ArgumentParser(description="Fetch data from the Regulations.gov API.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available subcommands")

    # Documents subcommand
    docs_parser = subparsers.add_parser("documents", help="Fetch a list of documents, with optional filters.")
    docs_parser.add_argument(
        "--search-term", 
        type=str, 
        help="Search for documents containing this term."
    )
    docs_parser.add_argument(
        "--docket-id", 
        type=str, 
        help="Filter documents by a specific docket ID."
    )
    docs_parser.add_argument(
        "--title-filter", 
        type=str, 
        help="Filter documents by words in the title."
    )
    docs_parser.add_argument(
        "--page-size", 
        type=int, 
        default=25, 
        help="Number of results per page (1-100, default: 25)."
    )
    docs_parser.add_argument(
        "--page-number", 
        type=int, 
        default=1, 
        help="Page number to retrieve (min 1, default: 1)."
    )
    docs_parser.set_defaults(func=fetch_documents_data)

    # Single Document subcommand
    doc_parser = subparsers.add_parser(
        "document", 
        help="Fetch a specific document by its ID, optionally including attachments."
    )
    doc_parser.add_argument(
        "--document-id",
        type=str,
        required=True,
        help="The ID of the document (e.g., EPA-HQ-OAR-2021-0295-0001)."
    )
    doc_parser.add_argument(
        "--include-attachments",
        action="store_true", # Makes it a boolean flag, default is False
        help="Include attachment details in the response."
    )
    doc_parser.set_defaults(func=fetch_single_document_data)

    # Dockets subcommand
    dockets_parser = subparsers.add_parser("dockets", help="Fetch a list of dockets, with optional filters.")
    dockets_parser.add_argument(
        "--search-term", 
        type=str, 
        help="Search for dockets containing this term."
    )
    dockets_parser.add_argument(
        "--page-size", 
        type=int, 
        default=25, 
        help="Number of results per page (1-250, default: 25)."
    )
    dockets_parser.add_argument(
        "--page-number", 
        type=int, 
        default=1, 
        help="Page number to retrieve (min 1, default: 1)."
    )
    dockets_parser.set_defaults(func=fetch_dockets_data)

    # Single Docket subcommand
    docket_parser = subparsers.add_parser( # Singular 'docket'
        "docket", 
        help="Fetch a specific docket by its ID."
    )
    docket_parser.add_argument(
        "--docket-id",
        type=str,
        required=True,
        help="The ID of the docket (e.g., EPA-HQ-OAR-2021-0295)."
    )
    docket_parser.set_defaults(func=fetch_single_docket_data)

    # Comments subcommand
    comments_parser = subparsers.add_parser("comments", help="Fetch a list of comments, with optional filters.")
    comments_parser.add_argument(
        "--search-term", 
        type=str, 
        help="Search for comments containing this term."
    )
    comments_parser.add_argument(
        "--page-size", 
        type=int, 
        default=10, 
        help="Number of results per page (1-100, default: 10)."
    )
    comments_parser.add_argument(
        "--page-after", 
        type=str, 
        help="Cursor for the next page of results (from 'nextPageToken' in previous response)."
    )
    comments_parser.set_defaults(func=fetch_comments_data)

    # Single Comment subcommand
    comment_parser = subparsers.add_parser( # Singular 'comment'
        "comment", 
        help="Fetch a specific comment by its ID, optionally including attachments."
    )
    comment_parser.add_argument(
        "--comment-id",
        type=str,
        required=True,
        help="The ID of the comment (e.g., EPA-HQ-OAR-2021-0295-0002)."
    )
    comment_parser.add_argument(
        "--include-attachments",
        action="store_true", # Makes it a boolean flag, default is False
        help="Include attachment details in the response."
    )
    comment_parser.set_defaults(func=fetch_single_comment_data)


    args = parser.parse_args()

    logging.info(f"Command: {args.command}")
    
    # This part will be expanded in later steps with actual function calls
    if hasattr(args, 'func'):
        args.func(args) # Assuming subcommands will set a 'func' attribute
    else:
        # If no subcommand is matched (though 'required=True' should prevent this for subparsers)
        # or if a subcommand is defined but no function is set via set_defaults
        print(f"Subcommand '{args.command}' recognized. Functionality to be implemented or no function associated.")
        # parser.print_help() # Optionally print help
        # sys.exit(1) # Optionally exit


if __name__ == "__main__":
    main()
