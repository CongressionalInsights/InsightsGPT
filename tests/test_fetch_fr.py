import pytest
import os
import sys
import json
from unittest import mock
import argparse # For creating mock args
import requests # For requests.exceptions

# Ensure 'scripts' directory is in sys.path for direct import
# This allows running pytest from the project root or within tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.fetch_fr import (
    save_json,
    fetch_json,
    cmd_documents_search,
    cmd_documents_single,
    API_BASE, # Import API_BASE for URL checking
    DATA_DIR,  # Import DATA_DIR for path checking
)

# Configure basic logging for testing if logs are generated
# (though we will primarily mock logging calls)
import logging
logging.basicConfig(level=logging.DEBUG)


# Test Fixtures (if any needed globally, otherwise define in test classes/functions)

# --- Tests for save_json ---
@mock.patch("scripts.fetch_fr.os.makedirs")
@mock.patch("scripts.fetch_fr.open", new_callable=mock.mock_open)
@mock.patch("scripts.fetch_fr.json.dump")
def test_save_json_creates_directory_and_file(mock_json_dump, mock_open_file, mock_makedirs):
    sample_data = {"key": "value"}
    file_prefix = "test_prefix"
    identifiers = {"id1": "val1", "id2": "val2"}
    
    expected_suffix = "id1_val1_id2_val2"
    expected_filename = f"{file_prefix}_{expected_suffix}.json"
    expected_path = os.path.join(DATA_DIR, expected_filename)

    save_json(sample_data, file_prefix, **identifiers)

    mock_makedirs.assert_called_once_with(DATA_DIR, exist_ok=True)
    mock_open_file.assert_called_once_with(expected_path, "w", encoding="utf-8")
    mock_json_dump.assert_called_once_with(sample_data, mock_open_file(), indent=2, ensure_ascii=False)

@mock.patch("scripts.fetch_fr.os.makedirs") # Keep mocking makedirs, it's harmless
@mock.patch("scripts.fetch_fr.open", new_callable=mock.mock_open)
@mock.patch("scripts.fetch_fr.json.dump")
def test_save_json_filename_generation_no_identifiers(mock_json_dump, mock_open_file, mock_makedirs):
    sample_data = {"key": "value"}
    file_prefix = "test_prefix_no_id"
    
    expected_filename = f"{file_prefix}_no_params.json"
    expected_path = os.path.join(DATA_DIR, expected_filename)

    save_json(sample_data, file_prefix)

    mock_open_file.assert_called_once_with(expected_path, "w", encoding="utf-8")
    mock_json_dump.assert_called_once_with(sample_data, mock_open_file(), indent=2, ensure_ascii=False)

@mock.patch("scripts.fetch_fr.os.makedirs")
@mock.patch("scripts.fetch_fr.open", new_callable=mock.mock_open)
@mock.patch("scripts.fetch_fr.json.dump")
def test_save_json_filename_generation_with_spaces_and_slashes(mock_json_dump, mock_open_file, mock_makedirs):
    sample_data = {"key": "value"}
    file_prefix = "test_complex_id"
    identifiers = {"name with space": "value/with/slash"}
    
    # Corrected expected_suffix: space in key is preserved by current save_json logic
    expected_suffix = "name with space_value_with_slash"
    expected_filename = f"{file_prefix}_{expected_suffix}.json"
    expected_path = os.path.join(DATA_DIR, expected_filename)

    save_json(sample_data, file_prefix, **identifiers)
    mock_open_file.assert_called_once_with(expected_path, "w", encoding="utf-8")

# --- Tests for fetch_json ---
@mock.patch("scripts.fetch_fr.requests.get")
def test_fetch_json_success(mock_requests_get):
    mock_response = mock.Mock()
    mock_response.json.return_value = {"data": "success"}
    mock_response.raise_for_status = mock.Mock() # Does not raise error
    mock_requests_get.return_value = mock_response
    
    url = "http://fakeurl.com/api/data"
    result = fetch_json(url)
    
    mock_requests_get.assert_called_once_with(url, timeout=mock.ANY) # scripts.fetch_fr.REQUEST_TIMEOUT
    mock_response.raise_for_status.assert_called_once()
    assert result == {"data": "success"}

@mock.patch("scripts.fetch_fr.logging.error")
@mock.patch("scripts.fetch_fr.requests.get")
def test_fetch_json_request_exception(mock_requests_get, mock_logging_error):
    mock_requests_get.side_effect = requests.exceptions.RequestException("Test network error")
    
    url = "http://fakeurl.com/api/data_error"
    result = fetch_json(url)
    
    mock_requests_get.assert_called_once_with(url, timeout=mock.ANY)
    mock_logging_error.assert_called_once_with(f"API request failed for URL {url}: Test network error")
    assert result is None

@mock.patch("scripts.fetch_fr.logging.error")
@mock.patch("scripts.fetch_fr.requests.get")
def test_fetch_json_http_error(mock_requests_get, mock_logging_error):
    mock_response = mock.Mock()
    http_error = requests.exceptions.HTTPError("Test HTTP error")
    mock_response.raise_for_status = mock.Mock(side_effect=http_error)
    mock_requests_get.return_value = mock_response
    
    url = "http://fakeurl.com/api/http_error"
    result = fetch_json(url)
    
    mock_requests_get.assert_called_once_with(url, timeout=mock.ANY)
    mock_response.raise_for_status.assert_called_once()
    mock_logging_error.assert_called_once_with(f"API request failed for URL {url}: Test HTTP error")
    assert result is None

# --- Tests for cmd_documents_single (URL Construction) ---
@mock.patch("scripts.fetch_fr.save_json")
@mock.patch("scripts.fetch_fr.fetch_json")
def test_cmd_documents_single_url_construction(mock_fetch_json, mock_save_json):
    mock_fetch_json.return_value = {"some": "data"} # fetch_json should return data for save_json
    
    args = argparse.Namespace(doc_number="2023-12345")
    cmd_documents_single(args)
    
    expected_url = f"{API_BASE}/documents/{args.doc_number}.json"
    mock_fetch_json.assert_called_once_with(expected_url)
    mock_save_json.assert_called_once_with({"some": "data"}, "documents_single", doc_number=args.doc_number)

# --- Tests for cmd_documents_search (Parameter Handling) ---
@mock.patch("scripts.fetch_fr.save_json")
@mock.patch("scripts.fetch_fr.fetch_json")
def test_cmd_documents_search_parameter_handling_basic(mock_fetch_json, mock_save_json):
    mock_fetch_json.return_value = {"results": []}
    args = argparse.Namespace(
        term="climate change",
        per_page="100",
        page="1",
        order="newest",
        pub_date_year="2023",
        pub_date_gte="2023-01-01",
        pub_date_lte="2023-12-31",
        pub_date_is="2023-07-15",
        agency_slug=[], # No agencies for this basic test
        doc_type=[]      # No doc_types for this basic test
    )
    
    cmd_documents_search(args)
    
    # Check that fetch_json was called (URL construction is complex, so check for key params)
    assert mock_fetch_json.call_count == 1
    called_url = mock_fetch_json.call_args[0][0]
    
    assert f"{API_BASE}/documents.json" in called_url
    assert "conditions%5Bterm%5D=climate+change" in called_url # urlencoded term
    assert "per_page=100" in called_url
    assert "page=1" in called_url
    assert "order=newest" in called_url
    assert "conditions%5Bpublication_date%5D%5Byear%5D=2023" in called_url
    assert "conditions%5Bpublication_date%5D%5Bgte%5D=2023-01-01" in called_url
    assert "conditions%5Bpublication_date%5D%5Blte%5D=2023-12-31" in called_url
    assert "conditions%5Bpublication_date%5D%5Bis%5D=2023-07-15" in called_url
    
    mock_save_json.assert_called_once_with(
        {"results": []},
        "documents_search",
        term="climate change",
        pub_date_year="2023",
        pub_date_is="2023-07-15", # Note: save_json only uses some args for its filename
        agency="",
        doc_type=""
    )

@mock.patch("scripts.fetch_fr.save_json")
@mock.patch("scripts.fetch_fr.fetch_json")
def test_cmd_documents_search_parameter_handling_multiple_agencies_doctypes(mock_fetch_json, mock_save_json):
    mock_fetch_json.return_value = {"results": ["item"]}
    args = argparse.Namespace(
        term="", per_page="", page="", order="",
        pub_date_year="", pub_date_gte="", pub_date_lte="", pub_date_is="",
        agency_slug=["environmental-protection-agency", "energy-department"],
        doc_type=["RULE", "NOTICE"]
    )
    
    cmd_documents_search(args)
    
    assert mock_fetch_json.call_count == 1
    called_url = mock_fetch_json.call_args[0][0]
    
    assert "conditions%5Bagencies%5D%5B%5D=environmental-protection-agency" in called_url
    assert "conditions%5Bagencies%5D%5B%5D=energy-department" in called_url
    assert "conditions%5Btype%5D%5B%5D=RULE" in called_url
    assert "conditions%5Btype%5D%5B%5D=NOTICE" in called_url
    
    mock_save_json.assert_called_once_with(
        {"results": ["item"]},
        "documents_search",
        term="",
        pub_date_year="",
        pub_date_is="",
        agency="environmental-protection-agency__energy-department",
        doc_type="RULE__NOTICE"
    )

# To make this file runnable with 'python -m pytest tests/test_fetch_fr.py' or similar
if __name__ == "__main__":
    pytest.main()
