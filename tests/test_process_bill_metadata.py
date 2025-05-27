import pytest
import json
import os
import pandas as pd
from datetime import datetime

# Add project root to sys.path for module import
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts import process_bill_metadata

# --- Sample Data ---

SAMPLE_DETAILED_BILL_CONTENT = {
    "bill_details": {
        "congress": 117,
        "type": "HR",
        "number": "123",
        "title": "Test Bill Act of 2023",
        "introducedDate": "2023-01-15",
        "policyArea": {"name": "Science"},
        "subjects": {"legislativeSubjects": [{"name": "Research"}, {"name": "Technology"}]}
    },
    "sponsors": [
        {"fullName": "Rep. John Doe", "party": "D", "state": "CA", "type": "Primary Sponsor"},
        {"fullName": "Rep. Jane Smith", "party": "R", "state": "NY", "type": "Cosponsor"}
    ],
    "actions": [
        {"text": "Became Public Law No: 117-1", "actionDate": "2023-03-01"}, # Latest
        {"text": "Introduced in House", "actionDate": "2023-01-15"}
    ],
    "committees": [
        {"name": "House Committee on Science", "chamber": "House"},
        {"name": "Senate Committee on Commerce", "chamber": "Senate"}
    ]
}

SAMPLE_CONGRESS_LIST_CONTENT = {
    "congress": 116,
    "bills": [
        {
            "congress": 116,
            "type": "S",
            "number": "10",
            "title": "Senate Test Bill 1",
            "introducedDate": "2020-02-01",
            "latestAction": {"text": "Referred to committee", "actionDate": "2020-02-10", "count": 5},
            "policyArea": {"name": "Health"},
            "cosponsors": {"count": 3}
        },
        {
            "congress": 116,
            "type": "HR",
            "number": "20",
            "title": "House Test Bill 2",
            "introducedDate": "2020-03-01",
            "latestAction": {"text": "Passed House", "actionDate": "2020-06-15"}, # No count provided here
            # No policyArea for this one
        }
    ],
    "bill_count": 2
}

MALFORMED_JSON_STRING = "{'key': 'value', 'unterminated_string: \"something else\""

# --- Fixtures ---

@pytest.fixture
def temp_data_dir(tmp_path):
    """Creates a temporary data directory with sample JSON files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Detailed bill file
    with open(data_dir / "117_hr123_detailed_metadata.json", 'w') as f:
        json.dump(SAMPLE_DETAILED_BILL_CONTENT, f)
        
    # Congress list file
    with open(data_dir / "bill_metadata_congress_116.json", 'w') as f:
        json.dump(SAMPLE_CONGRESS_LIST_CONTENT, f)

    # Malformed JSON file
    with open(data_dir / "malformed_bill.json", 'w') as f:
        f.write(MALFORMED_JSON_STRING)
        
    # Empty content detailed file (missing 'bill_details')
    with open(data_dir / "117_s1_detailed_metadata.json", 'w') as f:
        json.dump({"sponsors": [], "actions": []}, f) # No "bill_details"

    return data_dir

@pytest.fixture
def temp_processed_dir(tmp_path):
    """Creates a temporary directory for processed datasets."""
    processed_dir = tmp_path / "datasets"
    processed_dir.mkdir()
    return processed_dir

# --- Tests for Helper Functions ---

def test_load_json_file_success(temp_data_dir):
    """Test loading a valid JSON file."""
    filepath = temp_data_dir / "117_hr123_detailed_metadata.json"
    data = process_bill_metadata.load_json_file(str(filepath))
    assert data is not None
    assert data["bill_details"]["title"] == "Test Bill Act of 2023"

def test_load_json_file_malformed(temp_data_dir, capsys):
    """Test loading a malformed JSON file."""
    filepath = temp_data_dir / "malformed_bill.json"
    data = process_bill_metadata.load_json_file(str(filepath))
    assert data is None
    captured = capsys.readouterr()
    assert "Error decoding JSON" in captured.out

def test_load_json_file_not_found(capsys):
    """Test loading a non-existent file."""
    data = process_bill_metadata.load_json_file("non_existent_file.json")
    assert data is None
    captured = capsys.readouterr()
    assert "Error reading file" in captured.out


# --- Tests for Core Processing Functions ---

def test_process_single_bill_data():
    """Test processing logic for a single detailed bill."""
    processed = process_bill_metadata.process_single_bill_data(SAMPLE_DETAILED_BILL_CONTENT, "sample_detailed.json")
    assert processed is not None
    assert processed["bill_id"] == "117-HR-123"
    assert processed["title"] == "Test Bill Act of 2023"
    assert processed["introduced_date"] == "2023-01-15"
    assert processed["primary_sponsor_name"] == "Rep. John Doe"
    assert processed["primary_sponsor_party"] == "D"
    assert processed["primary_sponsor_state"] == "CA"
    assert processed["num_cosponsors"] == 1
    assert processed["latest_action_text"] == "Became Public Law No: 117-1"
    assert processed["latest_action_date"] == "2023-03-01" # Standardized
    assert processed["num_actions"] == 2
    assert "House Committee on Science" in processed["committees"]
    assert "Senate Committee on Commerce" in processed["committees"]
    assert processed["num_committees"] == 2
    assert processed["policy_area"] == "Science"
    assert "Research" in processed["legislative_subjects"]
    assert "Technology" in processed["legislative_subjects"]
    assert processed["source_filename"] == "sample_detailed.json"

def test_process_single_bill_data_missing_details(capsys):
    """Test processing when 'bill_details' is missing."""
    processed = process_bill_metadata.process_single_bill_data({"sponsors": []}, "missing_details.json")
    assert processed is None
    captured = capsys.readouterr()
    assert "Skipping missing_details.json: 'bill_details' key is missing or empty." in captured.out

def test_process_congress_bill_list_data():
    """Test processing logic for a congress list file."""
    processed_list = process_bill_metadata.process_congress_bill_list_data(SAMPLE_CONGRESS_LIST_CONTENT, "sample_congress_list.json")
    assert len(processed_list) == 2

    # Test first bill from the list
    bill1 = processed_list[0]
    assert bill1["bill_id"] == "116-S-10"
    assert bill1["title"] == "Senate Test Bill 1"
    assert bill1["introduced_date"] == "2020-02-01"
    assert bill1["latest_action_text"] == "Referred to committee"
    assert bill1["latest_action_date"] == "2020-02-10"
    assert bill1["num_cosponsors"] == 3
    assert bill1["num_actions"] == 5 # from latestAction.count
    assert bill1["policy_area"] == "Health"
    assert bill1["source_filename"] == "sample_congress_list.json"

    # Test second bill (some fields might be None)
    bill2 = processed_list[1]
    assert bill2["bill_id"] == "116-HR-20"
    assert bill2["title"] == "House Test Bill 2"
    assert bill2["latest_action_text"] == "Passed House"
    assert bill2["num_cosponsors"] == 0 # Default as not provided in "cosponsors" object
    assert bill2["num_actions"] is None # latestAction.count was missing
    assert bill2["policy_area"] is None # policyArea was missing

def test_get_primary_sponsor_details():
    sponsors1 = [{"type": "Primary Sponsor", "fullName": "Sponsor A", "party": "R", "state": "TX"}]
    name, party, state = process_bill_metadata.get_primary_sponsor_details(sponsors1)
    assert name == "Sponsor A" and party == "R" and state == "TX"

    sponsors2 = [{"fullName": "Sponsor B", "party": "D", "state": "CA"}, {"type": "Cosponsor"}] # First is primary by default
    name, party, state = process_bill_metadata.get_primary_sponsor_details(sponsors2)
    assert name == "Sponsor B" and party == "D" and state == "CA"
    
    assert process_bill_metadata.get_primary_sponsor_details([]) == (None, None, None)

def test_get_latest_action():
    actions1 = [{"text": "Action Z", "actionDate": "2023-10-01"}, {"text": "Action Y", "actionDate": "2023-09-01"}] # Latest first
    text, date = process_bill_metadata.get_latest_action(actions1)
    assert text == "Action Z" and date == "2023-10-01"

    actions2 = [{"text": "Action X", "actionDate": "2023-05-15T10:00:00Z"}] # ISO format
    text, date = process_bill_metadata.get_latest_action(actions2)
    assert text == "Action X" and date == "2023-05-15"

    actions3 = [{"text": "Action W"}] # No date
    text, date = process_bill_metadata.get_latest_action(actions3)
    assert text == "Action W" and date is None
    
    assert process_bill_metadata.get_latest_action([]) == (None, None)

# --- Test Main Functionality ---

def test_main_function(temp_data_dir, temp_processed_dir, mocker):
    """Test the main function for overall processing and CSV output."""
    
    # Patch constants in the module to use temp directories
    mocker.patch("scripts.process_bill_metadata.RAW_DATA_DIR", str(temp_data_dir))
    mocker.patch("scripts.process_bill_metadata.PROCESSED_DATA_DIR", str(temp_processed_dir))
    
    process_bill_metadata.main()
    
    output_csv_path = temp_processed_dir / process_bill_metadata.OUTPUT_CSV_FILENAME
    assert output_csv_path.exists()
    
    df = pd.read_csv(output_csv_path)
    
    # Expected number of rows: 1 from detailed, 2 from list = 3 total
    # Plus 1 from the empty detailed file which should be skipped after trying to process.
    # The empty file (117_s1_detailed_metadata.json) will be skipped by process_single_bill_data
    # because 'bill_details' is missing. The malformed_bill.json will be skipped by load_json_file.
    # So, we expect 3 rows.
    assert len(df) == 3 
    
    # Check for expected columns (a subset)
    expected_cols = [
        "bill_id", "title", "introduced_date", "primary_sponsor_name", 
        "latest_action_text", "latest_action_date", "committees", "policy_area",
        "days_pending_latest_action", "source_filename"
    ]
    for col in expected_cols:
        assert col in df.columns
        
    # Check some data consistency
    # Detailed bill HR123
    hr123_row = df[df["bill_id"] == "117-HR-123"]
    assert not hr123_row.empty
    assert hr123_row.iloc[0]["primary_sponsor_name"] == "Rep. John Doe"
    assert hr123_row.iloc[0]["latest_action_text"] == "Became Public Law No: 117-1"
    assert pd.notna(hr123_row.iloc[0]["days_pending_latest_action"]) # Should be calculated

    # List bill S10
    s10_row = df[df["bill_id"] == "116-S-10"]
    assert not s10_row.empty
    assert s10_row.iloc[0]["title"] == "Senate Test Bill 1"
    assert pd.isna(s10_row.iloc[0]["primary_sponsor_name"]) # Not in list view
    assert pd.notna(s10_row.iloc[0]["days_pending_latest_action"])


def test_main_no_files_found(tmp_path, mocker, capsys):
    """Test main function when no JSON files are in the data directory."""
    empty_data_dir = tmp_path / "empty_data"
    empty_data_dir.mkdir()
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()

    mocker.patch("scripts.process_bill_metadata.RAW_DATA_DIR", str(empty_data_dir))
    mocker.patch("scripts.process_bill_metadata.PROCESSED_DATA_DIR", str(processed_dir))

    process_bill_metadata.main()
    
    captured = capsys.readouterr()
    assert f"No JSON files found in '{str(empty_data_dir)}/'" in captured.out
    
    output_csv_path = processed_dir / process_bill_metadata.OUTPUT_CSV_FILENAME
    assert not output_csv_path.exists()


def test_main_all_files_skipped(temp_data_dir, temp_processed_dir, mocker, capsys):
    """Test main when all files are present but skipped (e.g. malformed, missing keys)."""
    # Overwrite temp_data_dir to only contain skippable files
    for item in temp_data_dir.iterdir(): # Clear existing files
        item.unlink()
    
    with open(temp_data_dir / "malformed.json", 'w') as f: f.write("{'") # Malformed
    with open(temp_data_dir / "empty_detailed.json", 'w') as f: json.dump({}, f) # Empty detailed
    with open(temp_data_dir / "unrecognized_name.txt", 'w') as f: f.write("text") # Unrecognized

    mocker.patch("scripts.process_bill_metadata.RAW_DATA_DIR", str(temp_data_dir))
    mocker.patch("scripts.process_bill_metadata.PROCESSED_DATA_DIR", str(temp_processed_dir))

    process_bill_metadata.main()

    captured = capsys.readouterr()
    assert "No bill data was successfully processed. Output CSV will not be generated." in captured.out
    
    output_csv_path = temp_processed_dir / process_bill_metadata.OUTPUT_CSV_FILENAME
    assert not output_csv_path.exists()
