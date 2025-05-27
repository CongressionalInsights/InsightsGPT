import pytest
import requests
import json
import os
from unittest.mock import MagicMock, call
from datetime import datetime, timedelta

# Add project root to sys.path for module import
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts import fetch_real_time_signals

# --- Fixtures ---

@pytest.fixture
def mock_env_news_api_key(mocker):
    """Mocks the NEWS_API_KEY environment variable."""
    mocker.patch.dict(os.environ, {"NEWS_API_KEY": "TEST_NEWS_KEY"})

@pytest.fixture
def mock_env_opensecrets_api_key(mocker):
    """Mocks the OPENSECRETS_API_KEY environment variable."""
    mocker.patch.dict(os.environ, {"OPENSECRETS_API_KEY": "TEST_OPENSECRETS_KEY"})

@pytest.fixture
def mock_requests_get(mocker):
    """Fixture to mock requests.get."""
    return mocker.patch("requests.get")

@pytest.fixture
def mock_save_json_data(mocker):
    """Mocks the save_json_data function in the script."""
    return mocker.patch("scripts.fetch_real_time_signals.save_json_data")

# --- Tests for Helper Functions ---

def test_sanitize_query_for_filename():
    assert fetch_real_time_signals.sanitize_query_for_filename("Test Query!") == "Test_Query_"
    assert fetch_real_time_signals.sanitize_query_for_filename("Bill H.R. 123") == "Bill_H_R__123"
    long_query = "a" * 100
    assert len(fetch_real_time_signals.sanitize_query_for_filename(long_query)) == 50

def test_make_api_request_success(mock_requests_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "success"}
    mock_requests_get.return_value = mock_response
    
    result = fetch_real_time_signals.make_api_request("http://fakeapi.com/data")
    assert result == {"data": "success"}
    mock_requests_get.assert_called_once_with("http://fakeapi.com/data", headers=None, params=None)

def test_make_api_request_http_error(mock_requests_get, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not Found")
    mock_requests_get.return_value = mock_response

    result = fetch_real_time_signals.make_api_request("http://fakeapi.com/nonexistent")
    assert result is None
    captured = capsys.readouterr()
    assert "HTTP error during API request" in captured.out

def test_make_api_request_rate_limit_error(mock_requests_get, mocker, capsys):
    mock_response_initial = MagicMock()
    mock_response_initial.status_code = 429 # Rate limit
    # Attach the response to the exception instance
    http_error = requests.exceptions.HTTPError("Too Many Requests")
    http_error.response = mock_response_initial
    mock_response_initial.raise_for_status.side_effect = http_error # This is what raise_for_status does

    mock_requests_get.return_value = mock_response_initial
    mocker.patch("time.sleep") # Mock time.sleep to speed up test

    result = fetch_real_time_signals.make_api_request("http://fakeapi.com/ratelimited")
    assert result is None # Default behavior is to return None after waiting
    captured = capsys.readouterr()
    assert "Rate limit hit for http://fakeapi.com/ratelimited" in captured.out
    fetch_real_time_signals.time.sleep.assert_called_once_with(60)


# --- Tests for fetch_media_data ---

def test_fetch_media_data_success_one_page(mock_env_news_api_key, mock_requests_get, mock_save_json_data, mocker):
    """Test successful media data fetching, single page."""
    mocker.patch("time.sleep") # Mock time.sleep
    mock_api_response = {
        "status": "ok",
        "totalResults": 2,
        "articles": [
            {"title": "Article 1", "description": "Desc 1", "source": {"name": "Source A"}, "url": "url1", "publishedAt": "2023-01-01T12:00:00Z", "content": "Content 1"},
            {"title": "Article 2", "description": "Desc 2", "source": {"name": "Source B"}, "url": "url2", "publishedAt": "2023-01-02T12:00:00Z", "content": "Content 2"},
        ]
    }
    # Patch make_api_request within the fetch_real_time_signals module
    mock_make_request = mocker.patch("scripts.fetch_real_time_signals.make_api_request")
    mock_make_request.return_value = mock_api_response

    fetch_real_time_signals.fetch_media_data(keywords="test policy", max_articles=5)

    # Check that make_api_request was called with correct NewsAPI params
    today = datetime.now().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    expected_params = {
        "q": "test policy", "apiKey": "TEST_NEWS_KEY", "from": thirty_days_ago, "to": today,
        "language": "en", "sortBy": "relevancy", "pageSize": 5, "page": 1
    }
    mock_make_request.assert_called_once_with(fetch_real_time_signals.NEWS_API_BASE_URL, params=expected_params)

    # Check that save_json_data was called correctly
    expected_saved_articles = [
        {"title": "Article 1", "description": "Desc 1", "source_name": "Source A", "url": "url1", "published_at": "2023-01-01T12:00:00Z", "content_preview": "Content 1"},
        {"title": "Article 2", "description": "Desc 2", "source_name": "Source B", "url": "url2", "published_at": "2023-01-02T12:00:00Z", "content_preview": "Content 2"},
    ]
    expected_save_call_args = {
        "keywords": "test policy",
        "fetch_parameters": {"from_date": thirty_days_ago, "to_date": today},
        "articles": expected_saved_articles
    }
    mock_save_json_data.assert_called_once()
    # Compare dicts field by field if direct comparison fails due to order or types
    args, _ = mock_save_json_data.call_args
    assert args[0] == expected_save_call_args
    assert args[1] == "media_data"
    assert args[2] == "test_policy" # Sanitized filename slug

def test_fetch_media_data_pagination(mock_env_news_api_key, mock_requests_get, mock_save_json_data, mocker):
    """Test media data fetching with pagination."""
    mocker.patch("time.sleep")
    mock_make_request = mocker.patch("scripts.fetch_real_time_signals.make_api_request")

    # Simulate two pages of results
    mock_make_request.side_effect = [
        { # Page 1
            "status": "ok", "totalResults": 3, 
            "articles": [{"title": "Article Page1-1"}] 
        },
        { # Page 2
            "status": "ok", "totalResults": 3,
            "articles": [{"title": "Article Page2-1"}]
        },
        { # Page 3 (empty, or could be fewer than pageSize)
            "status": "ok", "totalResults": 3,
            "articles": [{"title": "Article Page3-1"}]
        }
    ]
    
    # max_articles = 3, pageSize for API calls will be 3 (min(NEWS_API_PAGE_SIZE, max_articles))
    # But the internal loop for fetching articles is based on `max_articles`.
    # The NewsAPI `pageSize` param will be set to min(100, 3) = 3.
    # So, one article per page, needing 3 pages.

    fetch_real_time_signals.fetch_media_data(keywords="pagination test", max_articles=3)

    assert mock_make_request.call_count == 3
    # pageSize should be 3 for all calls
    for i in range(3):
        _, kwargs = mock_make_request.call_args_list[i]
        assert kwargs['params']['pageSize'] == 3
        assert kwargs['params']['page'] == i + 1
    
    mock_save_json_data.assert_called_once()
    args, _ = mock_save_json_data.call_args
    assert len(args[0]["articles"]) == 3 # 3 articles fetched in total

def test_fetch_media_data_no_api_key(mocker, capsys):
    """Test media data fetching when NEWS_API_KEY is not set."""
    mocker.patch.dict(os.environ, clear=True)
    mocker.patch("scripts.fetch_real_time_signals.NEWS_API_KEY", None) # Ensure module var is None
    
    mock_save = mocker.patch("scripts.fetch_real_time_signals.save_json_data")

    fetch_real_time_signals.fetch_media_data(keywords="any")
    
    captured = capsys.readouterr()
    assert "NEWS_API_KEY environment variable not set" in captured.out
    mock_save.assert_not_called()

def test_fetch_media_data_api_error(mock_env_news_api_key, mocker, capsys):
    """Test media data fetching when API returns an error."""
    mocker.patch("time.sleep")
    mock_make_request = mocker.patch("scripts.fetch_real_time_signals.make_api_request")
    mock_make_request.return_value = {"status": "error", "message": "API Key Invalid"}
    
    mock_save = mocker.patch("scripts.fetch_real_time_signals.save_json_data")

    fetch_real_time_signals.fetch_media_data(keywords="api error test")
    
    captured = capsys.readouterr()
    assert "Failed to fetch articles or error in response: API Key Invalid" in captured.out
    mock_save.assert_not_called()


# --- Tests for fetch_lobbying_data_by_topic (Simulated) ---

def test_fetch_lobbying_data_by_topic_simulated(mock_env_opensecrets_api_key, mock_save_json_data, mocker):
    """Test the simulated lobbying data fetching."""
    mocker.patch("time.sleep") # Mock time.sleep
    
    fetch_real_time_signals.fetch_lobbying_data_by_topic(topic_or_bill_id="AI Regulation", search_type="issue")

    mock_save_json_data.assert_called_once()
    args, _ = mock_save_json_data.call_args
    
    # Check structure of simulated data
    saved_data = args[0]
    assert saved_data["query"]["term"] == "AI Regulation"
    assert saved_data["query"]["type"] == "issue"
    assert "Simulated Call" in saved_data["source"]
    assert "filings" in saved_data
    assert len(saved_data["filings"]) > 0 # Expect some simulated filings
    assert "comment" in saved_data
    
    assert args[1] == "lobbying_data" # filename_prefix
    assert args[2] == "issue_AI_Regulation" # query_slug (sanitized)

def test_fetch_lobbying_data_no_api_key(mocker, capsys):
    """Test lobbying data fetching when OPENSECRETS_API_KEY is not set."""
    # This test is for the check at the beginning of the function.
    # The current `fetch_lobbying_data_by_topic` is simulated and doesn't strictly need the key
    # to produce its simulated output, but the guard clause is there.
    mocker.patch.dict(os.environ, clear=True)
    mocker.patch("scripts.fetch_real_time_signals.OPENSECRETS_API_KEY", None)
    
    mock_save = mocker.patch("scripts.fetch_real_time_signals.save_json_data")

    fetch_real_time_signals.fetch_lobbying_data_by_topic(topic_or_bill_id="any")
    
    captured = capsys.readouterr()
    assert "OPENSECRETS_API_KEY environment variable not set" in captured.out
    mock_save.assert_not_called() # Because of the early exit due to missing key

# --- Test save_json_data interaction (using tmp_path for actual file check) ---
def test_save_json_data_actual_file(tmp_path):
    """Test save_json_data creates a file with correct content."""
    # Configure RAW_DATA_DIR to use tmp_path
    original_raw_data_dir = fetch_real_time_signals.RAW_DATA_DIR
    fetch_real_time_signals.RAW_DATA_DIR = str(tmp_path)

    sample_payload = {"test_key": "test_value"}
    prefix = "test_prefix"
    slug = "test_slug"

    fetch_real_time_signals.save_json_data(sample_payload, prefix, slug)

    # Check if file was created
    # Filename includes timestamp, so we need to find it
    saved_file = None
    for item in tmp_path.iterdir():
        if item.is_file() and item.name.startswith(f"{prefix}_{slug}_") and item.name.endswith(".json"):
            saved_file = item
            break
    
    assert saved_file is not None, "No file was saved or filename pattern mismatch."
    
    with open(saved_file, 'r') as f:
        content = json.load(f)
    assert content == sample_payload

    # Restore original RAW_DATA_DIR if necessary for other tests (though fixtures usually isolate tests)
    fetch_real_time_signals.RAW_DATA_DIR = original_raw_data_dir
