import os
import json
import time
import requests

# --- Configuration ---
CONGRESS_API_KEY = os.environ.get('CONGRESS_API_KEY')
BASE_API_URL = "https://api.congress.gov/v3/"
# Rate limit: 1000 requests per hour. ~3.6 seconds per request.
# Be more conservative for loops.
DEFAULT_REQUEST_DELAY_SECONDS = 3.6 
SHORT_REQUEST_DELAY_SECONDS = 1.0 # For calls within a single bill's details

# --- Helper Functions ---

def fetch_data_from_api(endpoint_or_url: str, params: dict = None, is_full_url: bool = False) -> dict | None:
    """
    Fetches data from the specified API endpoint or a full URL.

    Args:
        endpoint_or_url: The API endpoint (e.g., "bill") or a full URL.
        params: A dictionary of parameters to include in the request (if not a full URL).
        is_full_url: True if endpoint_or_url is a complete URL.

    Returns:
        A dictionary containing the JSON response, or None if an error occurs.
    """
    if not CONGRESS_API_KEY:
        print("Error: CONGRESS_API_KEY environment variable not set.")
        return None

    headers = {
        "X-Api-Key": CONGRESS_API_KEY,
        "Accept": "application/json"
    }
    
    url = endpoint_or_url if is_full_url else f"{BASE_API_URL}{endpoint_or_url}"

    try:
        print(f"Requesting URL: {url} with params: {params if params else '{}'}")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429: # Too Many Requests
            print(f"Rate limit exceeded for {url}. Please wait and try again later.")
            # Future enhancement: implement exponential backoff here.
        else:
            print(f"HTTP error fetching data from {url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON response from {url}")
        return None

def save_data_to_json(data: dict, filename: str):
    """
    Saves the given data to a JSON file.

    Args:
        data: The dictionary to save.
        filename: The name of the file to save the data to.
                 The file will be saved in the 'data/' directory.
    """
    if not os.path.exists("data"):
        os.makedirs("data")

    filepath = os.path.join("data", filename)
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data successfully saved to {filepath}")
    except IOError as e:
        print(f"Error saving data to {filepath}: {e}")

# --- Main Fetching Logic ---

def fetch_bill_metadata_for_congress(congress_number: int, max_bills: int = 2500):
    """
    Fetches metadata for bills in a specific congress, handling pagination.

    Args:
        congress_number: The congress number (e.g., 117).
        max_bills: An approximate maximum number of bills to fetch to prevent excessive calls during testing.
                   Set to a very high number or None for no limit in production.
    """
    print(f"Fetching bill metadata for {congress_number}th Congress...")
    endpoint = f"bill/{congress_number}"
    # Congress.gov API has a max limit of 250.
    params = {"limit": 250, "offset": 0} 

    all_bills_data = []
    bills_fetched_count = 0
    
    current_url = None # For using 'next' links from pagination

    while True:
        if current_url:
            # If current_url is set, it means we are following a 'next' link which includes all necessary parameters
            api_response = fetch_data_from_api(current_url, is_full_url=True)
        else:
            # Initial request
            api_response = fetch_data_from_api(endpoint, params=params)

        if api_response and "bills" in api_response:
            bills = api_response["bills"]
            all_bills_data.extend(bills)
            bills_fetched_this_page = len(bills)
            bills_fetched_count += bills_fetched_this_page
            print(f"Fetched {bills_fetched_this_page} bills. Total fetched so far: {bills_fetched_count}")

            if not bills: # No bills returned in this page, though API indicated there might be
                print("No bills in the current page, stopping.")
                break

            # Pagination check using the 'next' link
            if "pagination" in api_response and api_response["pagination"].get("next"):
                current_url = api_response["pagination"]["next"]
                # No need to manually manage offset if using the 'next' URL.
                # params["offset"] += params["limit"] # This would be the manual way
            else:
                print("No 'next' page in pagination. All bills fetched for this query.")
                break # No more pages
            
            if max_bills is not None and bills_fetched_count >= max_bills:
                print(f"Reached specified maximum of {max_bills} bills to fetch.")
                break
            
            time.sleep(DEFAULT_REQUEST_DELAY_SECONDS) # Respect rate limits between paginated requests
        else:
            print(f"No bills found or error in API response for {endpoint} with params {params if not current_url else 'from next URL'}.")
            break
        
    if all_bills_data:
        filename = f"bill_metadata_congress_{congress_number}.json"
        save_data_to_json({"congress": congress_number, "bill_count": len(all_bills_data), "bills": all_bills_data}, filename)
    else:
        print(f"No bill data fetched for {congress_number}th Congress.")

def fetch_bill_details(congress: int, bill_type: str, bill_number: int):
    """
    Fetches detailed metadata for a specific bill, including actions, sponsors, and committees.

    Args:
        congress: The congress number (e.g., 117).
        bill_type: The type of bill (e.g., "hr", "s").
        bill_number: The bill number (e.g., 1, 50).
    """
    print(f"Fetching details for bill {bill_type.upper()}{bill_number} from {congress}th Congress...")
    bill_slug = f"{congress}/{bill_type.lower()}/{bill_number}"
    endpoint_base = f"bill/{bill_slug}"

    # Fetch main bill details
    bill_data_response = fetch_data_from_api(endpoint_base)
    time.sleep(SHORT_REQUEST_DELAY_SECONDS) # Delay after each call

    if not bill_data_response or "bill" not in bill_data_response:
        print(f"Could not fetch main details for bill {bill_slug}. Aborting.")
        return

    comprehensive_bill_data = {"bill_details": bill_data_response["bill"]}

    # Fetch Actions
    actions_response = fetch_data_from_api(f"{endpoint_base}/actions")
    if actions_response and "actions" in actions_response:
        comprehensive_bill_data["actions"] = actions_response["actions"]
    else:
        comprehensive_bill_data["actions"] = []
        print(f"No actions data found or error for bill {bill_slug}.")
    time.sleep(SHORT_REQUEST_DELAY_SECONDS)

    # Fetch Sponsors
    sponsors_response = fetch_data_from_api(f"{endpoint_base}/sponsors")
    if sponsors_response and "sponsors" in sponsors_response:
        comprehensive_bill_data["sponsors"] = sponsors_response["sponsors"]
    else:
        comprehensive_bill_data["sponsors"] = []
        print(f"No sponsors data found or error for bill {bill_slug}.")
    time.sleep(SHORT_REQUEST_DELAY_SECONDS)

    # Fetch Committees
    committees_response = fetch_data_from_api(f"{endpoint_base}/committees")
    if committees_response and "committees" in committees_response:
        comprehensive_bill_data["committees"] = committees_response["committees"]
    else:
        comprehensive_bill_data["committees"] = []
        print(f"No committees data found or error for bill {bill_slug}.")
    # No sleep needed after the last call in this function

    filename = f"{congress}_{bill_type.lower()}{bill_number}_detailed_metadata.json"
    save_data_to_json(comprehensive_bill_data, filename)


# --- Main Execution ---
if __name__ == "__main__":
    print("Starting bill metadata fetching script.")

    if not CONGRESS_API_KEY:
        print("Critical Error: CONGRESS_API_KEY is not set. This script cannot function without it.")
        print("Please set it as an environment variable. Example: export CONGRESS_API_KEY=\"YOUR_KEY_HERE\"")
        print("Script will exit.")
    else:
        # Masking the API key for display
        masked_api_key = f"{CONGRESS_API_KEY[:4]}...{CONGRESS_API_KEY[-4:]}" if len(CONGRESS_API_KEY) > 8 else "API Key (too short to mask)"
        print(f"Using API Key: {masked_api_key}")
        print(f"Default request delay between paginated list calls: {DEFAULT_REQUEST_DELAY_SECONDS}s")
        print(f"Short request delay between individual bill detail calls: {SHORT_REQUEST_DELAY_SECONDS}s")
        
        # --- Example Usage ---
        # Choose which operations to run:

        # == Option 1: Fetch metadata for bills in a specific Congress (handles pagination) ==
        # Fetches a list of bills with basic info.
        # To fetch all bills, set max_bills to a very high number or None.
        # Example: fetch_bill_metadata_for_congress(congress_number=117, max_bills=500) 
        # time.sleep(DEFAULT_REQUEST_DELAY_SECONDS * 2) # Longer pause if doing multiple congresses or types of operations

        # == Option 2: Fetch detailed metadata for a specific bill ==
        # This fetches main details, actions, sponsors, and committees for one bill.
        # Example: H.R. 1 from the 117th Congress
        fetch_bill_details(congress=117, bill_type="hr", bill_number=1)
        # time.sleep(DEFAULT_REQUEST_DELAY_SECONDS * 2) 

        # Example: S. 1 from the 118th Congress (hypothetical)
        # fetch_bill_details(congress=118, bill_type="s", bill_number=1)
        # time.sleep(DEFAULT_REQUEST_DELAY_SECONDS * 2)

        # Example: Fetch details for a bill that might not exist to test error handling
        # fetch_bill_details(congress=117, bill_type="hr", bill_number=99999)


    print("Script finished.")
