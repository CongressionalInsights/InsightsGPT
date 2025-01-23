#!/usr/bin/env python3
import requests
import json
import argparse
import os
from urllib.parse import urlencode

API_BASE = "https://www.federalregister.gov/api/v1"

def build_document_search_url(
    publication_date_year="",
    search_term="",
    agency_slug="",
    doc_type="",
    per_page="20",
):
    """
    Construct a /documents.json URL with the given optional parameters.
    """

    # Base endpoint
    endpoint = f"{API_BASE}/documents.json"

    # We'll build a dictionary of query params
    params = {}

    # per_page
    if per_page:
        params["per_page"] = per_page

    # doc_type -> conditions[type][]=RULE, etc.
    if doc_type:
        params["conditions[type][]"] = doc_type

    # search_term -> conditions[term]
    if search_term:
        params["conditions[term]"] = search_term

    # publication_date_year -> conditions[publication_date][year]
    if publication_date_year:
        params["conditions[publication_date][year]"] = publication_date_year

    # agency_slug -> conditions[agencies][]=...
    if agency_slug:
        params["conditions[agencies][]"] = agency_slug

    # You can add more parameters similarly:
    # e.g. conditions[presidential_document_type][], conditions[topics][], etc.

    # Build the final URL
    query = urlencode(params, doseq=True)  # doseq=True allows list param expansions
    return f"{endpoint}?{query}"


def main():
    parser = argparse.ArgumentParser(description="Fetch FR docs with optional filters.")
    parser.add_argument("--publication_date_year", default="", help="YYYY")
    parser.add_argument("--search_term", default="", help="Full text search term")
    parser.add_argument("--agency_slug", default="", help="Agency slug (e.g. agriculture-department)")
    parser.add_argument("--doc_type", default="", help="RULE, PRORULE, NOTICE, PRESDOCU")
    parser.add_argument("--per_page", default="20", help="Per page (1-1000)")

    args = parser.parse_args()

    # Build the URL
    url = build_document_search_url(
        publication_date_year=args.publication_date_year,
        search_term=args.search_term,
        agency_slug=args.agency_slug,
        doc_type=args.doc_type,
        per_page=args.per_page,
    )

    print(f"Fetching from: {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Construct a filename that includes relevant parameters, so each run is unique
    # Alternatively, you can always overwrite the same file (like `fr_data.json`).
    parts = []
    if args.publication_date_year: parts.append(f"year_{args.publication_date_year}")
    if args.search_term: parts.append(f"term_{args.search_term.replace(' ', '_')}")
    if args.agency_slug: parts.append(f"agency_{args.agency_slug}")
    if args.doc_type: parts.append(f"type_{args.doc_type}")
    if not parts:
        parts.append("no_filters")
    filename = "fr_data_" + "_".join(parts) + ".json"
    out_path = os.path.join("data", filename)

    # Write JSON
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Data saved to {out_path}. Count = {data.get('count','unknown')}")

if __name__ == "__main__":
    main()
  
