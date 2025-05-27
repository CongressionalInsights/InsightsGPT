import os
import json
import pandas as pd
from datetime import datetime

# --- Configuration ---
RAW_DATA_DIR = "data"
PROCESSED_DATA_DIR = "datasets"
OUTPUT_CSV_FILENAME = "processed_bill_metadata.csv"

# --- Helper Functions ---

def load_json_file(filepath: str) -> dict | None:
    """Loads a JSON file and returns its content as a dictionary."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {filepath}")
    except IOError:
        print(f"Error reading file: {filepath}")
    return None

def get_primary_sponsor_details(sponsors_list: list) -> tuple[str | None, str | None, str | None]:
    """
    Extracts details of the primary sponsor.
    Assumes the first sponsor in the list is primary, or one marked as 'Primary Sponsor'.
    """
    if not sponsors_list:
        return None, None, None
    
    # Look for a sponsor explicitly marked as "Primary Sponsor"
    for sponsor_item in sponsors_list:
        if isinstance(sponsor_item, dict) and sponsor_item.get("type") == "Primary Sponsor":
            s_name = sponsor_item.get("fullName") or sponsor_item.get("name")
            s_party = sponsor_item.get("party")
            s_state = sponsor_item.get("state")
            return s_name, s_party, s_state
            
    # Fallback to the first sponsor if no "Primary Sponsor" type found
    primary_sponsor = sponsors_list[0]
    if isinstance(primary_sponsor, dict):
        s_name = primary_sponsor.get("fullName") or primary_sponsor.get("name")
        s_party = primary_sponsor.get("party")
        s_state = primary_sponsor.get("state")
        return s_name, s_party, s_state
    return None, None, None # Should not happen if list is not empty and contains dicts

def get_latest_action(actions_list: list) -> tuple[str | None, str | None]:
    """
    Extracts the text and date of the latest action.
    Actions are usually sorted with the latest first in Congress.gov API.
    """
    if not actions_list:
        return None, None
    
    latest_action = None
    latest_date_str = None

    # Iterate to find the action with the most recent date, as order isn't always guaranteed
    # or use the first one if dates are consistently ordered (latest first)
    # For Congress.gov, actions are typically sorted latest first.
    if actions_list:
        action = actions_list[0] # Assuming latest is first
        action_text = action.get("text")
        action_date_str = action.get("actionDate")

        # Try to parse and reformat date, handle various possible formats
        if action_date_str:
            try:
                # Common formats: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
                dt_obj = pd.to_datetime(action_date_str).strftime('%Y-%m-%d')
                return action_text, dt_obj
            except ValueError:
                return action_text, action_date_str # Return original if parsing fails
        return action_text, None
        
    return None, None


def process_single_bill_data(bill_content: dict, source_filename: str) -> dict | None:
    """
    Processes the JSON data for a single bill to extract relevant fields.
    This function is designed for the structure of '*_detailed_metadata.json' files.
    """
    bill_details = bill_content.get("bill_details", {})
    if not bill_details:
        print(f"Skipping {source_filename}: 'bill_details' key is missing or empty.")
        return None

    processed_data = {}

    # Basic Info
    processed_data["bill_id"] = f"{bill_details.get('congress')}-{bill_details.get('type')}-{bill_details.get('number')}"
    processed_data["title"] = bill_details.get("title")
    processed_data["congress"] = bill_details.get("congress")
    processed_data["bill_type"] = bill_details.get("type")
    processed_data["bill_number"] = bill_details.get("number")
    
    introduced_date_str = bill_details.get("introducedDate")
    if introduced_date_str:
        try:
            processed_data["introduced_date"] = pd.to_datetime(introduced_date_str).strftime('%Y-%m-%d')
        except ValueError:
            processed_data["introduced_date"] = None # Or keep original string
            print(f"Warning: Could not parse introducedDate '{introduced_date_str}' in {source_filename}")
    else:
        processed_data["introduced_date"] = None

    # Sponsor Info (Primary Sponsor)
    sponsors = bill_content.get("sponsors", [])
    primary_sponsor_name, primary_sponsor_party, primary_sponsor_state = get_primary_sponsor_details(sponsors)
    processed_data["primary_sponsor_name"] = primary_sponsor_name
    processed_data["primary_sponsor_party"] = primary_sponsor_party
    processed_data["primary_sponsor_state"] = primary_sponsor_state
    processed_data["num_cosponsors"] = len(sponsors) - 1 if sponsors else 0 # Assuming first is primary

    # Latest Action
    actions = bill_content.get("actions", [])
    processed_data["num_actions"] = len(actions) if actions else 0
    latest_action_text, latest_action_date = get_latest_action(actions)
    processed_data["latest_action_text"] = latest_action_text
    processed_data["latest_action_date"] = latest_action_date
    
    # Committees
    committees_data = bill_content.get("committees", [])
    committee_names = []
    if committees_data:
        for committee in committees_data:
            if isinstance(committee, dict) and committee.get("name"):
                committee_names.append(committee["name"])
    processed_data["committees"] = "; ".join(committee_names) if committee_names else None
    processed_data["num_committees"] = len(committee_names)

    # Policy Area
    policy_area = bill_details.get("policyArea", {}).get("name")
    processed_data["policy_area"] = policy_area

    # Legislative Subjects
    subjects = bill_details.get("subjects", {}).get("legislativeSubjects", [])
    subject_names = [s.get("name") for s in subjects if isinstance(s, dict) and s.get("name")]
    processed_data["legislative_subjects"] = "; ".join(subject_names) if subject_names else None

    # Source Filename for traceability
    processed_data["source_filename"] = source_filename

    return processed_data

def process_congress_bill_list_data(congress_list_content: dict, source_filename: str) -> list[dict]:
    """
    Processes the JSON data from 'bill_metadata_congress_{congress_number}.json' files.
    These files contain a list of bills with less detail than the 'detailed' files.
    """
    bills = congress_list_content.get("bills", [])
    processed_bills_list = []

    if not bills:
        print(f"No 'bills' found in {source_filename}.")
        return []

    for bill_item in bills:
        if not isinstance(bill_item, dict):
            continue

        processed_data = {}
        processed_data["bill_id"] = f"{bill_item.get('congress')}-{bill_item.get('type')}-{bill_item.get('number')}"
        processed_data["title"] = bill_item.get("title")
        processed_data["congress"] = bill_item.get("congress")
        processed_data["bill_type"] = bill_item.get("type")
        processed_data["bill_number"] = bill_item.get("number")
        
        introduced_date_str = bill_item.get("introducedDate")
        if introduced_date_str:
            try:
                processed_data["introduced_date"] = pd.to_datetime(introduced_date_str).strftime('%Y-%m-%d')
            except ValueError:
                processed_data["introduced_date"] = None
        else:
            processed_data["introduced_date"] = None
        
        latest_action = bill_item.get("latestAction", {})
        processed_data["latest_action_text"] = latest_action.get("text")
        latest_action_date_str = latest_action.get("actionDate")
        if latest_action_date_str:
            try:
                processed_data["latest_action_date"] = pd.to_datetime(latest_action_date_str).strftime('%Y-%m-%d')
            except ValueError:
                processed_data["latest_action_date"] = None
        else:
            processed_data["latest_action_date"] = None

        # Fields not typically in list view, set to None or default
        processed_data["primary_sponsor_name"] = None
        processed_data["primary_sponsor_party"] = None
        processed_data["primary_sponsor_state"] = None
        processed_data["num_cosponsors"] = bill_item.get("cosponsors", {}).get("count", 0) # Some list views might have this
        processed_data["num_actions"] = latest_action.get("count") # API might provide total action count here
        processed_data["committees"] = None
        processed_data["num_committees"] = 0
        processed_data["policy_area"] = bill_item.get("policyArea", {}).get("name")
        processed_data["legislative_subjects"] = None
        processed_data["source_filename"] = source_filename
        
        processed_bills_list.append(processed_data)
    
    print(f"Processed {len(processed_bills_list)} bills from {source_filename}.")
    return processed_bills_list


# --- Main Processing Logic ---
def main():
    """
    Main function to orchestrate loading, processing, and saving of bill metadata.
    """
    print(f"Starting processing of JSON files from '{RAW_DATA_DIR}/'")
    all_processed_bill_data = []
    
    raw_files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith(".json")]
    if not raw_files:
        print(f"No JSON files found in '{RAW_DATA_DIR}/'. Exiting.")
        return

    print(f"Found {len(raw_files)} JSON files to process.")

    for filename in raw_files:
        filepath = os.path.join(RAW_DATA_DIR, filename)
        raw_content = load_json_file(filepath)

        if not raw_content:
            print(f"Skipping {filename} due to loading error.")
            continue
        
        print(f"Processing file: {filename}...")
        if "_detailed_metadata.json" in filename:
            # This is a file with detailed data for a single bill
            processed_data = process_single_bill_data(raw_content, filename)
            if processed_data:
                all_processed_bill_data.append(processed_data)
        elif "bill_metadata_congress_" in filename:
            # This is a file with a list of bills for a congress
            processed_list = process_congress_bill_list_data(raw_content, filename)
            if processed_list:
                all_processed_bill_data.extend(processed_list)
        else:
            print(f"Skipping {filename}: File naming convention not recognized for processing.")

    if not all_processed_bill_data:
        print("No bill data was successfully processed. Output CSV will not be generated.")
        return

    print(f"\nSuccessfully processed data for {len(all_processed_bill_data)} bill entries.")
    
    # Convert to DataFrame for easier handling and saving
    df = pd.DataFrame(all_processed_bill_data)

    # Potential new features / further cleaning (examples)
    # 1. Days since introduction (relative to today or latest action)
    df['introduced_date_dt'] = pd.to_datetime(df['introduced_date'], errors='coerce')
    df['latest_action_date_dt'] = pd.to_datetime(df['latest_action_date'], errors='coerce')

    # Calculate days_active (days from introduction to latest action, or to today if no latest action)
    # For this example, let's use days from introduction to latest action.
    # If latest_action_date is NaT, this will result in NaT.
    df['days_pending_latest_action'] = (df['latest_action_date_dt'] - df['introduced_date_dt']).dt.days
    
    # If you want days from introduction until today (if bill is still "active" or latest action is old)
    # today = pd.to_datetime(datetime.now().strftime('%Y-%m-%d'))
    # df['days_since_introduction'] = (today - df['introduced_date_dt']).dt.days
    
    # Clean up temporary datetime columns if not needed in CSV
    df = df.drop(columns=['introduced_date_dt', 'latest_action_date_dt'])

    # Ensure PROCESSED_DATA_DIR exists
    if not os.path.exists(PROCESSED_DATA_DIR):
        os.makedirs(PROCESSED_DATA_DIR)

    output_path = os.path.join(PROCESSED_DATA_DIR, OUTPUT_CSV_FILENAME)
    try:
        df.to_csv(output_path, index=False)
        print(f"\nProcessed data saved successfully to: {output_path}")
    except IOError as e:
        print(f"Error saving processed data to CSV: {e}")

if __name__ == "__main__":
    # Ensure pandas is installed. If not, this script will fail at import.
    # You might need to run: pip install pandas
    main()
    print("Processing script finished.")
