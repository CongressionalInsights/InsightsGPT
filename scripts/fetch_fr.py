#!/usr/bin/env python3
"""
fetch_fr.py

CLI tool with subcommands for interacting with the Federal Register API:
  - documents: Fetch documents by docket ID (advanced sync/async, caching, pagination)
  - search: Search documents by keyword terms
  - get-single: Retrieve a single document by its FR document number
  - issues: List regulatory issues
  - agencies: List agencies
  - public-inspection: Retrieve public inspection documents

Global Options:
  --api-key       Federal Register API key (overrides ENV)
  --output-dir    Directory to save JSON output (default from fr_client.DEFAULT_DATA_DIR)

Subcommand-specific options available via `fetch_fr.py <subcmd> --help`
"""
import argparse
import os
import sys
import json
import logging
import asyncio
import urllib.parse
from dotenv import load_dotenv
import httpx
import requests

# Add scripts directory to sys.path
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    from fr_client import (
        API_BASE,
        DEFAULT_DATA_DIR,
        DEFAULT_TIMEOUT,
        get_api_key,
        create_sync_session,
        create_async_client,
        validate_schema # Renamed from validate_with_schema
    )
except ImportError as e:
    print(f"Failed to import from fr_client: {e}. Ensure fr_client.py is in the same directory or PYTHONPATH is set correctly.")
    sys.exit(1)

# Initialize logger for this script
script_logger = logging.getLogger(__name__)

# --- Helper Function ---
def save_generic_json(data, command_name, args_dict, output_dir_resolved):
    os.makedirs(output_dir_resolved, exist_ok=True)
    filename_parts = [command_name]

    relevant_args_vars = vars(args_dict)
    # Exclude common/control args and args that are None for filename generation
    excluded_keys = ['command', 'func', 'api_key', 'output_dir', 'verbose', 'debug',
                     'use_async', 'dry_run', 'fetch_all', 'schema',
                     'page_size', 'max_pages', 'per_page', 'page']

    relevant_args = {
        k: v for k, v in sorted(relevant_args_vars.items())
        if k not in excluded_keys and v is not None
    }

    # Ensure specific list-type args are included if they were not None, even if part of a broader category
    list_arg_names_for_filename = ['agency_slugs', 'doc_type', 'topics', 'sections',
                                   'presidential_document_type', 'presidential_document_subtype']
    for list_arg_name in list_arg_names_for_filename:
        if hasattr(args_dict, list_arg_name) and getattr(args_dict, list_arg_name) is not None:
            if list_arg_name not in relevant_args:
                 relevant_args[list_arg_name] = getattr(args_dict, list_arg_name)

    for key, val in relevant_args.items():
        safe_key = "".join(c if c.isalnum() else '_' for c in str(key))
        if isinstance(val, list):
            val_str = "__".join("".join(c if c.isalnum() else '_' for c in str(v_item)) for v_item in val)
        else:
            val_str = "".join(c if c.isalnum() else '_' for c in str(val))

        safe_val = val_str[:50]
        filename_parts.append(f"{safe_key}_{safe_val}")

    if not relevant_args and command_name in ["agencies", "issues"] and not any(getattr(args_dict, d_arg, None) for d_arg in ["date_is", "date_gte", "date_lte"]):
        filename_parts.append("all_results")

    base_filename = "_".join(filename_parts)
    max_len_base = 220 - len(".json")
    if len(base_filename) > max_len_base:
        base_filename = base_filename[:max_len_base]

    filename = base_filename + ".json"
    filepath = os.path.join(output_dir_resolved, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        script_logger.info(f"Saved data to {filepath}")
    except IOError as e:
        script_logger.error(f"Failed to save data to {filepath}: {e}")
    except Exception as e:
        script_logger.error(f"An unexpected error occurred while saving to {filepath}: {e}")


# --- 'documents' Subcommand Functions ---
async def _fetch_page_async_docs(client, url, headers, params, page_num, retries, backoff_factor):
    script_logger.debug(f"Fetching page {page_num} asynchronously from {url} with params {params}")
    attempt = 0
    current_backoff = backoff_factor
    while attempt < retries:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            script_logger.warning(f"Attempt {attempt + 1}/{retries}: HTTP error {e.response.status_code} for page {page_num}. Retrying in {current_backoff:.2f}s...")
            if e.response.status_code == 404 and page_num > 1:
                 script_logger.info(f"Page {page_num} not found (404), likely end of results.")
                 return None
            if attempt + 1 == retries:
                script_logger.error(f"Final attempt failed for page {page_num}: {e}")
                raise
        except httpx.RequestError as e:
            script_logger.warning(f"Attempt {attempt + 1}/{retries}: Request error for page {page_num}: {e}. Retrying in {current_backoff:.2f}s...")
            if attempt + 1 == retries:
                script_logger.error(f"Final attempt failed for page {page_num}: {e}")
                raise
        await asyncio.sleep(current_backoff)
        attempt += 1
        current_backoff *= 2
    return None

async def _fetch_all_async_docs(args, fr_api_key, output_dir_resolved):
    script_logger.info(f"Starting asynchronous fetch for docket ID: {args.docket_id}")
    all_documents_data = []

    async with create_async_client() as client:
        headers = {'X-API-Key': fr_api_key, 'Accept': 'application/json'}
        base_doc_url = f"{API_BASE}/documents"
        page_num = 1

        while True:
            params = {'filter[docket_id]': args.docket_id, 'page[size]': args.page_size, 'page[number]': page_num} # Corrected API param from docket_numbers
            script_logger.info(f"Fetching page {page_num} for docket {args.docket_id}...")

            page_data_response = await _fetch_page_async_docs(client, base_doc_url, headers, params, page_num, retries=3, backoff_factor=1)

            if not page_data_response or not page_data_response.get("data"):
                script_logger.info(f"No more 'data' found for docket {args.docket_id} at page {page_num}.")
                break

            safe_docket_id = args.docket_id.replace('/', '_').replace('-', '_')
            page_filename = os.path.join(output_dir_resolved, f"docket_{safe_docket_id}_page_{page_num}_async.json")
            try:
                with open(page_filename, "w", encoding="utf-8") as f: json.dump(page_data_response, f, indent=2, ensure_ascii=False)
                script_logger.info(f"Saved page {page_num} to {page_filename}")
            except IOError as e: script_logger.error(f"Failed to save page {page_num} to {page_filename}: {e}")

            if args.schema and not validate_schema(page_data_response, args.schema):
                script_logger.warning(f"Schema validation failed for page {page_num} data from {args.docket_id}. Continuing...")

            all_documents_data.extend(page_data_response["data"])

            if args.max_pages and page_num >= args.max_pages: script_logger.info(f"Reached max pages ({args.max_pages})."); break

            meta = page_data_response.get("meta", {}); links = page_data_response.get("links", {})
            if not meta.get("next_page_url") and not links.get("next"): script_logger.info(f"Last page reached for docket {args.docket_id} at page {page_num}."); break

            page_num += 1
            if not args.fetch_all: script_logger.info("Not fetching all pages as per --fetch-all=False."); break

    if all_documents_data:
        safe_docket_id = args.docket_id.replace('/', '_').replace('-', '_')
        combined_data_output = {"data": all_documents_data, "meta": {"total_documents_retrieved": len(all_documents_data), "docket_id": args.docket_id, "description": "Combined results from asynchronous fetch"}}
        combined_filename = os.path.join(output_dir_resolved, f"docket_{safe_docket_id}_all_documents_async.json")
        try:
            with open(combined_filename, "w", encoding="utf-8") as f: json.dump(combined_data_output, f, indent=2, ensure_ascii=False)
            script_logger.info(f"Saved all combined documents to {combined_filename}")
        except IOError as e: script_logger.error(f"Failed to save combined documents to {combined_filename}: {e}")
    else: script_logger.info(f"No documents found or fetched for docket ID {args.docket_id} via async method.")
    return all_documents_data

def _fetch_pages_sync_docs(args, fr_api_key, output_dir_resolved):
    script_logger.info(f"Starting synchronous fetch for docket ID: {args.docket_id}")
    all_documents_data = []
    page_num = 1
    session = create_sync_session(use_cache=not args.no_cache) # Respect --no-cache from main
    base_doc_url = f"{API_BASE}/documents"
    headers = {'X-API-Key': fr_api_key, 'Accept': 'application/json'}
    try:
        while True:
            params = {'filter[docket_id]': args.docket_id, 'page[size]': args.page_size, 'page[number]': page_num} # Corrected API param
            script_logger.info(f"Fetching page {page_num} for docket {args.docket_id} synchronously...")
            response = None
            try:
                response = session.get(base_doc_url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
                response.raise_for_status()
                page_data_response = response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404 and page_num > 1: script_logger.info(f"Page {page_num} not found (404), end of results for docket {args.docket_id}."); break
                script_logger.error(f"HTTP error fetching page {page_num} for docket {args.docket_id}: {e}"); break
            except requests.exceptions.RequestException as e: script_logger.error(f"Request error fetching page {page_num} for docket {args.docket_id}: {e}"); break
            except json.JSONDecodeError as e:
                resp_text = response.text if response else "No response object"
                script_logger.error(f"JSON decode error for page {page_num} of docket {args.docket_id}: {e}. Content: {resp_text[:200]}"); break

            if not page_data_response or not page_data_response.get("data"): script_logger.info(f"No more 'data' found for docket {args.docket_id} at page {page_num} (sync)."); break

            safe_docket_id = args.docket_id.replace('/', '_').replace('-', '_')
            page_filename = os.path.join(output_dir_resolved, f"docket_{safe_docket_id}_page_{page_num}_sync.json")
            try:
                with open(page_filename, "w", encoding="utf-8") as f: json.dump(page_data_response, f, indent=2, ensure_ascii=False)
                script_logger.info(f"Saved page {page_num} to {page_filename}")
            except IOError as e: script_logger.error(f"Failed to save page {page_num} to {page_filename}: {e}")

            if args.schema and not validate_schema(page_data_response, args.schema):
                script_logger.warning(f"Schema validation failed for page {page_num} data (sync) from {args.docket_id}. Continuing...")
            all_documents_data.extend(page_data_response["data"])

            if args.max_pages and page_num >= args.max_pages: script_logger.info(f"Reached max pages ({args.max_pages}) for sync fetch."); break
            meta = page_data_response.get("meta", {}); links = page_data_response.get("links", {})
            if not meta.get("next_page_url") and not links.get("next"): script_logger.info(f"Last page reached (sync) for docket {args.docket_id} at page {page_num}."); break
            page_num += 1
            if not args.fetch_all: script_logger.info("Not fetching all pages as per --fetch-all=False (sync)."); break
    finally:
        if session: session.close()

    if all_documents_data:
        safe_docket_id = args.docket_id.replace('/', '_').replace('-', '_')
        combined_data_output = {"data": all_documents_data, "meta": {"total_documents_retrieved": len(all_documents_data), "docket_id": args.docket_id, "description": "Combined results from synchronous fetch"}}
        combined_filename = os.path.join(output_dir_resolved, f"docket_{safe_docket_id}_all_documents_sync.json")
        try:
            with open(combined_filename, "w", encoding="utf-8") as f: json.dump(combined_data_output, f, indent=2, ensure_ascii=False)
            script_logger.info(f"Saved all combined documents (sync) to {combined_filename}")
        except IOError as e: script_logger.error(f"Failed to save combined documents (sync) to {combined_filename}: {e}")
    else: script_logger.info(f"No documents found or fetched for docket ID {args.docket_id} (sync).")
    return all_documents_data

def run_documents(args): # Renamed from run_documents_subcommand
    script_logger.info(f"Executing 'documents' subcommand for Docket ID: {args.docket_id}")
    if '/' not in args.docket_id and '-' not in args.docket_id:
        script_logger.warning(f"Docket ID '{args.docket_id}' may not be in a standard format (e.g., AGENCY-YYYY-NUMBER or AGENCY_YYYY_NUMBER).")
    if args.dry_run:
        # Enhanced dry run output
        print(f"\nDRY RUN MODE for 'documents' subcommand:")
        print(f"  Docket ID: {args.docket_id}")
        print(f"  Page Size: {args.page_size}")
        print(f"  Fetch All: {args.fetch_all}")
        print(f"  Max Pages: {args.max_pages if args.max_pages else ('Unlimited' if args.fetch_all else '1 (default if not fetch-all)')}") # More descriptive max_pages
        print(f"  Use Async: {args.use_async}")
        print(f"  Schema: {args.schema if args.schema else 'None'}")
        print(f"  Output Dir: {args.resolved_output_dir}") # Use resolved_output_dir
        return
    if args.use_async: asyncio.run(_fetch_all_async_docs(args, args.resolved_api_key, args.resolved_output_dir))
    else: _fetch_pages_sync_docs(args, args.resolved_api_key, args.resolved_output_dir)

# --- Other Subcommand Handlers ---
def _generic_fr_api_call(args, fr_api_key_resolved, session_resolved, output_dir_resolved, endpoint_path_segment, params_to_build):
    script_logger.info(f"Executing '{args.command}' subcommand with params: {params_to_build}")
    endpoint_url = f"{API_BASE}/{endpoint_path_segment}"
    headers = {'X-API-Key': fr_api_key_resolved, 'Accept': 'application/json'}

    if args.dry_run:
        print(f"\nDRY RUN MODE for '{args.command}' subcommand:")
        print(f"  Endpoint URL: {endpoint_url}")
        query_string = urllib.parse.urlencode(params_to_build, doseq=True) if params_to_build else ""
        print(f"  Full URL (approx): {endpoint_url}{'?' if query_string else ''}{query_string}")
        print(f"  Headers: {headers}")
        return

    response = None
    try:
        response = session_resolved.get(endpoint_url, params=params_to_build, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if hasattr(args, 'schema') and args.schema and not validate_schema(data, args.schema):
            script_logger.warning(f"Schema validation failed for {args.command} results.")
        save_generic_json(data, args.command, args, output_dir_resolved)
    except requests.exceptions.HTTPError as e: script_logger.error(f"HTTP error for '{args.command}': {e}")
    except requests.exceptions.RequestException as e: script_logger.error(f"Request error for '{args.command}': {e}")
    except json.JSONDecodeError as e:
        resp_text = response.text if response else "No response object"
        script_logger.error(f"JSON decode error for '{args.command}': {e}. Response text: {resp_text[:500]}")


def run_search(args): # Renamed from run_search_subcommand
    params = {'filter[term]': args.term, 'page[per_page]': args.per_page, 'page[number]': args.page, 'order': args.order}
    if args.pub_date_year: params['filter[publication_date][year]'] = args.pub_date_year
    if args.pub_date_gte: params['filter[publication_date][gte]'] = args.pub_date_gte
    if args.pub_date_lte: params['filter[publication_date][lte]'] = args.pub_date_lte
    if args.pub_date_is: params['filter[publication_date][is]'] = args.pub_date_is
    if args.agency_slugs: params['filter[agency_ids][]'] = args.agency_slugs
    if args.doc_type: params['filter[type][]'] = args.doc_type
    if args.topics: params['filter[topics][]'] = args.topics
    if args.sections: params['filter[sections][]'] = args.sections
    if args.presidential_document_type: params['filter[presidential_document_type][]'] = args.presidential_document_type
    if args.presidential_document_subtype: params['filter[presidential_document_subtype][]'] = args.presidential_document_subtype
    _generic_fr_api_call(args, args.resolved_api_key, args.session, args.resolved_output_dir, "documents", params)

def run_get_single(args): # Renamed
    encoded_doc_number = urllib.parse.quote(args.doc_number, safe='')
    _generic_fr_api_call(args, args.resolved_api_key, args.session, args.resolved_output_dir, f"documents/{encoded_doc_number}", {})

def run_issues(args): # New handler for issues
    params = {}
    if args.date_is: params['filter[publication_date][is]'] = args.date_is
    if args.date_gte: params['filter[publication_date][gte]'] = args.date_gte
    if args.date_lte: params['filter[publication_date][lte]'] = args.date_lte
    _generic_fr_api_call(args, args.resolved_api_key, args.session, args.resolved_output_dir, "issues", params)

def run_agencies(args): # New handler for agencies
    _generic_fr_api_call(args, args.resolved_api_key, args.session, args.resolved_output_dir, "agencies", {})

def run_public_inspection(args):
    params = {}
    if args.date_is: params['filter[filing_date][is]'] = args.date_is
    if args.date_gte: params['filter[filing_date][gte]'] = args.date_gte
    if args.date_lte: params['filter[filing_date][lte]'] = args.date_lte
    if args.agency_slugs: params['filter[agency_ids][]'] = args.agency_slugs
    if args.doc_type: params['filter[type][]'] = args.doc_type
    _generic_fr_api_call(args, args.resolved_api_key, args.session, args.resolved_output_dir, "public-inspection-documents", params)


# --- Main Argparse and Execution ---
def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Fetch data from the Federal Register API (api.federalregister.gov/v1/).")
    parser.add_argument("--api-key", help="Federal Register API key. Overrides FEDREG_API_KEY environment variable.")
    parser.add_argument("--output-dir", default=None, help=f"Directory to save output files. Defaults to environment variable FEDREG_DATA_DIR or, if not set, '{DEFAULT_DATA_DIR}'.")
    # Changed verbose/debug logic slightly to match common patterns:
    # --verbose for INFO, --debug for DEBUG (implies verbose for script_logger)
    group_logging = parser.add_mutually_exclusive_group()
    group_logging.add_argument("--verbose", action="store_const", dest="log_level", const=logging.INFO, help="Enable INFO level logging for this script.")
    group_logging.add_argument("--debug", action="store_const", dest="log_level", const=logging.DEBUG, help="Enable DEBUG level logging for this script and dependencies.")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching for synchronous requests.")
    parser.set_defaults(log_level=logging.WARNING) # Default logging level for external libraries


    subparsers = parser.add_subparsers(dest="command", required=True, title="Subcommands", help="Available subcommands. Use <subcommand> --help for details.")

    # 'documents' subcommand
    p_docs = subparsers.add_parser("documents", help="Fetch documents by Docket ID. Supports pagination and async fetching.")
    p_docs.add_argument("--docket-id", required=True, help="Docket ID (e.g., 'USTR-2023-0001').")
    p_docs.add_argument("--page-size", type=int, default=250, help="Docs per page (default: 250). FR API max is 1000.")
    p_docs.add_argument("--fetch-all", action="store_true", help="Fetch all pages of results. If not set, fetches only the first page unless --max-pages is specified > 1.")
    p_docs.add_argument("--max-pages", type=int, default=0, help="Maximum number of pages to fetch if --fetch-all is set (0 for no limit). If --fetch-all is not set, this implies fetching up to max_pages. Default: 0.")
    p_docs.add_argument("--schema", type=str, help="Path to a JSON schema file for validating individual page responses.")
    p_docs.add_argument("--use-async", action="store_true", help="Use asynchronous fetching (experimental).")
    p_docs.add_argument("--dry-run", action="store_true", help="Simulate fetching; prints parameters.")
    p_docs.set_defaults(func=run_documents)

    # 'search' subcommand
    p_search = subparsers.add_parser("search", help="Search FR documents.")
    p_search.add_argument("--term", required=True, help="Search term.")
    p_search.add_argument("--per-page", type=int, default=20, dest="page_size", help="Results per page (default: 20). Note: API uses page[size] or page[per_page]. Standardizing to page_size internally for FR API.") # Renamed to page_size for consistency
    p_search.add_argument("--page", type=int, default=1, help="Page number to fetch (default: 1).") # This is for specific page fetching, pagination logic is separate
    p_search.add_argument("--order", choices=['relevance', 'newest', 'oldest'], default='relevance', help="Sort order (default: 'relevance').")
    p_search.add_argument("--pub-date-year", type=str, help="Filter by publication year (YYYY).")
    p_search.add_argument("--pub-date-gte", type=str, help="Filter by publication date greater than or equal to (YYYY-MM-DD).")
    p_search.add_argument("--pub-date-lte", type=str, help="Filter by publication date less than or equal to (YYYY-MM-DD).")
    p_search.add_argument("--pub-date-is", type=str, help="Filter by specific publication date (YYYY-MM-DD).")
    p_search.add_argument("--agency-slugs", type=str, nargs='+', help="Filter by one or more agency slugs (e.g., 'environmental-protection-agency' 'federal-reserve-system').")
    p_search.add_argument("--doc-type", type=str, nargs='+', help="Filter by one or more document types (e.g., 'RULE' 'NOTICE').")
    p_search.add_argument("--topics", type=str, nargs='+', help="Filter by one or more topics.")
    p_search.add_argument("--sections", type=str, nargs='+', help="Filter by one or more sections (e.g., 'money-and-finance').")
    p_search.add_argument("--presidential-document-type", type=str, nargs='+', help="Filter by type of presidential document (e.g. 'executive_order').")
    p_search.add_argument("--presidential-document-subtype", type=str, nargs='+', help="Filter by subtype of presidential document.")
    p_search.add_argument("--schema", type=str, help="Path to JSON schema for validating the API response.")
    p_search.add_argument("--dry-run", action="store_true", help="Simulate fetching; prints parameters.")
    p_search.set_defaults(func=run_search) # Corrected func name

    # 'get-single' subcommand
    p_get_single = subparsers.add_parser("get-single", help="Fetch a single document by its document number.")
    p_get_single.add_argument("--doc-number", required=True, help="The document number (e.g., '2023-12345').")
    p_get_single.add_argument("--schema", type=str, help="Path to JSON schema for validating the API response.")
    p_get_single.add_argument("--dry-run", action="store_true", help="Simulate fetching; prints parameters.")
    p_get_single.set_defaults(func=run_get_single) # Corrected func name

    # 'issues' subcommand
    p_issues = subparsers.add_parser("issues", help="List Federal Register issues by date or date range.")
    p_issues.add_argument("--date-is", type=str, help="List issues for a specific date (YYYY-MM-DD).")
    p_issues.add_argument("--date-gte", type=str, help="List issues on or after this date (YYYY-MM-DD).")
    p_issues.add_argument("--date-lte", type=str, help="List issues on or before this date (YYYY-MM-DD).")
    p_issues.add_argument("--page-size", type=int, default=100, help="Number of issues per page (if API paginates).") # Added page_size
    p_issues.add_argument("--schema", type=str, help="Path to JSON schema for validating the API response.")
    p_issues.add_argument("--dry-run", action="store_true", help="Simulate fetching; prints parameters.")
    p_issues.set_defaults(func=run_issues) # Corrected func name

    # 'agencies' subcommand
    p_agencies = subparsers.add_parser("agencies", help="List Federal Register agencies.")
    p_agencies.add_argument("--page-size", type=int, default=100, help="Number of agencies per page (if API paginates).") # Added page_size
    p_agencies.add_argument("--schema", type=str, help="Path to JSON schema for validating the API response.")
    p_agencies.add_argument("--dry-run", action="store_true", help="Simulate fetching; prints parameters.")
    p_agencies.set_defaults(func=run_agencies) # Corrected func name

    # 'public-inspection' subcommand
    p_pi = subparsers.add_parser("public-inspection", help="Fetch documents available for public inspection.")
    p_pi.add_argument("--date-is", type=str, help="Filter by specific filing date (YYYY-MM-DD).")
    p_pi.add_argument("--date-gte", type=str, help="Filter by filing date greater than or equal to (YYYY-MM-DD).")
    p_pi.add_argument("--date-lte", type=str, help="Filter by filing date less than or equal to (YYYY-MM-DD).")
    p_pi.add_argument("--agency-slugs", type=str, nargs='+', help="Filter by one or more agency slugs.")
    p_pi.add_argument("--doc-type", type=str, nargs='+', help="Filter by one or more document types (e.g., 'RULE', 'NOTICE').")
    p_pi.add_argument("--page-size", type=int, default=100, help="Number of documents per page (if API paginates).") # Added page_size
    p_pi.add_argument("--schema", type=str, help="Path to JSON schema for validating the API response.")
    p_pi.add_argument("--dry-run", action="store_true", help="Simulate fetching; prints parameters.")
    p_pi.set_defaults(func=run_public_inspection) # Corrected func name

    args = parser.parse_args()

    # Setup Logging
    # Configure basicConfig for root logger (affects external libraries if they use logging.getLogger())
    # Set external library logging level based on --debug flag
    external_lib_log_level = logging.DEBUG if args.log_level == logging.DEBUG else logging.WARNING
    logging.basicConfig(level=external_lib_log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler(sys.stdout)])
    # Set level for this script's specific logger instance based on --verbose or --debug
    script_logger.setLevel(args.log_level if args.log_level != logging.WARNING else logging.INFO)


    args.resolved_api_key = get_api_key(args.api_key, env_var_name='FEDREG_API_KEY')
    if not args.resolved_api_key and not args.dry_run:
        script_logger.error("Federal Register API key not found. Set --api-key or FEDREG_API_KEY environment variable.")
        sys.exit(1)

    if args.dry_run and not args.resolved_api_key:
        args.resolved_api_key = "DRY_RUN_NO_KEY_NEEDED"
        script_logger.info("Dry run mode: Using placeholder API key as none was provided.")

    args.resolved_output_dir = args.output_dir if args.output_dir else DEFAULT_DATA_DIR
    if not args.dry_run:
        try: os.makedirs(args.resolved_output_dir, exist_ok=True)
        except OSError as e: script_logger.error(f"Could not create output directory {args.resolved_output_dir}: {e}"); sys.exit(1)
    script_logger.info(f"Using output directory: {args.resolved_output_dir}")


    if hasattr(args, 'func'):
        if args.command == "documents":
            args.func(args) # Documents handler doesn't take session
        else:
            session_to_pass = None
            if not args.dry_run:
                # Pass args.no_cache to create_sync_session
                session_to_pass = create_sync_session(use_cache=not args.no_cache)

            # Add session to args for generic handlers
            args.session = session_to_pass
            try:
                args.func(args)
            finally:
                if session_to_pass:
                    session_to_pass.close()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
