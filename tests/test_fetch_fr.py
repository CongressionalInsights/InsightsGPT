import pytest
import os
import sys
import json
import argparse
import asyncio
import logging
from unittest.mock import patch, MagicMock, mock_open, call

# Add scripts directory to sys.path
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

# Modules to test from fetch_fr
try:
    from fetch_fr import (
        main,
        save_generic_json, 
        run_documents_subcommand,
        run_search_subcommand,
        run_get_single_subcommand,
        run_issues_subcommand,
        run_agencies_subcommand,
        run_public_inspection_subcommand,
        _fetch_pages_sync_docs, # For more direct testing
        _fetch_all_async_docs   # For more direct testing
    )
    from fr_client import API_BASE, DEFAULT_DATA_DIR, DEFAULT_TIMEOUT, validate_with_schema
    import requests 
    import httpx 
except ImportError as e:
    print(f"Error importing from fetch_fr or fr_client: {e}")
    pytest.fail(f"Failed to import modules: {e}")

# --- Fixtures ---

@pytest.fixture
def mock_common_args(tmp_path):
    """Provides common args, including a resolved output_dir using tmp_path."""
    return argparse.Namespace(
        api_key="TEST_API_KEY",
        output_dir=str(tmp_path), # Use tmp_path for output_dir
        verbose=False,
        debug=False,
        dry_run=False,
        command=None,
        func=None,
        schema=None # Default to no schema
    )

@pytest.fixture(autouse=True)
def mock_load_dotenv_fixture():
    """Auto-mock load_dotenv for all tests to avoid .env dependency."""
    with patch('dotenv.load_dotenv') as mock_ld:
        yield mock_ld

# --- Tests for Top-Level CLI Parsing and Dispatch ---

@patch('argparse.ArgumentParser.parse_args')
@patch('scripts.fetch_fr.run_documents_subcommand') # Patch within the script's context
def test_main_dispatches_documents(mock_run_docs, mock_parse_args, mock_common_args):
    # Setup args for 'documents' command
    args_for_docs = argparse.Namespace(
        **vars(mock_common_args), # Copy common args
        command="documents",
        func=run_documents_subcommand,
        docket_id="TEST-DOCS-001",
        use_async=False, # Example: test sync path by default
        page_size=100, fetch_all=False, max_pages=0 # Add other specific args for documents
    )
    mock_parse_args.return_value = args_for_docs

    main()
    mock_run_docs.assert_called_once()
    
    # Check arguments passed to run_documents_subcommand
    called_args, called_kwargs = mock_run_docs.call_args
    assert called_args[0] == args_for_docs # The Namespace object
    assert called_args[1] == "TEST_API_KEY"  # API key
    assert called_args[2] == mock_common_args.output_dir # Resolved output directory


@patch('argparse.ArgumentParser.parse_args')
@patch('scripts.fetch_fr.run_search_subcommand')
@patch('scripts.fr_client.create_sync_session') 
def test_main_dispatches_search(mock_create_session, mock_run_search, mock_parse_args, mock_common_args):
    args_for_search = argparse.Namespace(
        **vars(mock_common_args),
        command="search",
        func=run_search_subcommand,
        term="test_term", # Required for search
        per_page=20, page=1, order='relevance' # Add other specific args for search
    )
    mock_parse_args.return_value = args_for_search
    
    mock_session_instance = MagicMock(spec=requests.Session)
    mock_create_session.return_value = mock_session_instance

    main()
    mock_run_search.assert_called_once()
    called_args, _ = mock_run_search.call_args
    assert called_args[0] == args_for_search
    assert called_args[1] == "TEST_API_KEY"
    assert called_args[2] == mock_session_instance 
    assert called_args[3] == mock_common_args.output_dir
    mock_session_instance.close.assert_called_once()


@patch('argparse.ArgumentParser.parse_args')
@patch('sys.exit')
@patch('scripts.fr_client.get_api_key', return_value=None) 
def test_main_no_api_key_exits(mock_get_api_key_fr_client, mock_sys_exit, mock_parse_args, mock_common_args, caplog):
    args_no_key = argparse.Namespace(
        **vars(mock_common_args),
        command="search", # Any command that needs a key
        api_key=None # Simulate no --api-key passed
    )
    mock_parse_args.return_value = args_no_key
    
    with caplog.at_level(logging.ERROR):
        main()
    
    assert "Federal Register API key not found" in caplog.text
    mock_sys_exit.assert_called_once_with(1)

@patch('argparse.ArgumentParser.parse_args')
@patch('os.makedirs') # Mock makedirs to check its call
def test_main_output_dir_creation(mock_makedirs, mock_parse_args, mock_common_args):
    # Test with a command that doesn't require API key for this specific check (e.g., dry_run)
    args_output_dir = argparse.Namespace(
        **vars(mock_common_args),
        command="search", func=run_search_subcommand, term="test", dry_run=True,
        output_dir="/custom/output/path" # Specify a custom path
    )
    mock_parse_args.return_value = args_output_dir
    
    # For this test, we are focusing on directory creation, so we don't need to mock session etc.
    # The dry_run for run_search_subcommand will prevent actual API calls.
    main()
    # Directory creation is skipped for dry_run, so this assertion is only valid if not dry_run
    # Let's modify to test the case where it *should* be created
    args_output_dir.dry_run = False 
    with patch('scripts.fr_client.create_sync_session'), patch('scripts.fetch_fr.run_search_subcommand'):
         main()
    mock_makedirs.assert_called_with("/custom/output/path", exist_ok=True)


# --- Tests for 'documents' Subcommand (run_documents_subcommand and its helpers) ---

@pytest.fixture
def docs_specific_args(mock_common_args):
    """Args specific to the 'documents' subcommand."""
    return argparse.Namespace(
        **vars(mock_common_args), # Inherit common args like output_dir
        command="documents",
        docket_id="TEST-DOCKET-001", 
        page_size=10, 
        fetch_all=True, 
        max_pages=2,
        schema=None, 
        use_async=False, 
        dry_run=False
    )

@patch('scripts.fetch_fr._fetch_all_async_docs') # Patch the helper function
def test_run_documents_async_path_calls_helper(mock_fetch_all_async, docs_specific_args, caplog):
    docs_specific_args.use_async = True
    
    with caplog.at_level(logging.INFO):
        run_documents_subcommand(docs_specific_args, "ASYNC_API_KEY", docs_specific_args.output_dir)
    
    mock_fetch_all_async.assert_called_once_with(docs_specific_args, "ASYNC_API_KEY", docs_specific_args.output_dir)
    assert f"Executing 'documents' subcommand for Docket ID: {docs_specific_args.docket_id}" in caplog.text

@patch('scripts.fetch_fr._fetch_pages_sync_docs') # Patch the helper function
def test_run_documents_sync_path_calls_helper(mock_fetch_pages_sync, docs_specific_args, caplog):
    docs_specific_args.use_async = False
    
    with caplog.at_level(logging.INFO):
        run_documents_subcommand(docs_specific_args, "SYNC_API_KEY", docs_specific_args.output_dir)
        
    mock_fetch_pages_sync.assert_called_once_with(docs_specific_args, "SYNC_API_KEY", docs_specific_args.output_dir)
    assert f"Executing 'documents' subcommand for Docket ID: {docs_specific_args.docket_id}" in caplog.text


def test_run_documents_dry_run(docs_specific_args, capsys):
    docs_specific_args.dry_run = True
    run_documents_subcommand(docs_specific_args, "DRY_RUN_KEY", docs_specific_args.output_dir)
    
    captured = capsys.readouterr() # Dry run prints to stdout
    assert "DRY RUN MODE for 'documents' subcommand" in captured.out
    assert f"Docket ID: {docs_specific_args.docket_id}" in captured.out
    assert f"Output Dir: {docs_specific_args.output_dir}" in captured.out


@patch('scripts.fr_client.create_async_client')
@patch('scripts.fetch_fr._fetch_page_async_docs') # Mock the lowest level page fetcher
@patch('scripts.fr_client.validate_with_schema', return_value=True) # Assume valid schema
@patch('builtins.open', new_callable=mock_open)
async def run_fetch_all_async_docs_test_wrapper(mock_open_file, mock_validate_schema, mock_fetch_page, mock_create_client, args, api_key, output_dir):
    """Wrapper to call and test _fetch_all_async_docs."""
    mock_async_client_instance = MagicMock(spec=httpx.AsyncClient)
    mock_async_client_instance.__aenter__.return_value = mock_async_client_instance
    mock_async_client_instance.__aexit__.return_value = None
    mock_create_client.return_value = mock_async_client_instance

    # Setup mock responses for _fetch_page_async_docs
    page1_data = {"data": [{"id": "async_doc1"}], "meta": {"next_page_url": "yes"}}
    page2_data = {"data": [{"id": "async_doc2"}], "meta": {}} # No next page
    mock_fetch_page.side_effect = [page1_data, page2_data, None] # Third call returns None

    await _fetch_all_async_docs(args, api_key, output_dir)
    
    # Assertions
    assert mock_fetch_page.call_count == 2 # Page 1, Page 2
    
    safe_docket_id = args.docket_id.replace('/', '_').replace('-', '_')
    # Check individual page saves
    mock_open_file.assert_any_call(os.path.join(output_dir, f"docket_{safe_docket_id}_page_1_async.json"), "w", encoding="utf-8")
    mock_open_file.assert_any_call(os.path.join(output_dir, f"docket_{safe_docket_id}_page_2_async.json"), "w", encoding="utf-8")
    # Check combined save
    mock_open_file.assert_any_call(os.path.join(output_dir, f"docket_{safe_docket_id}_all_documents_async.json"), "w", encoding="utf-8")

    # Check schema validation calls if schema was provided
    if args.schema:
        mock_validate_schema.assert_any_call(page1_data, args.schema)
        mock_validate_schema.assert_any_call(page2_data, args.schema)


def test_fetch_all_async_docs_functionality(docs_specific_args, tmp_path):
    """Runs the async test wrapper for _fetch_all_async_docs."""
    docs_specific_args.output_dir = str(tmp_path) # Ensure tmp_path is used
    docs_specific_args.fetch_all = True
    docs_specific_args.max_pages = 2 
    # To test schema validation:
    docs_specific_args.schema = "path/to/dummy_schema.json"

    asyncio.run(run_fetch_all_async_docs_test_wrapper(args=docs_specific_args, api_key="TESTKEY", output_dir=str(tmp_path)))


@patch('scripts.fr_client.create_sync_session')
@patch('scripts.fr_client.validate_with_schema', return_value=True)
@patch('builtins.open', new_callable=mock_open)
def test_fetch_pages_sync_docs_functionality(mock_open_file, mock_validate_schema, mock_create_session, docs_specific_args, tmp_path):
    docs_specific_args.output_dir = str(tmp_path)
    docs_specific_args.fetch_all = True
    docs_specific_args.max_pages = 2
    docs_specific_args.schema = "path/to/sync_schema.json"

    mock_session_instance = MagicMock(spec=requests.Session)
    mock_create_session.return_value = mock_session_instance

    page1_data = {"data": [{"id": "sync_doc1"}], "links": {"next": "url_to_page2"}}
    page2_data = {"data": [{"id": "sync_doc2"}], "links": {}} # No next link

    mock_response1 = MagicMock(spec=requests.Response); mock_response1.json.return_value = page1_data
    mock_response2 = MagicMock(spec=requests.Response); mock_response2.json.return_value = page2_data
    mock_session_instance.get.side_effect = [mock_response1, mock_response2]

    _fetch_pages_sync_docs(docs_specific_args, "SYNC_TEST_KEY", str(tmp_path))

    assert mock_session_instance.get.call_count == 2
    mock_session_instance.close.assert_called_once()

    safe_docket_id = docs_specific_args.docket_id.replace('/', '_').replace('-', '_')
    mock_open_file.assert_any_call(os.path.join(str(tmp_path), f"docket_{safe_docket_id}_page_1_sync.json"), "w", encoding="utf-8")
    mock_open_file.assert_any_call(os.path.join(str(tmp_path), f"docket_{safe_docket_id}_page_2_sync.json"), "w", encoding="utf-8")
    mock_open_file.assert_any_call(os.path.join(str(tmp_path), f"docket_{safe_docket_id}_all_documents_sync.json"), "w", encoding="utf-8")
    
    mock_validate_schema.assert_any_call(page1_data, docs_specific_args.schema)
    mock_validate_schema.assert_any_call(page2_data, docs_specific_args.schema)


# --- Tests for Other Generic Subcommands ---
@pytest.mark.parametrize("subcommand_details", [
    {"name": "search", "handler": run_search_subcommand, "required_args": {"term": "example_search"}, "endpoint_part": "documents"},
    {"name": "get-single", "handler": run_get_single_subcommand, "required_args": {"doc_number": "2023-00001"}, "endpoint_part": "documents/2023-00001"},
    {"name": "issues", "handler": run_issues_subcommand, "required_args": {"date_is": "2023-11-11"}, "endpoint_part": "issues"},
    {"name": "agencies", "handler": run_agencies_subcommand, "required_args": {}, "endpoint_part": "agencies"},
    {"name": "public-inspection", "handler": run_public_inspection_subcommand, "required_args": {"date_is": "2023-11-10"}, "endpoint_part": "public-inspection-documents"},
])
@patch('scripts.fr_client.create_sync_session')
@patch('scripts.fetch_fr.save_generic_json')
def test_generic_subcommand_execution(mock_save_json, mock_create_session, subcommand_details, mock_common_args, tmp_path):
    handler_func = subcommand_details["handler"]
    command_name = subcommand_details["name"]
    
    args_for_command = argparse.Namespace(
        **vars(mock_common_args),
        command=command_name,
        **subcommand_details["required_args"]
    )
    # Add default per_page, page for search if not in required_args
    if command_name == "search" and "per_page" not in args_for_command: args_for_command.per_page = 20
    if command_name == "search" and "page" not in args_for_command: args_for_command.page = 1
    if command_name == "search" and "order" not in args_for_command: args_for_command.order = "relevance"


    mock_session_instance = MagicMock(spec=requests.Session)
    mock_create_session.return_value = mock_session_instance
    
    mock_api_response_data = {"data": [{"id": "generic_item"}]}
    mock_response_obj = MagicMock(spec=requests.Response)
    mock_response_obj.json.return_value = mock_api_response_data
    mock_session_instance.get.return_value = mock_response_obj

    handler_func(args_for_command, "GENERIC_KEY", mock_session_instance, str(tmp_path))

    mock_session_instance.get.assert_called_once()
    called_url = mock_session_instance.get.call_args[0][0]
    assert f"{API_BASE}/{subcommand_details['endpoint_part']}" in called_url
    
    # Example: Check if term is in params for search
    if command_name == "search":
         assert mock_session_instance.get.call_args[1]['params']['filter[term]'] == args_for_command.term

    mock_response_obj.raise_for_status.assert_called_once()
    mock_save_json.assert_called_once_with(mock_api_response_data, command_name, args_for_command, str(tmp_path))


@patch('scripts.fr_client.create_sync_session')
def test_generic_subcommand_dry_run_mode(mock_create_session, mock_common_args, capsys):
    # Using 'agencies' as a simple example for dry run
    args_for_dry_run = argparse.Namespace(
        **vars(mock_common_args),
        command="agencies", dry_run=True
    )
    
    run_agencies_subcommand(args_for_dry_run, "DRY_RUN_API_KEY", None, args_for_dry_run.output_dir) # Session is None for dry run
    
    captured_output = capsys.readouterr().out
    assert "DRY RUN MODE for 'agencies' subcommand" in captured_output
    assert f"Endpoint URL: {API_BASE}/agencies" in captured_output
    mock_create_session.assert_not_called() # Session should not be created for dry run


# --- Test save_generic_json more directly ---
def test_save_generic_json_filename_creation(tmp_path):
    args_for_saving = argparse.Namespace(
        command="search", 
        term="complex/term with spaces", 
        agency_slugs=["epa", "dept-of-energy"],
        doc_type=["RULE"],
        # These should be excluded from filename by save_generic_json's internal logic
        output_dir=str(tmp_path), api_key="key", func=lambda x: x, schema=None, dry_run=False,
        per_page=50, page=2 # Also excluded
    )
    sample_data = {"count": 10, "results": [{"title": "Test Rule"}]}
    
    save_generic_json(sample_data, "search", args_for_saving, str(tmp_path))
    
    # Expected parts based on current save_generic_json logic
    expected_parts = [
        "search",
        "term_complex_term_with_spaces", # Slashes replaced, spaces replaced
        "agency_slugs_epa__dept_of_energy", # List items joined by __
        "doc_type_RULE"
    ]
    
    # Search for a file in tmp_path that matches these characteristics
    found = False
    for filename_in_dir in os.listdir(tmp_path):
        if all(part in filename_in_dir for part in expected_parts) and filename_in_dir.endswith(".json"):
            found = True
            # Verify content
            with open(tmp_path / filename_in_dir, 'r') as f_saved:
                assert json.load(f_saved) == sample_data
            break
    assert found, f"File with expected parts not found in {tmp_path}. Expected parts: {expected_parts}"


if __name__ == "__main__":
    pytest.main()
