import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import shutil
import sys

# Add scripts directory to sys.path to allow direct import of fetch_govinfo
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

import fetch_govinfo

TEST_DATA_GOVINFO_DIR = os.path.join("data", "govinfo_test")
ORIGINAL_DATA_DIR = None # To store the original value of fetch_govinfo.DATA_DIR

class TestFetchGovinfo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global ORIGINAL_DATA_DIR
        ORIGINAL_DATA_DIR = fetch_govinfo.DATA_DIR # Store original
        fetch_govinfo.DATA_DIR = TEST_DATA_GOVINFO_DIR # Patch DATA_DIR for all tests

        # Ensure the base 'data' directory exists for creating 'data/govinfo_test'
        if not os.path.exists("data"):
            os.makedirs("data")
        # Clean up and create the test directory once before all tests
        if os.path.exists(TEST_DATA_GOVINFO_DIR):
            shutil.rmtree(TEST_DATA_GOVINFO_DIR)
        os.makedirs(TEST_DATA_GOVINFO_DIR, exist_ok=True)


    @classmethod
    def tearDownClass(cls):
        global ORIGINAL_DATA_DIR
        if os.path.exists(TEST_DATA_GOVINFO_DIR):
            shutil.rmtree(TEST_DATA_GOVINFO_DIR)
        # Clean up the 'data' directory if it's empty and was created by setUpClass
        if os.path.exists("data") and not os.listdir("data") and TEST_DATA_GOVINFO_DIR.startswith("data/"):
             # Only remove 'data' if it was likely created by us and is empty
            try:
                os.rmdir("data")
            except OSError:
                pass # Not empty, or some other issue, leave it.
        
        if ORIGINAL_DATA_DIR:
            fetch_govinfo.DATA_DIR = ORIGINAL_DATA_DIR # Restore original


    def setUp(self):
        # Set API key in environment for each test
        self.dummy_api_key = "TEST_KEY_GOVINFO"
        os.environ["GOVINFO_API_KEY"] = self.dummy_api_key
        fetch_govinfo.GOVINFO_API_KEY = self.dummy_api_key # Also set module level variable

        # Mock external dependencies
        self.load_dotenv_patch = patch('fetch_govinfo.load_dotenv')
        self.mock_load_dotenv = self.load_dotenv_patch.start()

        self.requests_get_patch = patch('fetch_govinfo.requests.get')
        self.mock_requests_get = self.requests_get_patch.start()

        self.logging_info_patch = patch('fetch_govinfo.logging.info')
        self.mock_logging_info = self.logging_info_patch.start()

        self.logging_error_patch = patch('fetch_govinfo.logging.error')
        self.mock_logging_error = self.logging_error_patch.start()
        
        self.logging_warning_patch = patch('fetch_govinfo.logging.warning')
        self.mock_logging_warning = self.logging_warning_patch.start()


        # Common mock response setup
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {"status": "success_mock_response"}
        self.mock_requests_get.return_value = self.mock_response

        # Clean the test data directory before each test to ensure isolation
        if os.path.exists(TEST_DATA_GOVINFO_DIR):
            shutil.rmtree(TEST_DATA_GOVINFO_DIR)
        os.makedirs(TEST_DATA_GOVINFO_DIR, exist_ok=True)


    def tearDown(self):
        self.load_dotenv_patch.stop()
        self.requests_get_patch.stop()
        self.logging_info_patch.stop()
        self.logging_error_patch.stop()
        self.logging_warning_patch.stop()

        # Clean up environment variable
        if "GOVINFO_API_KEY" in os.environ:
            del os.environ["GOVINFO_API_KEY"]
        fetch_govinfo.GOVINFO_API_KEY = None # Reset module level variable


    # --- Tests for save_json ---
    @patch('fetch_govinfo.os.makedirs', wraps=os.makedirs) # Wrap to allow actual dir creation
    @patch('builtins.open', new_callable=mock_open)
    def test_save_json_basic(self, mock_file_open, mock_os_makedirs):
        sample_data = {"test": "data"}
        file_prefix = "test_file"
        identifiers = {"id": "123"}
        
        fetch_govinfo.save_json(sample_data, file_prefix, **identifiers)
        
        expected_path = os.path.join(TEST_DATA_GOVINFO_DIR, "test_file_123.json")
        mock_os_makedirs.assert_any_call(TEST_DATA_GOVINFO_DIR, exist_ok=True)
        mock_file_open.assert_called_once_with(expected_path, "w")
        mock_file_open().write.assert_called_once_with(json.dumps(sample_data, indent=4))

    @patch('fetch_govinfo.os.makedirs', wraps=os.makedirs)
    @patch('builtins.open', new_callable=mock_open)
    def test_save_json_with_subdir(self, mock_file_open, mock_os_makedirs):
        sample_data = {"test": "data"}
        file_prefix = "test_file_subdir"
        sub_dir = "my_subdir"
        identifiers = {"code": "ABC"}

        fetch_govinfo.save_json(sample_data, file_prefix, sub_dir=sub_dir, **identifiers)
        
        expected_subdir_path = os.path.join(TEST_DATA_GOVINFO_DIR, sub_dir)
        expected_filepath = os.path.join(expected_subdir_path, "test_file_subdir_ABC.json")
        
        mock_os_makedirs.assert_any_call(expected_subdir_path, exist_ok=True)
        mock_file_open.assert_called_once_with(expected_filepath, "w")

    # --- Tests for make_govinfo_request ---
    def test_make_govinfo_request_success(self):
        endpoint = "/test_endpoint"
        params = {"param1": "value1"}
        expected_json_response = {"data": "test"}
        self.mock_response.json.return_value = expected_json_response

        response = fetch_govinfo.make_govinfo_request(endpoint, params)

        expected_url = f"{fetch_govinfo.API_BASE}{endpoint}"
        expected_api_params = params.copy()
        expected_api_params['api_key'] = self.dummy_api_key
        
        self.mock_requests_get.assert_called_once_with(
            expected_url, params=expected_api_params, timeout=fetch_govinfo.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        self.assertEqual(response, expected_json_response)

    @patch('fetch_govinfo.sys.exit')
    def test_make_govinfo_request_no_api_key(self, mock_sys_exit):
        fetch_govinfo.GOVINFO_API_KEY = None # Simulate missing API key
        fetch_govinfo.make_govinfo_request("/test")
        self.mock_logging_error.assert_called_with("GOVINFO_API_KEY environment variable not set.")
        mock_sys_exit.assert_called_once_with(1)

    def test_make_govinfo_request_http_error(self):
        self.mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=self.mock_response)
        self.mock_response.status_code = 404
        self.mock_response.text = "Not Found"
        
        response = fetch_govinfo.make_govinfo_request("/notfound")
        self.assertIsNone(response)
        self.mock_logging_error.assert_any_call(unittest.mock.ANY) # Check that some error was logged

    def test_make_govinfo_request_request_exception(self):
        self.mock_requests_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        response = fetch_govinfo.make_govinfo_request("/test")
        self.assertIsNone(response)
        self.mock_logging_error.assert_any_call(unittest.mock.ANY)


    # --- Tests for fetch_collections_data ---
    @patch('fetch_govinfo.make_govinfo_request')
    @patch('fetch_govinfo.save_json')
    def test_fetch_collections_data_success(self, mock_save_json, mock_make_request):
        sample_collections_data = {"collections": [{"code": "BILLS"}]}
        mock_make_request.return_value = sample_collections_data
        
        fetch_govinfo.fetch_collections_data()
        
        mock_make_request.assert_called_once_with("/collections")
        mock_save_json.assert_called_once_with(sample_collections_data, "collections_list")

    @patch('fetch_govinfo.make_govinfo_request', return_value=None)
    def test_fetch_collections_data_failure(self, mock_make_request):
        fetch_govinfo.fetch_collections_data()
        self.mock_logging_error.assert_called_with("Failed to fetch collections list.")

    # --- Tests for fetch_packages_data ---
    @patch('fetch_govinfo.make_govinfo_request')
    @patch('fetch_govinfo.save_json')
    def test_fetch_packages_data_success_with_filters(self, mock_save_json, mock_make_request):
        mock_args = MagicMock()
        mock_args.collection = "FR"
        mock_args.start_date = "2023-01-01"
        mock_args.end_date = "2023-01-31"
        mock_args.modified_since = "2023-01-01T00:00:00Z"
        mock_args.page_size = 50
        mock_args.offset_mark = "AoM="
        
        sample_packages_data = {"packages": []}
        mock_make_request.return_value = sample_packages_data

        fetch_govinfo.fetch_packages_data(mock_args)

        expected_params = {
            "collection": "FR",
            "dateIssuedStartDate": "2023-01-01",
            "dateIssuedEndDate": "2023-01-31",
            "modifiedSince": "2023-01-01T00:00:00Z",
            "pageSize": 50,
            "offsetMark": "AoM="
        }
        mock_make_request.assert_called_once_with("/packages", params=expected_params)
        
        expected_identifiers = {
            "collection": "FR", 
            "start_date": "2023-01-01", 
            "end_date": "2023-01-31",
            "modified_since": "20230101T000000Z" # Filename friendly
        }
        mock_save_json.assert_called_once_with(
            sample_packages_data, "packages_list", sub_dir="packages", **expected_identifiers
        )

    @patch('fetch_govinfo.make_govinfo_request')
    @patch('fetch_govinfo.save_json')
    def test_fetch_packages_data_success_no_optional_filters(self, mock_save_json, mock_make_request):
        mock_args = MagicMock(
            collection=None, start_date=None, end_date=None, modified_since=None, 
            page_size=100, offset_mark="*" # Defaults from argparse
        )
        sample_packages_data = {"packages": ["default_package"]}
        mock_make_request.return_value = sample_packages_data

        fetch_govinfo.fetch_packages_data(mock_args)
        expected_params = {"pageSize": 100, "offsetMark": "*"}
        mock_make_request.assert_called_once_with("/packages", params=expected_params)
        mock_save_json.assert_called_once_with(
            sample_packages_data, "packages_list", sub_dir="packages" # No extra identifiers
        )


    @patch('fetch_govinfo.make_govinfo_request', return_value=None)
    def test_fetch_packages_data_failure(self, mock_make_request):
        mock_args = MagicMock(collection="BILLS", start_date=None, end_date=None, modified_since=None, page_size=100, offset_mark="*")
        fetch_govinfo.fetch_packages_data(mock_args)
        self.mock_logging_error.assert_called_with(f"Failed to fetch packages for filters: {{'collection': 'BILLS'}}")


    # --- Tests for fetch_package_summary_data ---
    @patch('fetch_govinfo.make_govinfo_request')
    @patch('fetch_govinfo.save_json')
    def test_fetch_package_summary_data_success(self, mock_save_json, mock_make_request):
        mock_args = MagicMock(package_id="TEST-PKG-ID-001")
        sample_summary_data = {"summary": "details"}
        mock_make_request.return_value = sample_summary_data

        fetch_govinfo.fetch_package_summary_data(mock_args)
        
        expected_endpoint = f"/packages/{mock_args.package_id}/summary"
        mock_make_request.assert_called_once_with(expected_endpoint)
        
        safe_package_id = "TEST_PKG_ID_001"
        mock_save_json.assert_called_once_with(
            sample_summary_data, 
            "package_summary", 
            sub_dir=f"summaries/{mock_args.package_id}", 
            package_id=safe_package_id
        )

    @patch('fetch_govinfo.make_govinfo_request', return_value=None)
    def test_fetch_package_summary_data_failure(self, mock_make_request):
        mock_args = MagicMock(package_id="FAIL-PKG-ID")
        fetch_govinfo.fetch_package_summary_data(mock_args)
        self.mock_logging_error.assert_called_with(f"Failed to fetch summary for package ID: {mock_args.package_id}")


    # --- Tests for main function routing ---
    @patch('fetch_govinfo.fetch_collections_data')
    def test_main_collections_command(self, mock_fetch_collections):
        sys.argv = ["fetch_govinfo.py", "collections"]
        fetch_govinfo.main()
        mock_fetch_collections.assert_called_once()

    @patch('fetch_govinfo.fetch_packages_data')
    def test_main_packages_command(self, mock_fetch_packages):
        sys.argv = [
            "fetch_govinfo.py", "packages", 
            "--collection", "FR", 
            "--start-date", "2023-01-01",
            "--page-size", "10"
        ]
        fetch_govinfo.main()
        # Check that the mock was called, actual arg parsing is complex to assert here,
        # better to trust argparse and test the handler function directly with mock_args.
        mock_fetch_packages.assert_called_once() 
        # Example of more detailed check if needed:
        # called_args = mock_fetch_packages.call_args[0][0]
        # self.assertEqual(called_args.collection, "FR")

    @patch('fetch_govinfo.fetch_package_summary_data')
    def test_main_package_summary_command(self, mock_fetch_summary):
        sys.argv = ["fetch_govinfo.py", "package-summary", "--package-id", "PKG-ID-123"]
        fetch_govinfo.main()
        mock_fetch_summary.assert_called_once()
        called_args = mock_fetch_summary.call_args[0][0]
        self.assertEqual(called_args.package_id, "PKG-ID-123")
        
    def test_main_package_summary_missing_arg(self):
        sys.argv = ["fetch_govinfo.py", "package-summary"] # Missing --package-id
        with self.assertRaises(SystemExit): # Argparse should exit
            fetch_govinfo.main()


if __name__ == "__main__":
    unittest.main()
