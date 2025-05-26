import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import shutil
import sys

# Add scripts directory to sys.path to allow direct import of fetch_congress
# This is often necessary if the scripts directory is not a package or not in PYTHONPATH
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

import fetch_congress

# Define a directory for test output
TEST_DATA_CONGRESS_DIR = os.path.join("data", "congress_test")
DUMMY_API_KEY = "TEST_API_KEY"

class TestFetchCongress(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure the base 'data' directory exists for creating 'data/congress_test'
        if not os.path.exists("data"):
            os.makedirs("data")
        # Clean up and create the test directory once before all tests
        if os.path.exists(TEST_DATA_CONGRESS_DIR):
            shutil.rmtree(TEST_DATA_CONGRESS_DIR)
        os.makedirs(TEST_DATA_CONGRESS_DIR, exist_ok=True)
        fetch_congress.CONGRESS_API_KEY = DUMMY_API_KEY # Set for the module

    @classmethod
    def tearDownClass(cls):
        # Clean up the test directory once after all tests
        if os.path.exists(TEST_DATA_CONGRESS_DIR):
            shutil.rmtree(TEST_DATA_CONGRESS_DIR)
        # Clean up the 'data' directory if it's empty and was created by setUpClass
        if os.path.exists("data") and not os.listdir("data"):
            os.rmdir("data")


    def setUp(self):
        # Set API key in environment for each test, in case a test modifies it
        os.environ["CONGRESS_API_KEY"] = DUMMY_API_KEY
        fetch_congress.CONGRESS_API_KEY = DUMMY_API_KEY # Ensure module var is also reset

        # Mock external dependencies
        self.load_dotenv_patch = patch('fetch_congress.load_dotenv')
        self.mock_load_dotenv = self.load_dotenv_patch.start()

        self.requests_get_patch = patch('fetch_congress.requests.get')
        self.mock_requests_get = self.requests_get_patch.start()

        self.logging_info_patch = patch('fetch_congress.logging.info')
        self.mock_logging_info = self.logging_info_patch.start()

        self.logging_error_patch = patch('fetch_congress.logging.error')
        self.mock_logging_error = self.logging_error_patch.start()

        self.logging_warning_patch = patch('fetch_congress.logging.warning')
        self.mock_logging_warning = self.logging_warning_patch.start()

        # Common mock response setup
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {"status": "success"}
        self.mock_requests_get.return_value = self.mock_response

        # Ensure the test directory is clean before each test
        for item in os.listdir(TEST_DATA_CONGRESS_DIR):
            item_path = os.path.join(TEST_DATA_CONGRESS_DIR, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)


    def tearDown(self):
        self.load_dotenv_patch.stop()
        self.requests_get_patch.stop()
        self.logging_info_patch.stop()
        self.logging_error_patch.stop()
        self.logging_warning_patch.stop()
        # fetch_congress.os.path.join was self.original_data_dir # Restore original join - This line removed as the mock is removed from setUp

        # Clean up environment variable
        if "CONGRESS_API_KEY" in os.environ:
            del os.environ["CONGRESS_API_KEY"]


    @patch('fetch_congress.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_json(self, mock_file_open, mock_os_makedirs):
        """Test the save_json function."""
        sample_data = {"key": "value"}
        file_prefix = "test_prefix"
        identifiers = {"id1": "val1", "id2": "val2"}

        # Temporarily override the script's data_dir for this test
        original_script_data_dir_logic = fetch_congress.os.path.join
        fetch_congress.os.path.join = MagicMock(return_value=os.path.join(TEST_DATA_CONGRESS_DIR, f"{file_prefix}_val1_val2.json"))

        fetch_congress.save_json(sample_data, file_prefix, **identifiers)

        # The 'data_dir' variable inside save_json is hardcoded to "data/congress"
        # So, os.makedirs will be called with "data/congress".
        mock_os_makedirs.assert_called_once_with("data/congress", exist_ok=True)

        expected_filename = os.path.join(TEST_DATA_CONGRESS_DIR, "test_prefix_val1_val2.json")
        mock_file_open.assert_called_once_with(expected_filename, "w")
        mock_file_open().write.assert_called_once_with(json.dumps(sample_data, indent=4))
        self.mock_logging_info.assert_any_call(f"Successfully saved data to {expected_filename}")

        # Restore original os.path.join used by the script
        fetch_congress.os.path.join = original_script_data_dir_logic


    @patch('fetch_congress.save_json')
    def test_fetch_bill_data_success(self, mock_save_json):
        """Test fetching bill data successfully."""
        congress, bill_type, bill_number = 117, "hr", 2617
        expected_url = f"{fetch_congress.CONGRESS_API_BASE_URL}/bill/{congress}/{bill_type}/{bill_number}"
        api_response_data = {"bill": "details"}
        self.mock_response.json.return_value = api_response_data

        fetch_congress.fetch_bill_data(congress, bill_type, bill_number)

        self.mock_requests_get.assert_called_once_with(
            expected_url,
            headers={"x-api-key": DUMMY_API_KEY},
            params=None,
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        mock_save_json.assert_called_once_with(
            api_response_data,
            "bill",
            congress=congress,
            bill_type=bill_type,
            bill_number=bill_number,
        )

    @patch('fetch_congress.save_json')
    def test_fetch_member_data_success(self, mock_save_json):
        """Test fetching member data successfully."""
        bioguide_id = "B001288"
        expected_url = f"{fetch_congress.CONGRESS_API_BASE_URL}/member/{bioguide_id}"
        api_response_data = {"member": "details"}
        self.mock_response.json.return_value = api_response_data

        fetch_congress.fetch_member_data(bioguide_id)

        self.mock_requests_get.assert_called_once_with(
            expected_url,
            headers={"x-api-key": DUMMY_API_KEY},
            params=None,
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        mock_save_json.assert_called_once_with(
            api_response_data, "member", bioguide_id=bioguide_id
        )

    @patch('fetch_congress.save_json')
    @patch('fetch_congress.sys.exit') # Mock sys.exit to prevent test termination
    def test_api_request_failure(self, mock_sys_exit, mock_save_json):
        """Test API request failure handling."""
        self.mock_response.status_code = 404
        self.mock_response.raise_for_status.side_effect = fetch_congress.requests.exceptions.HTTPError("404 Client Error")
        self.mock_requests_get.return_value = self.mock_response

        fetch_congress.fetch_bill_data(117, "hr", 1) # Args don't matter much here

        self.mock_logging_error.assert_called()
        mock_save_json.assert_not_called()
        mock_sys_exit.assert_called_once_with(1)


    @patch('fetch_congress.fetch_bill_data')
    def test_main_function_bill_subcommand(self, mock_fetch_bill_data):
        """Test main function routing for bill subcommand."""
        sys.argv = ["fetch_congress.py", "bill", "--congress", "117", "--bill-type", "s", "--bill-number", "123"]
        fetch_congress.main()
        mock_fetch_bill_data.assert_called_once_with(117, "s", 123)

    @patch('fetch_congress.fetch_member_data')
    def test_main_function_member_subcommand(self, mock_fetch_member_data):
        """Test main function routing for member subcommand."""
        sys.argv = ["fetch_congress.py", "member", "--bioguide-id", "A000001"]
        fetch_congress.main()
        mock_fetch_member_data.assert_called_once_with("A000001")

    def test_api_key_retrieval_and_usage(self):
        """Test that API key is correctly retrieved and used in headers."""
        # This is implicitly tested in test_fetch_bill_data_success and test_fetch_member_data_success
        # by checking the headers in mock_requests_get.assert_called_once_with.
        # We can add a specific check here if needed, but it might be redundant.
        self.assertEqual(fetch_congress.CONGRESS_API_KEY, DUMMY_API_KEY)
        # Trigger a call that uses the key
        fetch_congress.fetch_member_data("T000001")
        self.mock_requests_get.assert_called_with(
            unittest.mock.ANY, # URL
            headers={"x-api-key": DUMMY_API_KEY},
            params=None,
            timeout=fetch_congress.REQUEST_TIMEOUT
        )

    @patch('fetch_congress.sys.exit')
    def test_save_json_no_api_key(self, mock_sys_exit):
        """Test save_json exits if API key is missing."""
        original_api_key = fetch_congress.CONGRESS_API_KEY
        try:
            fetch_congress.CONGRESS_API_KEY = None # Simulate missing API key
            fetch_congress.save_json({"data": "test"}, "prefix")
            self.mock_logging_error.assert_called_with("CONGRESS_API_KEY environment variable not set.")
            mock_sys_exit.assert_called_once_with(1)
        finally:
            fetch_congress.CONGRESS_API_KEY = original_api_key # Restore

    @patch('fetch_congress.sys.exit')
    def test_make_congress_request_no_api_key(self, mock_sys_exit):
        """Test make_congress_request exits if API key is missing."""
        original_api_key = fetch_congress.CONGRESS_API_KEY
        try:
            fetch_congress.CONGRESS_API_KEY = None # Simulate missing API key
            fetch_congress.make_congress_request("/test_endpoint")
            self.mock_logging_error.assert_called_with("CONGRESS_API_KEY environment variable not set.")
            mock_sys_exit.assert_called_once_with(1)
        finally:
            fetch_congress.CONGRESS_API_KEY = original_api_key # Restore


if __name__ == "__main__":
    unittest.main()
