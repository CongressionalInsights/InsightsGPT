import requests
import json
import os

# API endpoint and parameters for fetching comments
get_comments_url = "https://api.regulations.gov/v4/comments"
headers = {
    "X-Api-Key": os.getenv("REGULATIONS_API_KEY", "ze5djIUrfnCvhpfkzdzwKwuTQD5yghvLeXivkhLS"),
    "Content-Type": "application/vnd.api+json",
    "User-Agent": "Regulations.gov API Client/1.0",
    "Accept": "application/vnd.api+json"
}

# Default parameters
DEFAULT_KEYWORD = os.getenv("DEFAULT_KEYWORD", "Enter a search term here")
DEFAULT_AGENCY_ID = os.getenv("DEFAULT_AGENCY_ID", None)
DEFAULT_DOCKET_ID = os.getenv("DEFAULT_DOCKET_ID", None)
DEFAULT_AUTHOR_NAME = os.getenv("DEFAULT_AUTHOR_NAME", None)
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", 10))
DEFAULT_SORT = os.getenv("DEFAULT_SORT", "-postedDate")

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
            return json.dumps(value, ensure_ascii=False, indent=2)[:200] + "..."  # Format and truncate complex data
        return str(value)
    except Exception as e:
        return f"[Error Normalizing: {str(e)}]"

# Fetch full comment details for a given comment ID
def fetch_full_comment(comment_id):
    """Fetch the full comment details by its ID."""
    url = f"{get_comments_url}/{comment_id}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        comment_data = response.json()
        attributes = comment_data.get("data", {}).get("attributes", {})
        return attributes.get("comment", "No comment body available")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching full comment for ID {comment_id}: {str(e)}")
        return "Error fetching comment"

# Fetch all comments with pagination support
def fetch_all_comments(sort_by=DEFAULT_SORT, page_size=DEFAULT_PAGE_SIZE, keyword=DEFAULT_KEYWORD, agency_id=DEFAULT_AGENCY_ID, docket_id=DEFAULT_DOCKET_ID, author_name=DEFAULT_AUTHOR_NAME):
    """Fetch all comments with optional sorting, filtering, and pagination."""
    params = {
        "sort": sort_by,  # Sort by newest comments first
        "page[size]": page_size  # Number of comments to fetch per page
    }
    if keyword:
        params["filter[searchTerm]"] = keyword
    if agency_id:
        params["filter[agencyId]"] = agency_id
    if docket_id:
        params["filter[docketId]"] = docket_id
    if author_name:
        params["filter[author]"] = author_name  # Use specific filter for author name

    all_comments = []
    try:
        while True:
            response = requests.get(get_comments_url, headers=headers, params=params)
            print(f"Status Code (Fetching Comments): {response.status_code}")
            response.raise_for_status()
            data = response.json()

            # Debugging: Print the entire response to inspect fields
            print("Full API Response:")

            comments_list = data.get("data", [])

            if not comments_list:
                break

            for comment in comments_list:
                attributes = comment.get("attributes", {})
                comment_id = comment.get("id")
                # Fetch full comment body for each comment
                full_comment_body = fetch_full_comment(comment_id)

                # Debugging: Print raw attributes to identify issues
                print("Raw Attributes:", json.dumps(attributes, indent=2))

                all_comments.append({
                    "ID": normalize_field(comment_id),
                    "Title": normalize_field(attributes.get("title")),
                    "Comment Body": normalize_field(full_comment_body),
                    "Posted Date": normalize_field(attributes.get("postedDate"))
                })

            params["page[after]"] = data.get("meta", {}).get("nextPageToken")  # Handle pagination
            if not params.get("page[after]"):
                break

        # Display fetched comments
        for comment in all_comments:
            print(f"ID: {comment['ID']}
Title: {comment['Title']}
Comment Body: {comment['Comment Body']}
Posted Date: {comment['Posted Date']}
")

        return all_comments
    except requests.exceptions.RequestException as e:
        print(f"Error fetching all comments: {str(e)}")
        return []

# Run the functions for the specified document and comment
if __name__ == "__main__":
    print("\nFetching all comments...")
    fetch_all_comments()
