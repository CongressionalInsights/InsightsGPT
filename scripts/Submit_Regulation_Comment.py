#!/usr/bin/env python3
"""
Submit_Regulation_Comment.py

CLI tool to submit a public comment to Regulations.gov for a given docket.

Usage:
  python Submit_Regulation_Comment.py \
    --docket-id DOCKET_ID \
    [--comment "Your comment text"] \
    [--comment-file path/to/comment.txt] \
    [--api-key API_KEY] \
    [--dry-run] \
    [--output response.json]

Environment variables:
  REGGOV_API_KEY  Regulations.gov API key (if --api-key not provided)
"""
import argparse
import os
import sys
import json
import logging
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env
load_dotenv()

API_ENDPOINT = "https://api.regulations.gov/v4/comments"
DEFAULT_TIMEOUT = 10


def get_api_key(cli_key: str) -> str:
    """Retrieve API key from CLI or environment."""
    return cli_key or os.getenv("REGGOV_API_KEY")


def create_session(
    retries: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist=(500, 502, 504)
) -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def main():
    parser = argparse.ArgumentParser(
        description="Submit a comment to Regulations.gov"
    )
    parser.add_argument(
        "--docket-id", required=True,
        help="Regulations.gov docket ID (e.g., NOAA-NMFS-2024-0001)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--comment",
        help="Comment text"
    )
    group.add_argument(
        "--comment-file",
        help="Path to text file containing the comment"
    )
    parser.add_argument(
        "--api-key",
        help="Regulations.gov API key (overrides ENV VAR)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print payload and exit without sending"
    )
    parser.add_argument(
        "--output",
        help="Path to save JSON response"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )
    logger = logging.getLogger(__name__)

    api_key = get_api_key(args.api_key)
    if not api_key:
        logger.error(
            "No API key provided. Set REGGOV_API_KEY or use --api-key"
        )
        sys.exit(1)

    # Load comment text
    if args.comment:
        comment_text = args.comment
    else:
        try:
            with open(args.comment_file, "r", encoding="utf-8") as f:
                comment_text = f.read().strip()
        except Exception as e:
            logger.error(f"Failed to read comment file: {e}")
            sys.exit(1)

    # Build JSON:API payload
    payload = {
        "data": {
            "type": "Comment",
            "attributes": {
                "docketId": args.docket_id,
                "commentOn": args.docket_id,
                "body": comment_text
            }
        }
    }
    headers = {
        "Content-Type": "application/vnd.api+json",
        "X-API-Key": api_key
    }

    logger.info("Prepared comment for docket %s", args.docket_id)
    if args.dry_run:
        print("DRY RUN MODE")
        print("Endpoint:", API_ENDPOINT)
        print("Headers:", headers)
        print("Payload:", json.dumps(payload, indent=2))
        sys.exit(0)

    # Send request
    session = create_session()
    try:
        response = session.post(
            API_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        resp_json = response.json()
        comment_id = resp_json.get("data", {}).get("id")
        logger.info("Comment submitted successfully. ID: %s", comment_id)

        # Output result
        if args.output:
            with open(args.output, "w", encoding="utf-8") as out_file:
                json.dump(resp_json, out_file, indent=2)
            logger.info("Response saved to %s", args.output)
        else:
            print(json.dumps(resp_json, indent=2))

    except requests.exceptions.RequestException as err:
        logger.error("Submission failed: %s", err)
        sys.exit(1)


if __name__ == "__main__":
    main()
