#!/usr/bin/env python3

import argparse
import json
import os
from urllib.parse import urlencode
import requests
import logging
import sys
import time # Added import
from dotenv import load_dotenv

REQUEST_TIMEOUT = 10  # seconds
API_BASE = "https://www.federalregister.gov/api/v1"
DATA_DIR = "data"
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1
RETRY_STATUS_CODES = [500, 502, 503, 504] # Typical transient server errors


def sanitize_filename_part(part_value, is_term_for_federal_register=False):
    """Sanitizes a string part for use in a filename."""
    if not isinstance(part_value, str):
        part_value = str(part_value)

    # Basic sanitization: replace spaces and slashes
    safe_val = part_value.replace(" ", "_").replace("/", "_")
    
    # Allow alphanumeric, underscore, hyphen. Remove others.
    safe_val = "".join(c for c in safe_val if c.isalnum() or c in ['_', '-'])
    
    # Collapse multiple underscores/hyphens to a single underscore
    safe_val = safe_val.replace("--", "_").replace("__", "_")
    while "__" in safe_val or "--" in safe_val: # Repeat until clean
        safe_val = safe_val.replace("--", "_").replace("__", "_")

    # If it's a term for "federal_register_{term}.json" and it's empty after sanitization,
    # use a default. Otherwise, an empty string might be fine if it's just one of many parts.
    if is_term_for_federal_register and not safe_val:
        return "search_results" # Fallback for empty sanitized term
    return safe_val


def save_json(data, file_prefix, **identifiers):
    """
    Save the JSON data into the `data/` folder.
    Filename includes a prefix (e.g. 'documents_search') plus any relevant identifiers.
    For 'documents_search' with a 'term', filename is 'federal_register_{term}.json'.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    term_value = identifiers.get("term")

    if file_prefix == "documents_search" and term_value:
        # Specific filename for documents_search with a term
        sanitized_term = sanitize_filename_part(term_value, is_term_for_federal_register=True)
        filename = f"federal_register_{sanitized_term}.json"
    else:
        # Existing/General filename logic
        parts = []
        for key, val in identifiers.items():
            if val: # Ensure val is not None or empty string before processing
                sanitized_key = sanitize_filename_part(key)
                sanitized_val = sanitize_filename_part(str(val)) # Ensure val is string
                if sanitized_val: # Only add if the sanitized value is not empty
                    parts.append(f"{sanitized_key}_{sanitized_val}")
        
        if parts:
            suffix = "_".join(parts)
            filename = f"{file_prefix}_{suffix}.json"
        else:
            # Fallback if no identifiers produce a usable suffix
            filename = f"{file_prefix}_no_params.json"
            
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logging.info(f"Saved JSON to {path}.")


def fetch_json(url):
    """GET request with JSON parse, error handling, and retry for transient errors."""
    logging.info(f"GET {url}")
    for attempt in range(MAX_RETRIES + 1): # 0 is the initial attempt, 1 to MAX_RETRIES are retries
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()  # Raises HTTPError for 4xx/5xx
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in RETRY_STATUS_CODES:
                if attempt < MAX_RETRIES:
                    # Exponential backoff for retryable server errors
                    # The 'attempt' variable is 0-indexed for the loop, so 2**attempt is suitable
                    # for the first retry (attempt=0, 2^0=1), second retry (attempt=1, 2^1=2), etc.
                    # However, the prompt uses "attempt_number" as 0-indexed for *retry attempts*.
                    # If 'attempt' from 'range(MAX_RETRIES + 1)' is 0 (initial try), a retry happens if it fails.
                    # The first actual retry is when 'attempt' is 1 in the loop.
                    # So, if attempt 0 fails, the first retry is attempt 1.
                    # Let's adjust the logging to be attempt_in_loop + 1 for user display.
                    # And backoff_time for the first retry (loop attempt 1) should be 2^0.
                    # For the second retry (loop attempt 2), it should be 2^1.
                    # So, if attempt > 0 (meaning it's a retry), use 2**(attempt - 1).
                    # The provided code in prompt uses `2 ** attempt` where `attempt` is the loop variable
                    # which means initial attempt (0) gets 1s, first retry (1) gets 2s, second retry (2) gets 4s. This seems fine.
                    backoff_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt) 
                    logging.warning(
                        f"Attempt {attempt + 1}/{MAX_RETRIES + 1} failed for URL {url} with status "
                        f"{e.response.status_code}. Retrying in {backoff_time:.2f} seconds..."
                    )
                    time.sleep(backoff_time)
                else:
                    logging.error(
                        f"All {MAX_RETRIES + 1} attempts failed for URL {url} with status "
                        f"{e.response.status_code}. Final error: {e}"
                    )
                    return None # All retries exhausted
            else:
                # Non-retryable HTTPError (e.g., 4xx) or no response
                logging.error(f"HTTP request failed for URL {url} (non-retryable HTTPError or no response): {e}")
                return None
        except requests.exceptions.RequestException as e:
            # Handles other errors like network issues, timeouts beyond the HTTPError scope
            if attempt < MAX_RETRIES:
                backoff_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                logging.warning(
                    f"Attempt {attempt + 1}/{MAX_RETRIES + 1} for URL {url} failed due to RequestException: {e}. "
                    f"Retrying in {backoff_time:.2f} seconds..."
                )
                time.sleep(backoff_time)
            else:
                logging.error(
                    f"All {MAX_RETRIES + 1} attempts failed for URL {url} due to RequestException. Final error: {e}"
                )
                return None
        
    return None # Should be reached only if all retries exhausted, effectively handled within the loop.


###################
#  SUBCOMMANDS
###################


def cmd_documents_search(args):
    """
    /documents.{format} => Search published FR documents
    Docs: https://www.federalregister.gov/developers/api/v1
    """
    endpoint = f"{API_BASE}/documents.json"
    params = {}

    if args.per_page:
        params["per_page"] = args.per_page
    if args.page:
        params["page"] = args.page
    if args.order:
        params["order"] = args.order
    if args.term:
        params["conditions[term]"] = args.term
    if args.pub_date_year:
        params["conditions[publication_date][year]"] = args.pub_date_year
    if args.pub_date_gte:
        params["conditions[publication_date][gte]"] = args.pub_date_gte
    if args.pub_date_lte:
        params["conditions[publication_date][lte]"] = args.pub_date_lte
    if args.pub_date_is:
        params["conditions[publication_date][is]"] = args.pub_date_is
    # Note: args.agency_slug and args.doc_type are handled below by directly
    # appending to query_list because they can have multiple values.
    # etc. for other conditions[...] if needed

    # Convert single items into multi param approach:
    # We'll build the query string manually to handle repeated params if needed
    # requests.get(..., params=...) merges repeated keys, but let's be explicit:
    query_list = []
    for k, v in params.items():
        # if multiple, do them individually
        if isinstance(v, list):
            for item in v:
                query_list.append((k, item))
        else:
            query_list.append((k, v))

    # handle repeating conditions[agencies][] for multiple agencies
    for slug in args.agency_slug:
        query_list.append(("conditions[agencies][]", slug))

    # handle repeating conditions[type][] for multiple doc types
    for dt in args.doc_type:
        query_list.append(("conditions[type][]", dt))

    # Build final URL
    qs = urlencode(query_list, doseq=True)
    url = f"{endpoint}?{qs}"

    data = fetch_json(url)
    save_json(
        data,
        "documents_search",
        term=args.term or "",
        pub_date_year=args.pub_date_year or "",
        pub_date_is=args.pub_date_is or "",
        agency="__".join(args.agency_slug) if args.agency_slug else "",
        doc_type="__".join(args.doc_type) if args.doc_type else "",
    )


def cmd_documents_single(args):
    """
    GET /documents/{doc_number}.{format}
    """
    doc_number = args.doc_number
    url = f"{API_BASE}/documents/{doc_number}.json"
    data = fetch_json(url)
    save_json(data, "documents_single", doc_number=doc_number)


def cmd_documents_multi(args):
    """
    GET /documents/{doc_numbers}.{format}
    e.g. doc_numbers=2023-00123,2023-00456
    """
    doc_numbers = args.doc_numbers
    url = f"{API_BASE}/documents/{doc_numbers}.json"
    data = fetch_json(url)
    save_json(data, "documents_multi", doc_numbers=doc_numbers)


def cmd_documents_facets(args):
    """
    GET /documents/facets/{facet}?[conditions...]
    """
    facet = args.facet
    endpoint = f"{API_BASE}/documents/facets/{facet}"
    # We can add conditions similarly to the doc-search approach if needed
    params = {}
    if args.term:
        params["conditions[term]"] = args.term
    qs = urlencode(params)
    url = f"{endpoint}.json?{qs}" if qs else f"{endpoint}.json"
    data = fetch_json(url)
    save_json(data, "documents_facets", facet=facet, term=args.term or "")


def cmd_issues(args):
    """
    GET /issues/{publication_date}.{format}
    """
    publication_date = args.publication_date
    url = f"{API_BASE}/issues/{publication_date}.json"
    data = fetch_json(url)
    save_json(data, "issues", publication_date=publication_date)


def cmd_public_inspection_search(args):
    """
    GET /public-inspection-documents.{format}?[conditions]
    """
    endpoint = f"{API_BASE}/public-inspection-documents.json"
    params = {}
    if args.term:
        params["conditions[term]"] = args.term
    if args.per_page:
        params["per_page"] = args.per_page
    if args.page:
        params["page"] = args.page
    qs = urlencode(params)
    url = f"{endpoint}?{qs}"
    data = fetch_json(url)
    save_json(data, "public_inspection_search", term=args.term or "")


def cmd_public_inspection_single(args):
    """
    GET /public-inspection-documents/{doc_number}.{format}
    """
    doc_number = args.doc_number
    url = f"{API_BASE}/public-inspection-documents/{doc_number}.json"
    data = fetch_json(url)
    save_json(data, "public_inspection_single", doc_number=doc_number)


def cmd_public_inspection_multi(args):
    """
    GET /public-inspection-documents/{doc_numbers}.{format}
    """
    doc_numbers = args.doc_numbers
    url = f"{API_BASE}/public-inspection-documents/{doc_numbers}.json"
    data = fetch_json(url)
    save_json(data, "public_inspection_multi", doc_numbers=doc_numbers)


def cmd_public_inspection_current(args):
    """
    GET /public-inspection-documents/current.{format}
    """
    url = f"{API_BASE}/public-inspection-documents/current.json"
    data = fetch_json(url)
    save_json(data, "public_inspection_current")


def cmd_agencies(args):
    """
    GET /agencies
    """
    url = f"{API_BASE}/agencies"
    data = fetch_json(url)
    save_json(data, "agencies")


def cmd_agency_single(args):
    """
    GET /agencies/{slug}
    """
    slug = args.slug
    url = f"{API_BASE}/agencies/{slug}"
    data = fetch_json(url)
    save_json(data, "agency_single", slug=slug)


def cmd_images(args):
    """
    GET /images/{identifier}
    """
    identifier = args.identifier
    url = f"{API_BASE}/images/{identifier}"
    data = fetch_json(url)
    save_json(data, "images", identifier=identifier)


def cmd_suggested_searches(args):
    """
    GET /suggested_searches
    """
    # optionally pass conditions[sections]=...
    endpoint = f"{API_BASE}/suggested_searches"
    # Note: args.section is handled below by directly appending to qlist
    # as it can have multiple values.
    # build
    qlist = []
    for s in args.section:
        qlist.append(("conditions[sections]", s))
    qs = urlencode(qlist, doseq=True)
    url = f"{endpoint}?{qs}" if qs else endpoint
    data = fetch_json(url)
    save_json(
        data,
        "suggested_searches",
        section="__".join(args.section) if args.section else "",
    )


def cmd_suggested_search(args):
    """
    GET /suggested_searches/{slug}
    """
    slug = args.slug
    url = f"{API_BASE}/suggested_searches/{slug}"
    data = fetch_json(url)
    save_json(data, "suggested_search", slug=slug)


def main():
    print("MAIN_STARTED") # Basic print for testing
    load_dotenv() # Load environment variables from .env file
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', stream=sys.stdout)

    parser = argparse.ArgumentParser(
        description="Fetch data from Federal Register across all endpoints."
    )
    sub = parser.add_subparsers(dest="command")

    # Documents search
    p_docs_search = sub.add_parser("documents-search", help="Search FR documents.")
    p_docs_search.add_argument("--term", default="", help="Full text search term")
    p_docs_search.add_argument(
        "--per_page", default="", help="How many docs per page, up to 1000"
    )
    p_docs_search.add_argument("--page", default="", help="Page number of results")
    p_docs_search.add_argument(
        "--order",
        default="",
        choices=["relevance", "newest", "oldest", "executive_order_number"],
    )
    p_docs_search.add_argument(
        "--pub_date_year", default="", help="conditions[publication_date][year]"
    )
    p_docs_search.add_argument(
        "--pub_date_gte", default="", help="conditions[publication_date][gte]"
    )
    p_docs_search.add_argument(
        "--pub_date_lte", default="", help="conditions[publication_date][lte]"
    )
    p_docs_search.add_argument(
        "--pub_date_is", default="", help="conditions[publication_date][is]"
    )
    p_docs_search.add_argument(
        "--agency_slug",
        action="append",
        default=[],
        help="conditions[agencies][] (may be repeated)",
    )
    p_docs_search.add_argument(
        "--doc_type",
        action="append",
        default=[],
        help="conditions[type][] (RULE, PRORULE, NOTICE, PRESDOCU)",
    )
    p_docs_search.set_defaults(func=cmd_documents_search)

    # Documents single
    p_docs_single = sub.add_parser(
        "documents-single", help="Fetch single FR document by doc_number."
    )
    p_docs_single.add_argument("--doc_number", required=True, help="E.g. 2023-12345")
    p_docs_single.set_defaults(func=cmd_documents_single)

    # Documents multi
    p_docs_multi = sub.add_parser(
        "documents-multi",
        help="Fetch multiple FR documents by comma-separated doc_numbers.",
    )
    p_docs_multi.add_argument(
        "--doc_numbers", required=True, help="E.g. 2023-12345,2023-12346"
    )
    p_docs_multi.set_defaults(func=cmd_documents_multi)

    # Documents facets
    p_docs_facets = sub.add_parser(
        "documents-facets", help="Fetch document facet counts."
    )
    p_docs_facets.add_argument(
        "--facet", required=True, help="daily, agency, topic, etc."
    )
    p_docs_facets.add_argument(
        "--term", default="", help="Full text search, conditions[term]"
    )
    p_docs_facets.set_defaults(func=cmd_documents_facets)

    # Issues
    p_issues = sub.add_parser(
        "issues", help="Fetch an issue's table of contents by date (YYYY-MM-DD)."
    )
    p_issues.add_argument("--publication_date", required=True, help="E.g. 2025-01-10")
    p_issues.set_defaults(func=cmd_issues)

    # Public Inspection search
    p_pi_search = sub.add_parser(
        "public-inspection-search", help="Search public inspection documents."
    )
    p_pi_search.add_argument("--term", default="", help="conditions[term]")
    p_pi_search.add_argument(
        "--per_page", default="", help="Number per page, up to 1000"
    )
    p_pi_search.add_argument("--page", default="", help="Which page of results")
    p_pi_search.set_defaults(func=cmd_public_inspection_search)

    # Public Inspection single
    p_pi_single = sub.add_parser(
        "public-inspection-single",
        help="Fetch single public inspection doc by doc_number.",
    )
    p_pi_single.add_argument("--doc_number", required=True)
    p_pi_single.set_defaults(func=cmd_public_inspection_single)

    # Public Inspection multi
    p_pi_multi = sub.add_parser(
        "public-inspection-multi",
        help="Fetch multiple public inspection docs by comma-separated doc_numbers.",
    )
    p_pi_multi.add_argument("--doc_numbers", required=True)
    p_pi_multi.set_defaults(func=cmd_public_inspection_multi)

    # Public Inspection current
    p_pi_current = sub.add_parser(
        "public-inspection-current",
        help="Fetch all docs currently on public inspection.",
    )
    p_pi_current.set_defaults(func=cmd_public_inspection_current)

    # Agencies
    p_agencies = sub.add_parser("agencies", help="Fetch list of all agencies.")
    p_agencies.set_defaults(func=cmd_agencies)

    # Agency single
    p_agency_single = sub.add_parser(
        "agency-single", help="Fetch single agency by slug."
    )
    p_agency_single.add_argument(
        "--slug", required=True, help="E.g. 'agriculture-department'"
    )
    p_agency_single.set_defaults(func=cmd_agency_single)

    # Images
    p_images = sub.add_parser(
        "images", help="Fetch available image variants by identifier."
    )
    p_images.add_argument(
        "--identifier", required=True, help="Identifier for the image, e.g., '12345'"
    )
