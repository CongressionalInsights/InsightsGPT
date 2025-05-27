import pytest
import requests
import json
import os
from unittest.mock import MagicMock, call # For more complex mocking if needed

# Import the script to be tested
# To make this work, ensure 'scripts' directory is in PYTHONPATH or use relative imports if tests are structured as a package
# For now, let's assume we can adjust PYTHONPATH or tests are run from root where 'scripts' is accessible
# A common way is to add the project root to sys.path in a conftest.py or at the top of test files
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts import fetch_bill_metadata

# --- Fixtures ---

@pytest.fixture
def mock_env_api_key(mocker):
    """Mocks the CONGRESS_API_KEY environment variable."""
    mocker.patch.dict(os.environ, {"CONGRESS_API_KEY": "TEST_API_KEY"})

@pytest.fixture
def mock_requests_get(mocker):
    """Fixture to mock requests.get."""
    return mocker.patch("requests.get")

@pytest.fixture
def mock_save_json(mocker):
    """Mocks the save_data_to_json function in the script."""
    return mocker.patch("scripts.fetch_bill_metadata.save_data_to_json")

# --- Tests for fetch_data_from_api ---

def test_fetch_data_from_api_success(mock_env_api_key, mock_requests_get):
    """Test successful API call in fetch_data_from_api."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "data": "some_data"}
    mock_requests_get.return_value = mock_response

    result = fetch_bill_metadata.fetch_data_from_api("test_endpoint")

    mock_requests_get.assert_called_once_with(
        f"{fetch_bill_metadata.BASE_API_URL}test_endpoint",
        headers={"X-Api-Key": "TEST_API_KEY", "Accept": "application/json"},
        params=None
    )
    assert result == {"success": True, "data": "some_data"}

def test_fetch_data_from_api_http_error(mock_env_api_key, mock_requests_get, capsys):
    """Test HTTP error handling in fetch_data_from_api."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
    mock_requests_get.return_value = mock_response

    result = fetch_bill_metadata.fetch_data_from_api("error_endpoint")
    
    assert result is None
    captured = capsys.readouterr()
    assert "HTTP error fetching data" in captured.out
    assert "404 Client Error" in captured.out


def test_fetch_data_from_api_rate_limit_error(mock_env_api_key, mock_requests_get, capsys):
    """Test 429 rate limit error handling in fetch_data_from_api."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    # Attach the response to the exception instance as requests library does
    http_error = requests.exceptions.HTTPError("429 Client Error")
    http_error.response = mock_response 
    mock_response.raise_for_status.side_effect = http_error
    mock_requests_get.return_value = mock_response

    result = fetch_bill_metadata.fetch_data_from_api("rate_limit_endpoint")
    
    assert result is None
    captured = capsys.readouterr()
    assert "Rate limit exceeded for" in captured.out

def test_fetch_data_from_api_network_error(mock_env_api_key, mock_requests_get, capsys):
    """Test network error handling in fetch_data_from_api."""
    mock_requests_get.side_effect = requests.exceptions.RequestException("Network Error")

    result = fetch_bill_metadata.fetch_data_from_api("network_error_endpoint")
    
    assert result is None
    captured = capsys.readouterr()
    assert "Error fetching data" in captured.out
    assert "Network Error" in captured.out

def test_fetch_data_from_api_no_api_key(mocker, capsys):
    """Test behavior when API key is not set."""
    mocker.patch.dict(os.environ, clear=True) # Ensure API key is not set
    # We need to reload the module or patch CONGRESS_API_KEY inside the module directly for it to see the change
    mocker.patch("scripts.fetch_bill_metadata.CONGRESS_API_KEY", None)

    result = fetch_bill_metadata.fetch_data_from_api("any_endpoint")
    assert result is None
    captured = capsys.readouterr()
    assert "CONGRESS_API_KEY environment variable not set" in captured.out


# --- Tests for save_data_to_json (Interaction with file system) ---
def test_save_data_to_json(tmp_path):
    """Test saving data to a JSON file in a temporary directory."""
    data_dir = tmp_path / "data" # tmp_path is a pytest fixture for temp dirs
    # We need to patch os.makedirs because save_data_to_json calls it.
    # However, for this test, we want to ensure it CAN create it.
    # Or, we can make it part of the setup.
    # Let's test its actual file creation.
    
    # Path where the function will try to save. We need to make `fetch_bill_metadata.RAW_DATA_DIR` (if it used one)
    # or its default "data" point to our temp_path. For simplicity, let's assume it saves to "data/" relative to CWD
    # or we ensure the function `save_data_to_json` uses a passed-in base path.
    # The current `save_data_to_json` hardcodes "data" subfolder.
    
    # To test `save_data_to_json` directly, we need to ensure 'data' dir can be created or exists.
    # Let's change CWD for this test or mock `os.path.join` and `open`.
    # Easiest is to allow it to create data_dir inside tmp_path.
    
    original_cwd = os.getcwd()
    os.chdir(tmp_path) # Change CWD to tmp_path

    sample_data = {"key": "value", "number": 123}
    filename = "test_output.json"
    
    fetch_bill_metadata.save_data_to_json(sample_data, filename)
    
    expected_file_path = data_dir / filename
    assert expected_file_path.exists()
    
    with open(expected_file_path, 'r') as f:
        saved_content = json.load(f)
    assert saved_content == sample_data
    
    os.chdir(original_cwd) # Change back CWD


# --- Tests for fetch_bill_details ---
def test_fetch_bill_details_success(mock_env_api_key, mock_requests_get, mock_save_json, mocker):
    """Test successful fetching and saving of detailed bill data."""
    # Mock fetch_data_from_api to control its output directly for sub-calls
    mock_fetch = mocker.patch("scripts.fetch_bill_metadata.fetch_data_from_api")
    
    # Define return values for main bill and sub-resources
    mock_fetch.side_effect = [
        {"bill": {"title": "Main Bill Title", "number": "123"}}, # Main bill data
        {"actions": [{"text": "Action 1"}]},                     # Actions
        {"sponsors": [{"name": "Sponsor A"}]},                   # Sponsors
        {"committees": [{"name": "Committee X"}]}                # Committees
    ]

    fetch_bill_metadata.fetch_bill_details(congress=117, bill_type="hr", bill_number=123)

    # Check calls to fetch_data_from_api
    expected_calls = [
        call("bill/117/hr/123"),
        call("bill/117/hr/123/actions"),
        call("bill/117/hr/123/sponsors"),
        call("bill/117/hr/123/committees")
    ]
    mock_fetch.assert_has_calls(expected_calls, any_order=False) # Order matters here

    # Check that save_data_to_json was called with the correct data structure and filename
    expected_saved_data = {
        "bill_details": {"title": "Main Bill Title", "number": "123"},
        "actions": [{"text": "Action 1"}],
        "sponsors": [{"name": "Sponsor A"}],
        "committees": [{"name": "Committee X"}]
    }
    expected_filename = "117_hr123_detailed_metadata.json"
    mock_save_json.assert_called_once_with(expected_saved_data, expected_filename)

def test_fetch_bill_details_main_bill_fails(mock_env_api_key, mock_requests_get, mock_save_json, mocker, capsys):
    """Test when fetching the main bill details fails."""
    mock_fetch = mocker.patch("scripts.fetch_bill_metadata.fetch_data_from_api")
    mock_fetch.return_value = None # Simulate failure for the first call (main bill)

    fetch_bill_metadata.fetch_bill_details(congress=117, bill_type="s", bill_number=10)

    mock_fetch.assert_called_once_with("bill/117/s/10") # Only one call should be made
    mock_save_json.assert_not_called() # Save should not be called
    captured = capsys.readouterr()
    assert "Could not fetch main details for bill 117/s/10. Aborting." in captured.out

# --- Tests for fetch_bill_metadata_for_congress ---
def test_fetch_bill_metadata_for_congress_success_one_page(mock_env_api_key, mock_requests_get, mock_save_json, mocker):
    """Test fetching congress metadata with a single page of results."""
    mock_fetch = mocker.patch("scripts.fetch_bill_metadata.fetch_data_from_api")
    
    # Simulate API response for one page (no "next" link in pagination)
    mock_fetch.return_value = {
        "bills": [{"title": "Bill A"}, {"title": "Bill B"}],
        "pagination": {"count": 2, "next": None} # No next page
    }

    fetch_bill_metadata.fetch_bill_metadata_for_congress(congress_number=116, max_bills=10)

    mock_fetch.assert_called_once_with("bill/116", params={"limit": 250, "offset": 0})
    
    expected_saved_data = {
        "congress": 116,
        "bill_count": 2,
        "bills": [{"title": "Bill A"}, {"title": "Bill B"}]
    }
    expected_filename = "bill_metadata_congress_116.json"
    mock_save_json.assert_called_once_with(expected_saved_data, expected_filename)


def test_fetch_bill_metadata_for_congress_multiple_pages(mock_env_api_key, mock_requests_get, mock_save_json, mocker):
    """Test fetching congress metadata with pagination."""
    mock_fetch = mocker.patch("scripts.fetch_bill_metadata.fetch_data_from_api")

    # Simulate API responses for multiple pages
    mock_fetch.side_effect = [
        { # Page 1
            "bills": [{"id": "bill1"}, {"id": "bill2"}],
            "pagination": {"count": 4, "next": "https://api.example.com/next_page_url_for_page2"}
        },
        { # Page 2 (from next_page_url_for_page2)
            "bills": [{"id": "bill3"}, {"id": "bill4"}],
            "pagination": {"count": 4, "next": None} # Last page
        }
    ]

    fetch_bill_metadata.fetch_bill_metadata_for_congress(congress_number=115, max_bills=10) # max_bills > total bills

    # Check calls to fetch_data_from_api
    # First call is with endpoint and params
    # Subsequent calls are with the full 'next' URL
    expected_api_calls = [
        call("bill/115", params={"limit": 250, "offset": 0}),
        call("https://api.example.com/next_page_url_for_page2", is_full_url=True)
    ]
    mock_fetch.assert_has_calls(expected_api_calls)
    assert mock_fetch.call_count == 2
    
    expected_saved_data = {
        "congress": 115,
        "bill_count": 4,
        "bills": [{"id": "bill1"}, {"id": "bill2"}, {"id": "bill3"}, {"id": "bill4"}]
    }
    expected_filename = "bill_metadata_congress_115.json"
    mock_save_json.assert_called_once_with(expected_saved_data, expected_filename)

def test_fetch_bill_metadata_for_congress_max_bills_limit(mock_env_api_key, mock_requests_get, mock_save_json, mocker):
    """Test that fetching stops when max_bills is reached, even if more pages exist."""
    mock_fetch = mocker.patch("scripts.fetch_bill_metadata.fetch_data_from_api")
    
    # API has many bills, but we set max_bills to 2
    mock_fetch.return_value = { 
        "bills": [{"id": "b1"}, {"id": "b2"}, {"id": "b3"}], # Page has 3 bills
        "pagination": {"count": 100, "next": "https://api.example.com/next_page"}
    }

    # Max_bills is 2, so it should stop after processing the first 2 from the first page.
    fetch_bill_metadata.fetch_bill_metadata_for_congress(congress_number=114, max_bills=2) 
    
    # API should be called once
    mock_fetch.assert_called_once_with("bill/114", params={"limit": 250, "offset": 0})
    
    # Saved data should contain only 2 bills
    # The current implementation of fetch_bill_metadata_for_congress adds all bills from the last fetched page,
    # then checks max_bills. So it might save 3 bills if the page size is 3 and limit is 2.
    # Let's refine this test based on the exact behavior.
    # The loop is: fetch page, extend all_bills_data, increment count, THEN check max_bills.
    # So, if a page brings bills_fetched_count >= max_bills, it breaks *after* adding that page's bills.
    
    # The code is:
    # all_bills_data.extend(bills)
    # ... bills_fetched_count += bills_fetched_this_page
    # ... if max_bills is not None and bills_fetched_count >= max_bills: break
    # This means it will save all 3 bills from the first page in this scenario.

    expected_saved_data = {
        "congress": 114,
        "bill_count": 3, # All bills from the page that met/exceeded max_bills
        "bills": [{"id": "b1"}, {"id": "b2"}, {"id": "b3"}]
    }
    expected_filename = "bill_metadata_congress_114.json"
    mock_save_json.assert_called_once_with(expected_saved_data, expected_filename)
    # This test reveals a slight nuance in how max_bills interacts with page results.
    # If precise cutoff is needed, the logic in the main script would need adjustment.
    # For this test, we assert the current behavior.

def test_fetch_bill_metadata_for_congress_api_failure(mock_env_api_key, mock_requests_get, mock_save_json, mocker, capsys):
    """Test API failure during congress metadata fetching."""
    mock_fetch = mocker.patch("scripts.fetch_bill_metadata.fetch_data_from_api")
    mock_fetch.return_value = None # Simulate API failure

    fetch_bill_metadata.fetch_bill_metadata_for_congress(congress_number=113)

    mock_fetch.assert_called_once()
    mock_save_json.assert_not_called()
    captured = capsys.readouterr()
    assert "No bills found or error in API response" in captured.out
    assert "No bill data fetched for 113th Congress." in captured.out
