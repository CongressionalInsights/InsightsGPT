import pytest
import os
import sys
import json
import logging
import argparse
from unittest.mock import patch, MagicMock, mock_open, call
import io
import contextlib

# Add scripts directory to sys.path to allow importing the script under test
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

# Now import the functions/classes from the script
try:
    from Submit_Regulation_Comment import (
        get_api_key,
        create_session,
        main,
        API_ENDPOINT, # For checking in dry run
        DEFAULT_TIMEOUT
    )
    # Import requests specifically for RequestException and Session
    import requests
except ImportError as e:
    print(f"Error importing from Submit_Regulation_Comment: {e}")
    print(f"sys.path: {sys.path}")
    pytest.fail(f"Failed to import Submit_Regulation_Comment: {e}")

# --- Fixtures ---

@pytest.fixture
def mock_args_base():
    """Provides a base Namespace object for args, can be updated in tests."""
    return argparse.Namespace(
        docket_id="TEST-0001",
        comment="This is a test comment.",
        comment_file=None,
        api_key="CLI_API_KEY", # Default to CLI key being present
        dry_run=False,
        output=None
    )

# --- Tests for get_api_key ---

def test_get_api_key_cli_provided():
    """Test get_api_key when CLI key is provided."""
    assert get_api_key("cli_key_value") == "cli_key_value"

@patch('os.getenv')
def test_get_api_key_env_var_set(mock_getenv):
    """Test get_api_key when REGGOV_API_KEY is set in environment and no CLI key."""
    mock_getenv.return_value = "env_api_key_value"
    # Pass None for cli_key to simulate it not being provided
    assert get_api_key(None) == "env_api_key_value"
    mock_getenv.assert_called_once_with("REGGOV_API_KEY")

@patch('os.getenv')
def test_get_api_key_cli_overrides_env_var(mock_getenv):
    """Test get_api_key when CLI key is provided, it overrides env var."""
    mock_getenv.return_value = "env_api_key_value"
    assert get_api_key("cli_key_value_override") == "cli_key_value_override"
    # os.getenv should not be called if cli_key is present
    mock_getenv.assert_not_called()


@patch('os.getenv')
def test_get_api_key_none_provided(mock_getenv):
    """Test get_api_key when no key is provided via CLI or environment."""
    mock_getenv.return_value = None
    assert get_api_key(None) is None
    mock_getenv.assert_called_once_with("REGGOV_API_KEY")

# --- Tests for create_session ---

def test_create_session_returns_session_instance():
    """Test that create_session returns a requests.Session instance."""
    session = create_session()
    assert isinstance(session, requests.Session)

def test_create_session_retry_adapter_mounted():
    """Test that an HTTPAdapter with Retry strategy is mounted for https and http."""
    session = create_session()
    adapter_https = session.get_adapter("https://")
    adapter_http = session.get_adapter("http://")
    
    assert isinstance(adapter_https, requests.adapters.HTTPAdapter)
    assert isinstance(adapter_https.max_retries, requests.packages.urllib3.util.retry.Retry)
    
    assert isinstance(adapter_http, requests.adapters.HTTPAdapter)
    assert isinstance(adapter_http.max_retries, requests.packages.urllib3.util.retry.Retry)


def test_create_session_retry_parameters():
    """Test the Retry strategy parameters."""
    retries_val = 5
    backoff_factor_val = 0.5
    status_forcelist_val = (500, 503) # Tuple
    
    session = create_session(retries=retries_val, backoff_factor=backoff_factor_val, status_forcelist=status_forcelist_val)
    adapter = session.get_adapter("https://") # Check one, as both http/https use same adapter instance
    retry_strategy = adapter.max_retries
    
    assert retry_strategy.total == retries_val
    assert retry_strategy.backoff_factor == backoff_factor_val
    assert retry_strategy.status_forcelist == status_forcelist_val
    assert "POST" in retry_strategy.allowed_methods # Check if POST is in allowed_methods

# --- Tests for main() function ---

class TestMainFunctionScenarios:

    @patch('argparse.ArgumentParser.parse_args')
    @patch('Submit_Regulation_Comment.get_api_key') # Mock the function within the script's context
    @patch('sys.exit')
    def test_main_no_api_key(self, mock_sys_exit, mock_script_get_api_key, mock_parse_args, caplog, mock_args_base):
        """Test main() when no API key is available."""
        mock_args_base.api_key = None # CLI arg is None
        mock_parse_args.return_value = mock_args_base
        mock_script_get_api_key.return_value = None # Simulate get_api_key finding no key

        with caplog.at_level(logging.ERROR): # Ensure logging is captured
            main()
        
        mock_script_get_api_key.assert_called_once_with(None) # Called with None as cli_key
        assert "No API key provided" in caplog.text
        mock_sys_exit.assert_called_once_with(1)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('Submit_Regulation_Comment.get_api_key', return_value="DUMMY_API_KEY_FROM_GET")
    @patch('Submit_Regulation_Comment.create_session') 
    @patch('sys.exit') 
    def test_main_comment_from_text_dry_run(self, mock_sys_exit, mock_create_session, mock_get_api_key, mock_parse_args, mock_args_base, caplog):
        """Test main() with comment from text in dry-run mode."""
        mock_args_base.comment = "Direct comment text for dry run"
        mock_args_base.comment_file = None
        mock_args_base.dry_run = True
        mock_parse_args.return_value = mock_args_base
        
        mock_session_instance = MagicMock(spec=requests.Session) # Use spec for stricter mocking
        mock_create_session.return_value = mock_session_instance

        # Capture stdout
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            with caplog.at_level(logging.INFO): # Capture info logs
                main()
            dry_run_output = buf.getvalue()

        assert "DRY RUN MODE" in dry_run_output
        assert f"Endpoint: {API_ENDPOINT}" in dry_run_output
        assert "'X-API-Key': 'DUMMY_API_KEY_FROM_GET'" in dry_run_output
        assert f'"docketId": "{mock_args_base.docket_id}"' in dry_run_output
        assert f'"body": "{mock_args_base.comment}"' in dry_run_output
        
        mock_session_instance.post.assert_not_called() 
        mock_sys_exit.assert_called_once_with(0)
        assert f"Prepared comment for docket {mock_args_base.docket_id}" in caplog.text


    @patch('argparse.ArgumentParser.parse_args')
    @patch('Submit_Regulation_Comment.get_api_key', return_value="DUMMY_API_KEY_FILE")
    @patch('builtins.open', new_callable=mock_open, read_data="Comment from file for dry run.")
    @patch('Submit_Regulation_Comment.create_session')
    @patch('sys.exit')
    def test_main_comment_from_file_dry_run(self, mock_sys_exit, mock_create_session, mock_file_open, mock_get_api_key, mock_parse_args, mock_args_base):
        """Test main() with comment from file in dry-run mode."""
        comment_file_path = "test_comment_dry.txt"
        mock_args_base.comment = None
        mock_args_base.comment_file = comment_file_path
        mock_args_base.dry_run = True
        mock_parse_args.return_value = mock_args_base

        mock_session_instance = MagicMock(spec=requests.Session)
        mock_create_session.return_value = mock_session_instance

        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            main()
            dry_run_output = buf.getvalue()
        
        mock_file_open.assert_called_once_with(comment_file_path, "r", encoding="utf-8")
        assert '"body": "Comment from file for dry run."' in dry_run_output
        mock_session_instance.post.assert_not_called()
        mock_sys_exit.assert_called_once_with(0)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('Submit_Regulation_Comment.get_api_key', return_value="DUMMY_API_KEY_IO_ERROR")
    @patch('builtins.open', side_effect=IOError("Mocked File Read Error"))
    @patch('sys.exit')
    def test_main_comment_file_read_error(self, mock_sys_exit, mock_file_open, mock_get_api_key, mock_parse_args, mock_args_base, caplog):
        """Test main() when comment file reading fails."""
        comment_file_path_error = "bad_read_file.txt"
        mock_args_base.comment = None
        mock_args_base.comment_file = comment_file_path_error
        mock_parse_args.return_value = mock_args_base

        with caplog.at_level(logging.ERROR):
            main()

        mock_file_open.assert_called_once_with(comment_file_path_error, "r", encoding="utf-8")
        assert "Failed to read comment file: Mocked File Read Error" in caplog.text
        mock_sys_exit.assert_called_once_with(1)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('Submit_Regulation_Comment.get_api_key', return_value="DUMMY_API_KEY_SUCCESS")
    @patch('Submit_Regulation_Comment.create_session')
    def test_main_successful_submission_console_output(self, mock_create_session, mock_get_api_key, mock_parse_args, mock_args_base, caplog):
        """Test successful API submission with console output."""
        mock_args_base.comment = "Successful console comment"
        mock_args_base.output = None # Ensure console output
        mock_parse_args.return_value = mock_args_base

        mock_session_instance = MagicMock(spec=requests.Session)
        mock_create_session.return_value = mock_session_instance
        
        mock_api_response = MagicMock(spec=requests.Response)
        mock_api_response.status_code = 201 
        mock_response_content_json = {"data": {"id": "COMMENT-ID-CONSOLE-123"}}
        mock_api_response.json.return_value = mock_response_content_json
        mock_session_instance.post.return_value = mock_api_response

        with io.StringIO() as buf_stdout, contextlib.redirect_stdout(buf_stdout): 
            with caplog.at_level(logging.INFO):
                main()
            captured_stdout = buf_stdout.getvalue()
        
        mock_session_instance.post.assert_called_once()
        _, kwargs_post = mock_session_instance.post.call_args
        assert kwargs_post['json']['data']['attributes']['body'] == "Successful console comment"
        assert kwargs_post['headers']['X-API-Key'] == "DUMMY_API_KEY_SUCCESS"
        assert kwargs_post['timeout'] == DEFAULT_TIMEOUT
        
        mock_api_response.raise_for_status.assert_called_once()
        
        assert f"Prepared comment for docket {mock_args_base.docket_id}" in caplog.text
        assert "Comment submitted successfully. ID: COMMENT-ID-CONSOLE-123" in caplog.text
        assert json.dumps(mock_response_content_json, indent=2) in captured_stdout


    @patch('argparse.ArgumentParser.parse_args')
    @patch('Submit_Regulation_Comment.get_api_key', return_value="DUMMY_API_KEY_FILE_OUT")
    @patch('Submit_Regulation_Comment.create_session')
    @patch('builtins.open', new_callable=mock_open) # Mock open for the output JSON file
    def test_main_successful_submission_file_output(self, mock_output_file_open, mock_create_session, mock_get_api_key, mock_parse_args, mock_args_base, caplog):
        """Test successful API submission with file output."""
        output_json_file_path = "response_output.json"
        mock_args_base.output = output_json_file_path
        mock_parse_args.return_value = mock_args_base

        mock_session_instance = MagicMock(spec=requests.Session)
        mock_create_session.return_value = mock_session_instance
        
        mock_api_response = MagicMock(spec=requests.Response)
        mock_api_response.status_code = 201
        mock_response_content_json_file = {"data": {"id": "COMMENT-ID-FILE-456"}}
        mock_api_response.json.return_value = mock_response_content_json_file
        mock_session_instance.post.return_value = mock_api_response

        with caplog.at_level(logging.INFO):
            main()
            
        mock_session_instance.post.assert_called_once()
        # Check that open was called for the output file
        mock_output_file_open.assert_called_once_with(output_json_file_path, "w", encoding="utf-8")
        
        # Check that json.dump was called correctly (via the write method of the mock_open handle)
        # json.dump writes in chunks. We can check the content written.
        # The handle is mock_output_file_open()
        handle = mock_output_file_open()
        # Concatenate all arguments from all .write calls
        written_data_str = "".join(c_args[0] for c_args, _ in handle.write.call_args_list)
        assert json.loads(written_data_str) == mock_response_content_json_file
        
        assert f"Response saved to {output_json_file_path}" in caplog.text

    @patch('argparse.ArgumentParser.parse_args')
    @patch('Submit_Regulation_Comment.get_api_key', return_value="DUMMY_API_KEY_REQ_EXC")
    @patch('Submit_Regulation_Comment.create_session')
    @patch('sys.exit')
    def test_main_api_request_exception(self, mock_sys_exit, mock_create_session, mock_get_api_key, mock_parse_args, mock_args_base, caplog):
        """Test main() when API request raises RequestException."""
        mock_parse_args.return_value = mock_args_base
        
        mock_session_instance = MagicMock(spec=requests.Session)
        mock_create_session.return_value = mock_session_instance
        mock_session_instance.post.side_effect = requests.exceptions.RequestException("Mocked Network Error")

        with caplog.at_level(logging.ERROR):
            main()
            
        mock_session_instance.post.assert_called_once()
        assert "Submission failed: Mocked Network Error" in caplog.text
        mock_sys_exit.assert_called_once_with(1)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('Submit_Regulation_Comment.get_api_key', return_value="DUMMY_API_KEY_HTTP_ERR")
    @patch('Submit_Regulation_Comment.create_session')
    @patch('sys.exit')
    def test_main_api_http_error(self, mock_sys_exit, mock_create_session, mock_get_api_key, mock_parse_args, mock_args_base, caplog):
        """Test main() when API returns an HTTP error status that raise_for_status handles."""
        mock_parse_args.return_value = mock_args_base
        
        mock_session_instance = MagicMock(spec=requests.Session)
        mock_create_session.return_value = mock_session_instance
        
        mock_api_response_http_error = MagicMock(spec=requests.Response)
        mock_api_response_http_error.status_code = 403 # Forbidden
        # Configure raise_for_status to throw an HTTPError
        mock_api_response_http_error.raise_for_status.side_effect = requests.exceptions.HTTPError("Client Error: Forbidden for url")
        mock_session_instance.post.return_value = mock_api_response_http_error
        
        with caplog.at_level(logging.ERROR):
            main()

        mock_session_instance.post.assert_called_once()
        mock_api_response_http_error.raise_for_status.assert_called_once()
        assert "Submission failed: Client Error: Forbidden for url" in caplog.text
        mock_sys_exit.assert_called_once_with(1)


if __name__ == "__main__":
    pytest.main()
