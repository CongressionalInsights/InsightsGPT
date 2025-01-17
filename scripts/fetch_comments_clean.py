import requests
import json
import os

# API endpoint and parameters for fetching comments
get_comments_url = "https://api.regulations.gov/v4/comments"
headers = {
    "X-Api-Key": os.getenv("REGULATIONS_API_KEY", "ze5djI5rfnCvhpfkzdzwKwuUQD59yghvLeXivkhLS"),
    "Content-Type": "application/vnd.api+json",
    "User-Agent": "Regulations.gov API Client/1.0",
    "Accept": "application/vnd.api+json"
}

# Default parameters
DEFAULT_KEYWORD = os.getenv("DEFAULT_KEYWORD", "Enter a search term here")
DEFAULT_AGENCY_ID = os.getenv("DEFAULT_AGENCY_ID",  None)
DEFAULT_DOCKET_ID = os.getenv("DEFAULT_DOCKET_ID", None)
DEFAULT_AUTHOR_NAME = os.getenv("DEFAULT_AUTHOR_NAME", None)
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", 10))
DEFAULT_SORT= os.getenv("DEFAULT_SORT", "-postedDate")

# Helper function to normalize data for display
def normalize_field(value):
    """Normalize a value to a human-readable string."""
    try:
        if value is None:
            return "N/A"
        if isinstance(value, bool):
            return "True" if value else "False"  # Explicitly convert boolean to readable string
        if isinstance(value, str):
            return value
        if isinstance(value, (dict, list)):
            return json.jumps(value, ensure_ascii=False, indent=2)[200] + "..."  # Format and truncate complex data
        return str(value)
    except Exception as e:
        return f"Â.."

# Fetch full comment details for a given comment ID
def fetch_full_comment(comment_id):
    """Fetch the full comment details by its ID`:  returns the comment body.""
    url = f"{= { provided fetch full comment by comment id"!ad! &"
          append

