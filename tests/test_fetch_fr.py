import pytest
import os
import sys
import json
import argparse
import asyncio
import logging
from unittest.mock import patch, MagicMock, mock_open, call
import re # For regex matching in logs

# Add scripts directory to sys.path
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

# Modules to test from fetch_fr
try:
    from fetch_fr import (
        main,
        save_generic_json,
        run_documents,
        run_search,
        run_get_single,
        run_generic_list_endpoint,
        run_public_inspection,
        _fetch_pages_sync_docs,
        _fetch_all_async_docs
    )
    # Import client components for mocking
    from fr_client import API_BASE, DEFAULT_DATA_DIR, DEFAULT_TIMEOUT, validate_schema
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
        api_key=None, # Default to None, main() will try to resolve or use env
        output_dir=str(tmp_path),
        verbose=False, # Test default logging
        no_cache=False,
        dry_run=False,
        command=None,
        func=None, # Will be set by specific command parsers
        schema=None,
        # These will be added by main() after resolution
        resolved_api_key=None,
        resolved_output_dir=str(tmp_path)
    )

@pytest.fixture(autouse=True)
def mock_load_dotenv_fixture():
    # The fetch_fr.py from Turn 20 does not directly call load_dotenv.
    # It's assumed fr_client or user environment handles it.
    # So, no need to mock it here unless fr_client.py itself calls it (it doesn't).
    pass


# --- Tests for Main CLI Parsing and Setup (main() function) ---

@patch('argparse.ArgumentParser.parse_args')
@patch('scripts.fetch_fr.run_documents')
@patch('scripts.fr_client.get_api_key', return_value="MOCKED_API_KEY_MAIN")
@patch('os.makedirs') # Mock os.makedirs
def test_main_dispatches_documents_and_resolves_args(mock_makedirs, mock_get_key, mock_run_docs, mock_parse_args, mock_common_args, tmp_path, caplog):
    args_for_docs = argparse.Namespace(
        **vars(mock_common_args), # Copy common args
        command="documents",
        func=run_documents,
        docket_id="TEST-DOCS-001",
        use_async=False,
        page_size=100, fetch_all=False, max_pages=0,
        api_key="CLI_KEY_TEST" # Test CLI key being passed to get_api_key
    )
    mock_parse_args.return_value = args_for_docs

    with caplog.at_level(logging.INFO):
        main()

    mock_get_key.assert_called_once_with("CLI_KEY_TEST", env_var_name='FEDREG_API_KEY')
    mock_run_docs.assert_called_once()

    called_args_obj = mock_run_docs.call_args[0][0] # The args Namespace passed to run_documents
    assert called_args_obj.resolved_api_key == "MOCKED_API_KEY_MAIN" # Resolved by main
    assert called_args_obj.resolved_output_dir == str(tmp_path)
    assert f"Using output directory: {str(tmp_path)}" in caplog.text
    mock_makedirs.assert_called_with(str(tmp_path), exist_ok=True)


@patch('argparse.ArgumentParser.parse_args')
@patch('scripts.fr_client.get_api_key', return_value=None)
@patch('sys.exit')
def test_main_no_api_key_exits(mock_sys_exit, mock_get_key, mock_parse_args, mock_common_args, caplog):
    args_no_key = argparse.Namespace(
        **vars(mock_common_args),
        api_key=None, # Explicitly None
        command="search", term="test", func=run_search, # Any command
        dry_run=False # Ensure it's not a dry run for key check
    )
    mock_parse_args.return_value = args_no_key
    
    with caplog.at_level(logging.ERROR):
        main()

    mock_get_key.assert_called_once_with(None, env_var_name='FEDREG_API_KEY')
    assert "API key is required." in caplog.text # Matches error message in main()
    mock_sys_exit.assert_called_once_with(1)


@patch('argparse.ArgumentParser.parse_args')
@patch('scripts.fr_client.get_api_key', return_value="API_KEY_LOG_TEST")
@patch('scripts.fetch_fr.run_search')
@patch('logging.basicConfig')
def test_main_logging_setup_verbose_debug(mock_basic_config, mock_run_search, mock_get_key, mock_parse_args, mock_common_args):
    # Test with --verbose (maps to DEBUG for script_logger, INFO for basicConfig in final script)
    args_verbose = argparse.Namespace(**vars(mock_common_args), verbose=True, debug=False, command="search", term="v_test", func=run_search)
    mock_parse_args.return_value = args_verbose
    with patch.object(sys.modules['scripts.fetch_fr'].script_logger, 'setLevel') as mock_script_setlevel:
        main()
    # Final script logic: verbose -> script_logger.DEBUG, basicConfig.INFO
    # The provided script sets script_logger to DEBUG if verbose.
    # And basicConfig (external) to INFO.
    # Let's verify basicConfig call for external log level
    # This is based on the final script version from Turn 20:
    # verbose=True, debug=False -> basicConfig level=INFO, script_logger level=DEBUG
    # This is a bit counter-intuitive based on typical logging.
    # The provided script has: log_level = logging.DEBUG if args.verbose else logging.INFO
    # logging.basicConfig(level=log_level, ...)
    # This means with --verbose, basicConfig (and thus external libs) go to DEBUG.
    # And script_logger also goes to DEBUG.
    # Let's test based on the code from Turn 20.
    # In Turn 20: verbose=True -> log_level=DEBUG. basicConfig(level=log_level)
    # So basicConfig should be called with DEBUG. script_logger.setLevel is also DEBUG.

    # Correcting based on Turn 20: args.verbose sets log_level to DEBUG.
    # This log_level is used for basicConfig. Script_logger is also set to this.

    # For --verbose:
    args_verbose.debug = False; args_verbose.verbose = True
    mock_parse_args.return_value = args_verbose
    mock_basic_config.reset_mock() # Reset from previous calls if any
    with patch.object(sys.modules['scripts.fetch_fr'].script_logger, 'setLevel') as mock_script_setlevel_v:
        main()
    mock_basic_config.assert_called_with(level=logging.DEBUG, format=ANY, handlers=ANY)
    mock_script_setlevel_v.assert_called_with(logging.DEBUG)


    # Test with --debug (maps to DEBUG for script_logger and basicConfig)
    args_debug = argparse.Namespace(**vars(mock_common_args), verbose=False, debug=True, command="search", term="d_test", func=run_search)
    mock_parse_args.return_value = args_debug
    mock_basic_config.reset_mock()
    with patch.object(sys.modules['scripts.fetch_fr'].script_logger, 'setLevel') as mock_script_setlevel_d:
        main()
    mock_basic_config.assert_called_with(level=logging.DEBUG, format=ANY, handlers=ANY) # Should be DEBUG
    mock_script_setlevel_d.assert_called_with(logging.DEBUG)

    # Test default (no verbose, no debug) -> INFO for script, WARNING for basicConfig
    args_default = argparse.Namespace(**vars(mock_common_args), verbose=False, debug=False, command="search", term="def_test", func=run_search)
    mock_parse_args.return_value = args_default
    mock_basic_config.reset_mock()
    with patch.object(sys.modules['scripts.fetch_fr'].script_logger, 'setLevel') as mock_script_setlevel_def:
        main()
    # Based on Turn 20: default -> basicConfig WARNING, script_logger INFO
    mock_basic_config.assert_called_with(level=logging.WARNING, format=ANY, handlers=ANY)
    mock_script_setlevel_def.assert_called_with(logging.INFO)


# --- Tests for 'documents' Subcommand (run_documents function) ---
# Fixture for documents subcommand arguments
@pytest.fixture
def docs_args(mock_common_args, tmp_path):
    return argparse.Namespace(
        **vars(mock_common_args),
        command="documents",
        docket_id="TEST-DOCKET-001",
        page_size=10,
        fetch_all=True,
        max_pages=2,
        schema=None,
        use_async=False,
        dry_run=False,
        resolved_api_key="DOCS_API_KEY",
        resolved_output_dir=str(tmp_path)
    )

# Async Path for 'documents'
@patch('scripts.fetch_fr.create_async_client')
@patch('scripts.fetch_fr._fetch_page_async_docs')
@patch('scripts.fr_client.validate_schema', return_value=True)
@patch('builtins.open', new_callable=mock_open)
async def run_async_docs_wrapper_for_test(mock_open_file, mock_validate, mock_fetch_page, mock_create_client, current_docs_args_ns):
    """Helper to execute the async part of run_documents for testing."""
    mock_async_client_instance = MagicMock(spec=httpx.AsyncClient)
    mock_async_client_instance.__aenter__.return_value = mock_async_client_instance
    mock_async_client_instance.__aexit__.return_value = None
    mock_create_client.return_value = mock_async_client_instance

    page1_data = {"data": [{"id": "doc1"}], "meta": {"pagination": {"total_pages": 2, "current_page": 1}}}
    page2_data = {"data": [{"id": "doc2"}], "meta": {"pagination": {"total_pages": 2, "current_page": 2}}}
    mock_fetch_page.side_effect = [page1_data, page2_data, None]

    await _fetch_all_async_docs(current_docs_args_ns, current_docs_args_ns.resolved_api_key, current_docs_args_ns.resolved_output_dir)
    return mock_fetch_page, mock_open_file, mock_validate


def test_run_documents_async_pagination_output_schema(docs_args, tmp_path, caplog):
    docs_args.use_async = True
    docs_args.fetch_all = True
    docs_args.max_pages = 2
    docs_args.schema = "dummy_schema.json"

    mock_fetch_page, mock_open_file, mock_validate = asyncio.run(
        run_async_docs_wrapper_for_test(current_docs_args_ns=docs_args)
    )

    assert mock_fetch_page.call_count == 2

    safe_docket_id = docs_args.docket_id.replace('/', '_').replace('-', '_')
    mock_open_file.assert_any_call(os.path.join(str(tmp_path), f"{safe_docket_id}_page_1.json"), "w", encoding="utf-8")
    mock_open_file.assert_any_call(os.path.join(str(tmp_path), f"{safe_docket_id}_page_2.json"), "w", encoding="utf-8")
    mock_open_file.assert_any_call(os.path.join(str(tmp_path), f"{safe_docket_id}_all_async_pages.json"), "w", encoding="utf-8")

    mock_validate.assert_any_call(mock_fetch_page.side_effect[0], docs_args.schema)
    mock_validate.assert_any_call(mock_fetch_page.side_effect[1], docs_args.schema)
    assert "Schema validation failed" not in caplog.text


# Sync Path for 'documents'
@patch('scripts.fetch_fr.create_sync_session')
@patch('scripts.fr_client.validate_schema', return_value=True)
@patch('builtins.open', new_callable=mock_open)
def test_run_documents_sync_pagination_output_schema_cache(mock_open_file, mock_validate, mock_create_session, docs_args, tmp_path, caplog):
    docs_args.use_async = False
    docs_args.fetch_all = True
    docs_args.max_pages = 2
    docs_args.schema = "dummy_sync_schema.json"
    docs_args.no_cache = False # Test with caching enabled

    mock_session_instance = MagicMock(spec=requests.Session)
    mock_create_session.return_value = mock_session_instance

    page1_data = {"data": [{"id": "sync_doc1"}], "meta": {"pagination": {"total_pages": 2, "current_page": 1}}}
    page2_data = {"data": [{"id": "sync_doc2"}], "meta": {"pagination": {"total_pages": 2, "current_page": 2}}}

    mock_response1 = MagicMock(spec=requests.Response); mock_response1.json.return_value = page1_data
    mock_response2 = MagicMock(spec=requests.Response); mock_response2.json.return_value = page2_data
    mock_session_instance.get.side_effect = [mock_response1, mock_response2]

    run_documents(docs_args)

    mock_create_session.assert_called_once_with(use_cache=True) # Cache should be used
    assert mock_session_instance.get.call_count == 2
    mock_session_instance.close.assert_called_once()

    safe_docket_id = docs_args.docket_id.replace('/', '_').replace('-', '_')
    mock_open_file.assert_any_call(os.path.join(str(tmp_path), f"{safe_docket_id}_page_1.json"), "w", encoding="utf-8")
    mock_open_file.assert_any_call(os.path.join(str(tmp_path), f"{safe_docket_id}_page_2.json"), "w", encoding="utf-8")
    mock_open_file.assert_any_call(os.path.join(str(tmp_path), f"{safe_docket_id}_all_sync_pages.json"), "w", encoding="utf-8")

    mock_validate.assert_any_call(page1_data, docs_args.schema)
    mock_validate.assert_any_call(page2_data, docs_args.schema)


def test_run_documents_dry_run_mode(docs_args, caplog): # Use caplog for dry run output
    docs_args.dry_run = True
    with caplog.at_level(logging.INFO): # Dry run logs at INFO
        run_documents(docs_args)

    # Check specific parts of the dry run log output
    log_output = caplog.text
    assert "DRY RUN: DOCUMENTS" in log_output
    assert f"'filter[docket_numbers]': '{docs_args.docket_id}'" in log_output
    assert f"Target URL: {API_BASE}/documents" in log_output


# --- Tests for Other Subcommands ---
# Parameterized test for generic subcommands and their specific handlers
@pytest.mark.parametrize("subcommand_config", [
    {"name": "search", "handler_func_name": "run_search", "required_args": {"term": "test search", "page_size":10, "fetch_all":False, "max_pages":0}, "endpoint_part": "documents"},
    {"name": "get-single", "handler_func_name": "run_get_single", "required_args": {"doc_number": "2023-TEST"}, "endpoint_part": "documents/2023-TEST"},
    {"name": "issues", "handler_func_name": "run_generic_list_endpoint", "required_args": {"page_size":5}, "endpoint_part": "issues", "is_generic": True, "generic_endpoint_name": "issues"},
    {"name": "agencies", "handler_func_name": "run_generic_list_endpoint", "required_args": {"page_size":5}, "endpoint_part": "agencies", "is_generic": True, "generic_endpoint_name": "agencies"},
    {"name": "public-inspection", "handler_func_name": "run_public_inspection", "required_args": {"date": "2023-01-01", "page_size":5}, "endpoint_part": "public-inspection-documents"}
])
@patch('scripts.fetch_fr.create_sync_session')
@patch('scripts.fetch_fr.save_generic_json')
@patch('builtins.open', new_callable=mock_open)
@patch('scripts.fr_client.validate_schema', return_value=True) # Assume schema validation passes
def test_various_subcommands_execution_and_file_output(mock_validate, mock_open_file, mock_save_json, mock_create_session, subcommand_config, mock_common_args, tmp_path, caplog):
    handler_func_name = subcommand_config["handler_func_name"]
    # Get the actual handler function from the fetch_fr module
    handler_func_to_test = getattr(sys.modules['scripts.fetch_fr'], handler_func_name)
    command_name = subcommand_config["name"]

    current_test_args = argparse.Namespace(
        **vars(mock_common_args),
        command=command_name,
        **subcommand_config["required_args"],
        resolved_api_key="SUBCOMMAND_API_KEY",
        resolved_output_dir=str(tmp_path),
        schema = "dummy_schema.json" # Test schema validation path
    )

    mock_session_instance = MagicMock(spec=requests.Session)
    mock_create_session.return_value = mock_session_instance
    
    mock_api_response_data = {"data": [{"id": f"{command_name}_item1"}]}
    mock_response_obj = MagicMock(spec=requests.Response)
    mock_response_obj.json.return_value = mock_api_response_data
    mock_session_instance.get.return_value = mock_response_obj

    with caplog.at_level(logging.INFO):
        if subcommand_config.get("is_generic", False):
            # For run_generic_list_endpoint, it needs the endpoint name as an arg
            handler_func_to_test(current_test_args, subcommand_config["generic_endpoint_name"])
        else:
            handler_func_to_test(current_test_args)

    mock_session_instance.get.assert_called_once()
    called_url = mock_session_instance.get.call_args[0][0]
    expected_endpoint_part = subcommand_config['endpoint_part']
    assert f"{API_BASE}/{expected_endpoint_part}" in called_url
    
    mock_response_obj.raise_for_status.assert_called_once()
    mock_validate.assert_called_once_with(mock_api_response_data, current_test_args.schema)

    # Assert save function calls based on handler
    if command_name in ["issues", "agencies"] or (command_name == "public-inspection" and subcommand_config.get("is_generic", False)):
        mock_save_json.assert_called_once_with(mock_api_response_data, command_name, current_test_args, str(tmp_path))
    elif command_name == "get-single":
        safe_doc_number = current_test_args.doc_number.replace('/', '_').replace('-', '_')
        mock_open_file.assert_called_once_with(os.path.join(str(tmp_path), f"document_{safe_doc_number}.json"), "w", encoding="utf-8")
    elif command_name == "search": # Search saves individual pages directly
         safe_term = "".join(c if c.isalnum() else '_' for c in current_test_args.term)
         # It saves the first page, and if fetch_all, a combined file.
         # Here, fetch_all is False by default in required_args, so only one page.
         mock_open_file.assert_any_call(os.path.join(str(tmp_path), f"search_{safe_term}_page_1.json"), "w", encoding="utf-8")
    elif command_name == "public-inspection" and not subcommand_config.get("is_generic", False): # if it has its own handler
        # This means run_public_inspection was called, which internally calls run_generic_list_endpoint
        # So save_generic_json should be called.
        mock_save_json.assert_called_once()


# --- Test Error Handling in Generic Call ---
@patch('scripts.fr_client.create_sync_session')
def test_generic_api_call_http_error(mock_create_session, mock_common_args, tmp_path, caplog):
    args = argparse.Namespace(**vars(mock_common_args), command="agencies", resolved_api_key="ERR_KEY", resolved_output_dir=str(tmp_path), schema=None, page_size=10)
    
    mock_session_instance = MagicMock(spec=requests.Session)
    mock_create_session.return_value = mock_session_instance
    mock_http_error = requests.exceptions.HTTPError("Test HTTP Error", response=MagicMock(status_code=500, text="Server Error"))
    mock_session_instance.get.side_effect = mock_http_error

    with caplog.at_level(logging.ERROR):
        run_generic_list_endpoint(args, "agencies") # Call the generic handler
    
    assert "HTTP error for 'agencies': Test HTTP Error" in caplog.text


# --- Test save_generic_json directly for filename nuances ---
def test_save_generic_json_filename_creation_robust(tmp_path):
    # More complex args to test sanitization and length limits
    args_for_save = argparse.Namespace(
        command="search",
        term="!@#$/\\&*()_+=-`~[]{}|;':\",.<>?`term with spaces and very_long_value_that_should_be_truncated",
        agency_slugs=["epa/federal", "dept-of-energy!"],
        doc_type=["RULE", "NOTICE"],
        custom_filter_ABC = "value123",
        # These should be excluded from filename by save_generic_json's internal logic
        output_dir=str(tmp_path), api_key="key", func=lambda x: x, schema=None, dry_run=False,
        per_page=50, page=2
    )
    sample_data = {"count": 10, "results": [{"title": "Test Rule"}]}

    save_generic_json(sample_data, "search", args_for_save, str(tmp_path))

    # Check for a file that contains sanitized parts and respects length limits
    found_file = None
    for f_name in os.listdir(tmp_path):
        if f_name.startswith("search_") and "term____term_with_spaces_and_very_long_value_that_s" in f_name:
            # Check some key sanitized parts
            assert "agency_slugs_epa_federal__dept_of_energy_" in f_name
            assert "doc_type_RULE__NOTICE" in f_name
            assert "custom_filter_ABC_value123" in f_name
            found_file = f_name
            break

    assert found_file is not None, f"File with expected sanitized components not found in {tmp_path}."
    with open(tmp_path / found_file, 'r') as saved_file:
        assert json.load(saved_file) == sample_data


if __name__ == "__main__": # pragma: no cover
    pytest.main()
