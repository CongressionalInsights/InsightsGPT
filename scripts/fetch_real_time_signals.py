import os
import json
import requests
import time
from datetime import datetime, timedelta

# --- Configuration ---
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
OPENSECRETS_API_KEY = os.environ.get('OPENSECRETS_API_KEY') # For OpenSecrets or similar lobbying data API

NEWS_API_BASE_URL = "https://newsapi.org/v2/everything" # or /top-headlines
# For OpenSecrets, the API URL would be specific to their service.
# Example: OPENSECRETS_BASE_URL = "http://www.opensecrets.org/api/" # This is a guess
# For this script, we'll simulate OpenSecrets or use a general approach if a direct API is not confirmed.

RAW_DATA_DIR = "data"
DEFAULT_REQUEST_DELAY_SECONDS = 5 # General delay for APIs
NEWS_API_PAGE_SIZE = 100 # Max for NewsAPI developer plan is 100

# --- Helper Functions ---

def make_api_request(url: str, headers: dict = None, params: dict = None) -> dict | None:
    """
    Makes an API request and returns the JSON response.
    Includes basic error handling and rate limit awareness.
    """
    try:
        response = requests.get(url, headers=headers, params=params)
        # Check for common rate limiting status codes first
        if response.status_code == 429: # Too Many Requests
            print(f"Rate limit hit for {url}. Waiting for a bit before retrying or stopping.")
            # Simple wait, could be more sophisticated (e.g. read 'Retry-After' header)
            time.sleep(60) 
            # Optionally, retry the request once or pass the error up
            # response = requests.get(url, headers=headers, params=params) # Example retry
            # response.raise_for_status()
            print(f"Rate limit hit and simple wait completed for {url}. If issues persist, script might need to stop.")
            return None # Or re-raise specific exception

        response.raise_for_status() # Raises HTTPError for other bad responses (4XX or 5XX)
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error during API request to {url}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Network error during API request to {url}: {e}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON response from {url}")
    return None

def save_json_data(data: dict, filename_prefix: str, query_slug: str):
    """Saves data to a JSON file in the RAW_DATA_DIR."""
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{filename_prefix}_{query_slug}_{timestamp}.json"
    filepath = os.path.join(RAW_DATA_DIR, filename)

    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data successfully saved to {filepath}")
    except IOError as e:
        print(f"Error saving data to {filepath}: {e}")

def sanitize_query_for_filename(query: str) -> str:
    """Sanitizes a query string to be used in a filename."""
    return "".join(c if c.isalnum() else "_" for c in query)[:50]

# --- Media Sentiment Fetching ---

def fetch_media_data(keywords: str, from_date: str = None, to_date: str = None, max_articles: int = 100):
    """
    Fetches news articles related to keywords using NewsAPI.
    Saves article headlines, snippets (description), source, and publication date.

    Args:
        keywords: Keywords to search for (e.g., bill title, bill number, topics).
        from_date: Optional. YYYY-MM-DD. Start date for articles. Defaults to 30 days ago.
        to_date: Optional. YYYY-MM-DD. End date for articles. Defaults to today.
        max_articles: Maximum number of articles to fetch (respecting API limits per call).
    """
    if not NEWS_API_KEY:
        print("Error: NEWS_API_KEY environment variable not set. Cannot fetch media data.")
        return

    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    if not from_date:
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    print(f"Fetching media data for keywords: '{keywords}' from {from_date} to {to_date}")

    params = {
        "q": keywords,
        "apiKey": NEWS_API_KEY,
        "from": from_date,
        "to": to_date,
        "language": "en", # Focus on English language articles
        "sortBy": "relevancy", # or 'publishedAt', 'popularity'
        "pageSize": min(NEWS_API_PAGE_SIZE, max_articles), # Number of results per page
        "page": 1
    }

    all_articles_data = []
    articles_fetched = 0
    
    while articles_fetched < max_articles:
        print(f"Requesting NewsAPI page {params['page']} for keywords '{keywords}'...")
        response_data = make_api_request(NEWS_API_BASE_URL, params=params)
        time.sleep(DEFAULT_REQUEST_DELAY_SECONDS) # Respect rate limits

        if response_data and response_data.get("status") == "ok":
            articles_on_page = response_data.get("articles", [])
            if not articles_on_page:
                print("No more articles found for this query.")
                break # No more articles

            for article in articles_on_page:
                all_articles_data.append({
                    "title": article.get("title"),
                    "description": article.get("description"), # Snippet
                    "source_name": article.get("source", {}).get("name"),
                    "url": article.get("url"),
                    "published_at": article.get("publishedAt"),
                    "content_preview": article.get("content") # Some APIs provide more content
                })
                articles_fetched += 1
                if articles_fetched >= max_articles:
                    break
            
            print(f"Fetched {len(articles_on_page)} articles this page. Total fetched: {articles_fetched}")

            # Check if there are more results than what we've fetched and if we need to paginate
            total_results = response_data.get("totalResults", 0)
            if articles_fetched >= total_results or articles_fetched >= max_articles:
                print("Reached max articles or no more results available.")
                break
            
            params["page"] += 1 # Go to next page
        else:
            print(f"Failed to fetch articles or error in response: {response_data.get('message', 'No message') if response_data else 'No response'}")
            break # Error or no more data

    if all_articles_data:
        query_slug = sanitize_query_for_filename(keywords)
        save_json_data(
            {"keywords": keywords, "fetch_parameters": {"from_date": from_date, "to_date": to_date}, "articles": all_articles_data},
            "media_data",
            query_slug
        )
    else:
        print(f"No media data fetched for keywords: {keywords}")


# --- Lobbying Data Fetching ---
# Note: Accessing specific, real-time lobbying data per bill is challenging without premium/specialized APIs.
# OpenSecrets.org has an API, but its granularity for *specific bills* in real-time might be limited.
# This function will be a conceptual placeholder or target high-level lobbying data (e.g., by topic or organization).

def fetch_lobbying_data_by_topic(topic_or_bill_id: str, search_type: str = "issue"):
    """
    Conceptual function to fetch lobbying data related to a topic, bill ID, or organization.
    This function's implementation heavily depends on the chosen lobbying data API.
    For OpenSecrets, you'd use their specific API endpoints and parameters.
    (https://www.opensecrets.org/api/docs/lobbying) - their API seems to focus on lobbyists, organizations, and broad issues.

    Args:
        topic_or_bill_id: The search term (e.g., "H.R.1", "Climate Change", "Specific Organization Name").
        search_type: "issue", "bill", "organization_name" - to guide API query if flexible.
                     The OpenSecrets API is more geared towards `Lobbying_Issue` or `Lobbying_Client`.
    """
    if not OPENSECRETS_API_KEY:
        print("Error: OPENSECRETS_API_KEY environment variable not set. Cannot fetch lobbying data.")
        return

    print(f"Fetching lobbying data for '{topic_or_bill_id}' (type: {search_type})... (Conceptual)")

    # This is a placeholder. A real implementation would use OpenSecrets API methods like:
    # getLobbying.php?output=json&apikey=YOUR_KEY&id=BILL_ID (if bill ID search exists)
    # or more likely, search by issue/client:
    # Example for OpenSecrets:
    # params = {
    #     "method": "getLobbying", # This is hypothetical, check OpenSecrets docs
    #     "output": "json",
    #     "apikey": OPENSECRETS_API_KEY,
    # }
    # if search_type == "issue":
    #    params["issue"] = topic_or_bill_id 
    # elif search_type == "bill_id": # Assuming API supports bill ID search
    #    params["bill"] = topic_or_bill_id 
    # ... and so on

    # Simulated response structure (as actual API is not being hit here)
    simulated_data = {
        "query": {"term": topic_or_bill_id, "type": search_type},
        "source": "OpenSecrets API (Simulated Call)",
        "filings": [
            {
                "filer": "Lobbying Firm A",
                "client": "Corporation X",
                "amount_spent": 150000,
                "issues_lobbied": [topic_or_bill_id, "Related Topic 1"],
                "report_date": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
                "specific_bills_mentioned": [topic_or_bill_id] if search_type == "bill" else []
            },
            {
                "filer": "Advocacy Group B",
                "client": "Advocacy Group B", # Self-filer
                "amount_spent": 75000,
                "issues_lobbied": [topic_or_bill_id],
                "report_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
                "specific_bills_mentioned": []
            }
        ],
        "comment": "This is simulated data. Real implementation requires OpenSecrets API integration."
    }
    
    print("Simulated lobbying data fetched. In a real scenario, an API call to OpenSecrets or similar would be made.")
    time.sleep(1) # Simulating delay of an API call

    if simulated_data["filings"]:
        query_slug = sanitize_query_for_filename(f"{search_type}_{topic_or_bill_id}")
        save_json_data(simulated_data, "lobbying_data", query_slug)
    else:
        print(f"No lobbying data found/simulated for: {topic_or_bill_id}")


# --- Main Execution ---
if __name__ == "__main__":
    print("Starting real-time signal fetching script.")

    # --- Example Usage ---
    
    # == Media Sentiment Example ==
    # Ensure NEWS_API_KEY is set in your environment.
    # Example: Fetch media data related to "climate change policy"
    # bill_keywords = "climate change policy" 
    # bill_keywords = "H.R. 3684" # Example: Infrastructure Investment and Jobs Act
    # fetch_media_data(keywords=bill_keywords, max_articles=50) # Fetch fewer articles for testing
    
    # Example: Fetch media data for a more recent, specific bill if one is known
    # For instance, if you know a bill "S.1234" was introduced recently.
    # Use a broader search if the bill number itself doesn't yield many news results.
    # fetch_media_data(keywords="S.1234 OR 'Senate technology bill'", max_articles=30)

    # To run, uncomment one of the fetch_media_data calls and ensure NEWS_API_KEY is set.
    if NEWS_API_KEY:
        fetch_media_data(keywords="renewable energy legislation", max_articles=20) # Small number for quick test
    else:
        print("Skipping media data fetching as NEWS_API_KEY is not set.")

    print("-" * 30)

    # == Lobbying Data Example ==
    # Ensure OPENSECRETS_API_KEY is set for real data. This example uses simulated data.
    # topic_for_lobbying = "Artificial Intelligence regulation"
    # fetch_lobbying_data_by_topic(topic_or_bill_id=topic_for_lobbying, search_type="issue")
    
    # Example for a hypothetical bill ID search (actual API may differ)
    # bill_id_for_lobbying = "S.1234"
    # fetch_lobbying_data_by_topic(topic_or_bill_id=bill_id_for_lobbying, search_type="bill_id")

    # To run, uncomment one of the fetch_lobbying_data_by_topic calls.
    # Note: This will currently save SIMULATED data.
    if OPENSECRETS_API_KEY: # This check is for a real key, but function is simulated
        print("\nNote: Lobbying data fetching is currently SIMULATED.")
        fetch_lobbying_data_by_topic(topic_or_bill_id="pharmaceutical pricing", search_type="issue")
    else:
        print("Skipping lobbying data fetching as OPENSECRETS_API_KEY is not set (or using simulated data path).")
        # Still run with simulated data if key isn't present, for demonstration
        print("\nRunning SIMULATED lobbying data fetching for demonstration as API key is not set.")
        fetch_lobbying_data_by_topic(topic_or_bill_id="pharmaceutical pricing", search_type="issue")


    print("\nReal-time signal fetching script finished.")
