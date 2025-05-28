import pytest
import os
import json
import logging
from unittest.mock import patch, MagicMock, mock_open

# Ensure scripts directory is in sys.path for fr_client import
import sys
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

# Modules to test from fr_client
try:
    from fr_client import (
        get_api_key,
        create_sync_session,
        create_async_client,
        validate_with_schema,
        API_BASE,  # Though not directly tested, good to ensure it's importable
        DEFAULT_TIMEOUT,
        requests_cache # To check its mocked state or presence
    )
    # Import requests for type checking Session
    import requests
    import httpx
    # Import jsonschema for its exceptions if available, or mock them
    try:
        import jsonschema
        from jsonschema import ValidationError as jsonschema_ValidationError
    except ImportError:
        jsonschema = None
        jsonschema_ValidationError = None # Define as None if not importable
except ImportError as e:
    print(f"Error importing from fr_client: {e}")
    pytest.fail(f"Failed to import fr_client components: {e}")


# --- Tests for get_api_key ---

def test_get_api_key_cli_provided():
    """Test get_api_key when CLI key is provided."""
    assert get_api_key(cli_api_key="cli_key_value") == "cli_key_value"

@patch('os.getenv')
def test_get_api_key_env_var_set(mock_getenv):
    """Test get_api_key when environment variable is set and no CLI key."""
    mock_getenv.return_value = "env_key_value"
    assert get_api_key(cli_api_key=None, env_var_name="TEST_API_KEY") == "env_key_value"
    mock_getenv.assert_called_once_with("TEST_API_KEY")

@patch('os.getenv')
def test_get_api_key_cli_overrides_env(mock_getenv):
    """Test CLI key overrides environment variable."""
    mock_getenv.return_value = "env_key_value" # Should not be used
    assert get_api_key(cli_api_key="cli_key_override", env_var_name="TEST_API_KEY") == "cli_key_override"
    mock_getenv.assert_not_called() # Because CLI key was provided

@patch('os.getenv')
def test_get_api_key_none_found(mock_getenv):
    """Test get_api_key returns None when no key is found."""
    mock_getenv.return_value = None
    assert get_api_key(cli_api_key=None, env_var_name="TEST_API_KEY") is None
    mock_getenv.assert_called_once_with("TEST_API_KEY")


# --- Tests for create_sync_session ---

@patch('scripts.fr_client.requests_cache.CachedSession')
def test_create_sync_session_with_cache_available(MockCachedSession, caplog):
    """Test session creation with caching enabled and requests_cache available."""
    # Mock requests_cache itself to be not None to simulate it being imported
    with patch('scripts.fr_client.requests_cache', MagicMock(spec=True)) as mock_rc_module:
        mock_rc_module.CachedSession = MockCachedSession # Assign our specific mock to it
        
        session = create_sync_session(use_cache=True)
        MockCachedSession.assert_called_once_with(
            cache_name='fr_cache',
            backend='sqlite',
            expire_after=3600,
            allowable_methods=['GET']
        )
        assert "Using requests_cache for synchronous HTTP caching." in caplog.text
        adapter = session.adapters.get("https://")
        assert isinstance(adapter.max_retries, requests.packages.urllib3.util.retry.Retry)

@patch('logging.Logger.warning') # More direct way to check logger.warning
def test_create_sync_session_with_cache_unavailable(mock_logger_warning):
    """Test session creation with caching enabled but requests_cache unavailable."""
    with patch('scripts.fr_client.requests_cache', None): # Simulate requests_cache not imported
        session = create_sync_session(use_cache=True)
        mock_logger_warning.assert_called_once_with(
            "requests_cache not installed; caching for sync requests is disabled."
        )
        assert not hasattr(session, 'cache') # Should be a regular session
        adapter = session.adapters.get("https://")
        assert isinstance(adapter.max_retries, requests.packages.urllib3.util.retry.Retry)


def test_create_sync_session_cache_disabled(caplog):
    """Test session creation with use_cache=False."""
    session = create_sync_session(use_cache=False)
    assert not hasattr(session, 'cache') # Should be a regular session
    assert "Using requests_cache" not in caplog.text # No caching message
    adapter = session.adapters.get("https://")
    assert isinstance(adapter.max_retries, requests.packages.urllib3.util.retry.Retry)


def test_create_sync_session_retry_strategy():
    """Verify Retry strategy is configured correctly."""
    session = create_sync_session(use_cache=False) # Cache not relevant here
    adapter = session.adapters.get("https://") # Check for https
    retry_strategy = adapter.max_retries
    
    from scripts.fr_client import RETRIES, BACKOFF_FACTOR, STATUS_FORCELIST
    assert retry_strategy.total == RETRIES
    assert retry_strategy.read == RETRIES
    assert retry_strategy.connect == RETRIES
    assert retry_strategy.backoff_factor == BACKOFF_FACTOR
    assert retry_strategy.status_forcelist == STATUS_FORCELIST
    assert 'GET' in retry_strategy.allowed_methods
    assert 'POST' in retry_strategy.allowed_methods


# --- Tests for create_async_client ---

def test_create_async_client_instance_and_timeout():
    """Verify it returns an httpx.AsyncClient instance with correct timeout."""
    client = create_async_client()
    assert isinstance(client, httpx.AsyncClient)
    assert client.timeout.connect == DEFAULT_TIMEOUT # httpx default has multiple timeout phases
    assert client.timeout.read == DEFAULT_TIMEOUT
    assert client.timeout.write == DEFAULT_TIMEOUT
    assert client.timeout.pool is None # Default pool timeout


# --- Tests for validate_with_schema ---

@patch('builtins.open', new_callable=mock_open, read_data='{"type": "object"}')
@patch('json.load')
@patch('scripts.fr_client.jsonschema.validate') # Mock the validate function itself
def test_validate_with_schema_successful(mock_js_validate, mock_json_load, mock_file_open, caplog):
    """Test successful validation."""
    mock_json_load.return_value = {"type": "object"} # Schema content
    instance_data = {"key": "value"}
    schema_file_path = "dummy_schema.json"
    
    with caplog.at_level(logging.INFO):
        result = validate_with_schema(instance_data, schema_file_path)
    
    assert result is True
    mock_file_open.assert_called_once_with(schema_file_path, 'r', encoding='utf-8')
    mock_json_load.assert_called_once()
    mock_js_validate.assert_called_once_with(instance=instance_data, schema={"type": "object"})
    assert f"Instance successfully validated against schema: {schema_file_path}" in caplog.text


def test_validate_with_schema_path_none():
    """Test with schema_path=None (should return True and not attempt to open/validate)."""
    assert validate_with_schema({"key": "value"}, None) is True


@patch('logging.Logger.warning')
def test_validate_with_schema_jsonschema_unavailable(mock_logger_warning):
    """Test with jsonschema library mocked as unavailable."""
    with patch('scripts.fr_client.jsonschema', None):
        result = validate_with_schema({"key": "value"}, "some_schema.json")
        assert result is True
        mock_logger_warning.assert_called_once_with(
            "JSON schema validation requested but 'jsonschema' library not installed."
        )

@patch('builtins.open', side_effect=FileNotFoundError("Schema not found"))
def test_validate_with_schema_file_not_found(mock_file_open, caplog):
    """Test FileNotFoundError for schema file."""
    schema_file_path = "non_existent_schema.json"
    with caplog.at_level(logging.ERROR):
        result = validate_with_schema({"key": "value"}, schema_file_path)
    assert result is False
    mock_file_open.assert_called_once_with(schema_file_path, 'r', encoding='utf-8')
    assert f"Schema file not found: {schema_file_path}" in caplog.text

@patch('builtins.open', new_callable=mock_open, read_data='invalid json')
@patch('json.load', side_effect=json.JSONDecodeError("Decode error", "doc", 0))
def test_validate_with_schema_json_decode_error(mock_json_load, mock_file_open, caplog):
    """Test json.JSONDecodeError for schema file."""
    schema_file_path = "bad_schema.json"
    with caplog.at_level(logging.ERROR):
        result = validate_with_schema({"key": "value"}, schema_file_path)
    assert result is False
    assert f"Error decoding schema file {schema_file_path}" in caplog.text

@patch('builtins.open', new_callable=mock_open, read_data='{"type": "object"}')
@patch('json.load')
@patch('scripts.fr_client.jsonschema.validate')
def test_validate_with_schema_validation_error(mock_js_validate, mock_json_load, mock_file_open, caplog):
    """Test jsonschema.ValidationError during validation."""
    # Ensure jsonschema_ValidationError is not None for this test
    if not jsonschema_ValidationError:
        pytest.skip("jsonschema library not available, skipping ValidationError test")

    mock_json_load.return_value = {"type": "object"}
    # Create a mock error object similar to what jsonschema.ValidationError would be
    validation_error_instance = jsonschema_ValidationError("Instance is not valid")
    mock_js_validate.side_effect = validation_error_instance
    
    schema_file_path = "schema.json"
    with caplog.at_level(logging.ERROR):
        result = validate_with_schema({"key": "value"}, schema_file_path)
    
    assert result is False
    assert f"Schema validation error against {schema_file_path}: Instance is not valid" in caplog.text


if __name__ == "__main__":
    pytest.main()
