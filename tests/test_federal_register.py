import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import os
import json
import sys

import time # For mocking time.sleep
import requests # For requests.exceptions.HTTPError

# Adjust path to allow direct import of scripts.fetch_fr
# This assumes the test is run from the project root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.fetch_fr import (
    cmd_documents_search, save_json, sanitize_filename_part, DATA_DIR, API_BASE,
    fetch_json, MAX_RETRIES, INITIAL_BACKOFF_SECONDS, RETRY_STATUS_CODES
)

# Create a dummy argparse Namespace class for simulating args
class Args:
    def __init__(self, **kwargs):
        # Initialize all expected attributes to None or default values
        self.term = None
        self.per_page = None
        self.page = None
        self.order = None
        self.pub_date_year = None
        self.pub_date_gte = None
        self.pub_date_lte = None
        self.pub_date_is = None
        self.agency_slug = []  # Default to empty list as per argparse action='append'
        self.doc_type = []     # Default to empty list
        # Update with provided kwargs
        self.__dict__.update(kwargs)

class TestFederalRegister(unittest.TestCase):

    def setUp(self):
        # Ensure data directory exists for path joining, though files won't be written
        # In a real scenario with actual file I/O, you might clean this up in tearDown
        os.makedirs(DATA_DIR, exist_ok=True)
        # Reset mock call counts if needed, though patchers usually handle this per-test method
        pass

    def test_sanitize_filename_part(self):
        self.assertEqual(sanitize_filename_part("test term"), "test_term")
        self.assertEqual(sanitize_filename_part("test/term"), "test_term")
        self.assertEqual(sanitize_filename_part("test-term!@#$%.json"), "test-term.json")
        self.assertEqual(sanitize_filename_part("  leading and trailing  "), "leading_and_trailing")
        self.assertEqual(sanitize_filename_part("multiple__underscores--hyphens"), "multiple_underscores_hyphens")
        self.assertEqual(sanitize_filename_part(""), "") # Empty input
        self.assertEqual(sanitize_filename_part("!@#$%", is_term_for_federal_register=True), "search_results") # Becomes empty
        self.assertEqual(sanitize_filename_part("term with !@#", is_term_for_federal_register=True), "term_with_")

    @patch('scripts.fetch_fr.open', new_callable=mock_open)
    def test_save_json_documents_search_with_term(self, mock_file_open):
        test_data = {"key": "value"}
        test_term = "climate change"
        
        save_json(test_data, "documents_search", term=test_term, other_param="value")
        
        sanitized_term = sanitize_filename_part(test_term, is_term_for_federal_register=True)
        expected_filename = os.path.join(DATA_DIR, f"federal_register_{sanitized_term}.json")
        mock_file_open.assert_called_once_with(expected_filename, 'w', encoding='utf-8')
        mock_file_open().write.assert_called_once_with(json.dumps(test_data, indent=2, ensure_ascii=False))

    @patch('scripts.fetch_fr.open', new_callable=mock_open)
    def test_save_json_other_subcommand(self, mock_file_open):
        test_data = {"key": "value"}
        
        save_json(test_data, "agencies", slug="environmental-protection-agency")
        
        expected_filename = os.path.join(DATA_DIR, "agencies_slug_environmental-protection-agency.json")
        mock_file_open.assert_called_once_with(expected_filename, 'w', encoding='utf-8')
        mock_file_open().write.assert_called_once_with(json.dumps(test_data, indent=2, ensure_ascii=False))

    @patch('scripts.fetch_fr.fetch_json') # Mocking fetch_json which wraps requests.get
    @patch('scripts.fetch_fr.save_json') # Mock save_json to check its inputs
    def test_cmd_documents_search_single_term(self, mock_save_json, mock_fetch_json):
        mock_api_response = {"results": [{"title": "Test Document Education"}]}
        mock_fetch_json.return_value = mock_api_response
        
        test_term = "education policy"
        args = Args(
            term=test_term,
            # Provide all other args cmd_documents_search might access, even if None or default
            per_page="20", page=None, order="newest", 
            pub_date_year="2023", pub_date_gte=None, pub_date_lte=None, pub_date_is=None,
            agency_slug=[], doc_type=[]
        )

        cmd_documents_search(args)

        # Check that fetch_json was called (indirectly checks requests.get)
        # A more detailed check would be on the URL passed to fetch_json
        mock_fetch_json.assert_called_once()
        # Example of checking part of the URL:
        self.assertIn(f"conditions%5Bterm%5D={test_term.replace(' ', '+')}", mock_fetch_json.call_args[0][0])
        self.assertIn("per_page=20", mock_fetch_json.call_args[0][0])
        self.assertIn("order=newest", mock_fetch_json.call_args[0][0])
        self.assertIn("conditions%5Bpublication_date%5D%5Byear%5D=2023", mock_fetch_json.call_args[0][0])


        # Check that save_json was called with the correct parameters
        mock_save_json.assert_called_once_with(
            mock_api_response,
            "documents_search",
            term=test_term,
            pub_date_year="2023", 
            pub_date_is="", # or None, depending on how or "" is handled
            agency="",     # or None
            doc_type=""    # or None
        )

    @patch('scripts.fetch_fr.fetch_json') # Mocking fetch_json
    @patch('scripts.fetch_fr.save_json')  # Mocking save_json
    def test_cmd_documents_search_simulating_multiple_terms(self, mock_save_json, mock_fetch_json):
        mock_api_response_term1 = {"results": [{"title": "Test Doc Term1"}]}
        mock_api_response_term2 = {"results": [{"title": "Test Doc Term2"}]}
        
        terms = ["term1", "very specific term2"]
        
        # Simulate calls for each term
        # Call 1
        mock_fetch_json.return_value = mock_api_response_term1
        args1 = Args(term=terms[0], agency_slug=[], doc_type=[]) # ensure defaults for lists
        cmd_documents_search(args1)
        
        # Call 2
        mock_fetch_json.return_value = mock_api_response_term2
        args2 = Args(term=terms[1], agency_slug=[], doc_type=[]) # ensure defaults for lists
        cmd_documents_search(args2)

        # Assert fetch_json calls
        self.assertEqual(mock_fetch_json.call_count, 2)
        self.assertIn(f"conditions%5Bterm%5D={terms[0].replace(' ', '+')}", mock_fetch_json.call_args_list[0][0][0])
        self.assertIn(f"conditions%5Bterm%5D={terms[1].replace(' ', '+')}", mock_fetch_json.call_args_list[1][0][0])

        # Assert save_json calls
        self.assertEqual(mock_save_json.call_count, 2)
        calls_to_save_json = [
            call(mock_api_response_term1, "documents_search", term=terms[0], pub_date_year="", pub_date_is="", agency="", doc_type=""),
            call(mock_api_response_term2, "documents_search", term=terms[1], pub_date_year="", pub_date_is="", agency="", doc_type="")
        ]
        mock_save_json.assert_has_calls(calls_to_save_json, any_order=False)


    @patch('scripts.fetch_fr.fetch_json')
    @patch('scripts.fetch_fr.save_json')
    def test_cmd_documents_search_no_term(self, mock_save_json, mock_fetch_json):
        mock_api_response = {"results": "no term results"}
        mock_fetch_json.return_value = mock_api_response

        args = Args(
            term="", # Empty term
            per_page="10",
            agency_slug=["dept-of-labor"], 
            doc_type=[]
        )
        cmd_documents_search(args)

        mock_fetch_json.assert_called_once()
        # Ensure term is not in the query params if it's empty
        self.assertNotIn("conditions%5Bterm%5D", mock_fetch_json.call_args[0][0])
        self.assertIn("per_page=10", mock_fetch_json.call_args[0][0])
        self.assertIn("conditions%5Bagencies%5D%5B%5D=dept-of-labor", mock_fetch_json.call_args[0][0])


        # save_json should be called with term=""
        mock_save_json.assert_called_once_with(
            mock_api_response,
            "documents_search",
            term="",
            pub_date_year="",
            pub_date_is="",
            agency="dept-of-labor", # Check how multiple agencies are joined if applicable
            doc_type=""
        )
        # This will result in save_json using the old naming convention due to term being empty
        # e.g. documents_search_per_page_10_agency_dept-of-labor.json (actual name depends on save_json logic for empty term)

if __name__ == '__main__':
    # This allows running the tests from the command line
    unittest.main(verbosity=2)


    # New tests for fetch_json retry logic
    @patch('scripts.fetch_fr.time.sleep')
    @patch('scripts.fetch_fr.requests.get')
    def test_fetch_json_success_first_try(self, mock_requests_get, mock_time_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}
        mock_requests_get.return_value = mock_response

        result = fetch_json("http://testurl.com/success")
        
        mock_requests_get.assert_called_once_with("http://testurl.com/success", timeout=unittest.mock.ANY)
        self.assertEqual(result, {"data": "success"})
        mock_time_sleep.assert_not_called()

    @patch('scripts.fetch_fr.time.sleep')
    @patch('scripts.fetch_fr.requests.get')
    def test_fetch_json_retry_on_503_then_success(self, mock_requests_get, mock_time_sleep):
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"data": "success from retry"}

        # Create an HTTPError instance for the 503 failure
        http_error_503 = requests.exceptions.HTTPError("503 Server Error")
        mock_response_failure_503 = MagicMock()
        mock_response_failure_503.status_code = 503
        http_error_503.response = mock_response_failure_503
        
        mock_requests_get.side_effect = [
            http_error_503,
            mock_response_success
        ]

        result = fetch_json("http://testurl.com/retry_success")

        self.assertEqual(mock_requests_get.call_count, 2)
        mock_requests_get.assert_any_call("http://testurl.com/retry_success", timeout=unittest.mock.ANY)
        # time.sleep is called once after the first failure (attempt 0 in the loop)
        mock_time_sleep.assert_called_once_with(INITIAL_BACKOFF_SECONDS * (2**0)) 
        self.assertEqual(result, {"data": "success from retry"})

    @patch('scripts.fetch_fr.time.sleep')
    @patch('scripts.fetch_fr.requests.get')
    def test_fetch_json_exhausted_retries_on_persistent_503(self, mock_requests_get, mock_time_sleep):
        # Create an HTTPError instance for the persistent 503 failure
        http_error_503 = requests.exceptions.HTTPError("Persistent 503 Server Error")
        mock_response_persistent_failure_503 = MagicMock()
        mock_response_persistent_failure_503.status_code = 503
        http_error_503.response = mock_response_persistent_failure_503

        # requests.get will always raise this error
        mock_requests_get.side_effect = http_error_503 

        result = fetch_json("http://testurl.com/persistent_fail")

        self.assertEqual(mock_requests_get.call_count, MAX_RETRIES + 1)
        self.assertEqual(mock_time_sleep.call_count, MAX_RETRIES)
        
        # Check backoff times for each sleep call
        expected_sleep_calls = []
        for i in range(MAX_RETRIES):
            expected_sleep_calls.append(call(INITIAL_BACKOFF_SECONDS * (2**i)))
        mock_time_sleep.assert_has_calls(expected_sleep_calls)
        
        self.assertIsNone(result)

    @patch('scripts.fetch_fr.time.sleep')
    @patch('scripts.fetch_fr.requests.get')
    def test_fetch_json_no_retry_on_404(self, mock_requests_get, mock_time_sleep):
        # Create an HTTPError instance for the 404 failure
        http_error_404 = requests.exceptions.HTTPError("404 Not Found")
        mock_response_failure_404 = MagicMock()
        mock_response_failure_404.status_code = 404
        http_error_404.response = mock_response_failure_404
        
        mock_requests_get.side_effect = http_error_404

        result = fetch_json("http://testurl.com/notfound")

        mock_requests_get.assert_called_once_with("http://testurl.com/notfound", timeout=unittest.mock.ANY)
        mock_time_sleep.assert_not_called()
        self.assertIsNone(result)

    @patch('scripts.fetch_fr.time.sleep')
    @patch('scripts.fetch_fr.requests.get')
    def test_fetch_json_retry_on_request_exception_then_success(self, mock_requests_get, mock_time_sleep):
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"data": "success after network issue"}

        # Simulate a network error (e.g., ConnectionError)
        network_error = requests.exceptions.ConnectionError("Simulated network error")
        
        mock_requests_get.side_effect = [
            network_error,
            mock_response_success
        ]

        result = fetch_json("http://testurl.com/network_issue_then_success")

        self.assertEqual(mock_requests_get.call_count, 2)
        mock_time_sleep.assert_called_once_with(INITIAL_BACKOFF_SECONDS * (2**0))
        self.assertEqual(result, {"data": "success after network issue"})
