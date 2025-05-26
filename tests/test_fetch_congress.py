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
    def test_fetch_member_data_success_by_bioguide_id(self, mock_save_json):
        """Test fetching member data successfully by Bioguide ID."""
        bioguide_id = "B001288"
        # Endpoint is now /member, bioguideId is a param
        expected_url = f"{fetch_congress.CONGRESS_API_BASE_URL}/member"
        expected_params = {"bioguideId": bioguide_id}
        api_response_data = {"member": "details"}
        self.mock_response.json.return_value = api_response_data

        fetch_congress.fetch_member_data(bioguide_id=bioguide_id)

        self.mock_requests_get.assert_called_once_with(
            expected_url,
            headers={"x-api-key": DUMMY_API_KEY},
            params=expected_params, # Check params
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        mock_save_json.assert_called_once_with(
            api_response_data, "member_data", bioguide_id=bioguide_id # Prefix changed
        )

    @patch('fetch_congress.save_json')
    def test_fetch_member_data_success_with_other_filters(self, mock_save_json):
        """Test fetching member data successfully with other filters."""
        api_response_data = {"members": ["member1", "member2"]}
        self.mock_response.json.return_value = api_response_data

        filters = {"congress": 117, "state_code": "CA", "sponsorship": True}
        expected_params = {"congress": 117, "stateCode": "CA", "sponsorship": "true"}
        expected_identifiers = {"congress": 117, "state_code": "CA", "sponsorship": "true"}


        fetch_congress.fetch_member_data(**filters)

        self.mock_requests_get.assert_called_once_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/member",
            headers={"x-api-key": DUMMY_API_KEY},
            params=expected_params,
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        mock_save_json.assert_called_once_with(
            api_response_data, "member_data", **expected_identifiers
        )

    @patch('fetch_congress.sys.exit')
    @patch('fetch_congress.save_json')
    def test_fetch_member_data_no_filters_provided(self, mock_save_json, mock_sys_exit):
        """Test fetch_member_data exits if no filters are provided."""
        fetch_congress.fetch_member_data() # Call with all defaults
        self.mock_logging_error.assert_called_with(
            "No filters provided for member command. Please provide at least one filter."
        )
        mock_sys_exit.assert_called_once_with(1)
        mock_save_json.assert_not_called()
    
    @patch('fetch_congress.save_json')
    @patch('fetch_congress.sys.exit') # Mock sys.exit to prevent test termination
    def test_fetch_member_data_api_error(self, mock_sys_exit, mock_save_json):
        """Test API error handling for fetch_member_data."""
        self.mock_response.status_code = 404
        self.mock_response.raise_for_status.side_effect = fetch_congress.requests.exceptions.HTTPError("404 Client Error")
        self.mock_requests_get.return_value = self.mock_response

        # Call fetch_member_data with a valid filter to trigger the API call
        fetch_congress.fetch_member_data(bioguide_id="T00TEST") 

        self.mock_logging_error.assert_called() # Check that an error was logged
        mock_save_json.assert_not_called()      # Ensure save_json was not called on error
        mock_sys_exit.assert_called_once_with(1)# Ensure sys.exit was called

    # Note: test_api_request_failure might need to be generalized or removed if
    # specific error tests like test_fetch_member_data_api_error are preferred for each function.
    # For now, I'll keep it if it tests a different function or a general case.
    # The existing test_api_request_failure calls fetch_bill_data, so it's fine.

    @patch('fetch_congress.fetch_bill_data')
    def test_main_function_bill_subcommand(self, mock_fetch_bill_data):
        """Test main function routing for bill subcommand."""
        sys.argv = ["fetch_congress.py", "bill", "--congress", "117", "--bill-type", "s", "--bill-number", "123"]
        fetch_congress.main()
        mock_fetch_bill_data.assert_called_once_with(117, "s", 123)

    @patch('fetch_congress.fetch_member_data')
    def test_main_function_member_subcommand_by_bioguide_id(self, mock_fetch_member_data):
        """Test main function routing for member subcommand by Bioguide ID."""
        sys.argv = ["fetch_congress.py", "member", "--bioguide-id", "A000001"]
        fetch_congress.main()
        mock_fetch_member_data.assert_called_once_with(
            bioguide_id="A000001", 
            congress=None, 
            state_code=None, 
            district=None, 
            sponsorship=False, 
            cosponsorship=False
        )

    @patch('fetch_congress.fetch_member_data')
    def test_main_function_member_subcommand_with_other_filters(self, mock_fetch_member_data):
        """Test main function routing for member subcommand with other filters."""
        sys.argv = [
            "fetch_congress.py", "member", 
            "--congress", "117", 
            "--state-code", "CA", 
            "--sponsorship"
        ]
        fetch_congress.main()
        mock_fetch_member_data.assert_called_once_with(
            bioguide_id=None,
            congress=117,
            state_code="CA",
            district=None,
            sponsorship=True,
            cosponsorship=False,
        )

    @patch('fetch_congress.fetch_member_data')
    @patch('fetch_congress.logging.error') # Also mock logging to check error message
    @patch('fetch_congress.sys.exit')    # Mock sys.exit
    def test_main_function_member_subcommand_no_filters(self, mock_sys_exit, mock_logging_error, mock_fetch_member_data):
        """Test main function routing for member subcommand with no filters (should trigger error in fetch_member_data)."""
        sys.argv = ["fetch_congress.py", "member"]
        fetch_congress.main()
        # fetch_member_data will be called with all Nones/False, which then logs error and exits
        mock_fetch_member_data.assert_called_once_with(
            bioguide_id=None, congress=None, state_code=None, district=None, sponsorship=False, cosponsorship=False
        )
        # The actual error logging and exit are tested in test_fetch_member_data_no_filters_provided
        # Here, we just ensure main correctly calls the handler which then fails.


    @patch('fetch_congress.fetch_bills_list_data')
    def test_main_function_bills_subcommand(self, mock_fetch_bills_list_data):
        """Test main function routing for bills (list) subcommand."""
        sys.argv = ["fetch_congress.py", "bills", "--congress", "117", "--bill-type", "hr"]
        fetch_congress.main()
        mock_fetch_bills_list_data.assert_called_once_with(congress=117, bill_type="hr", introduced_date=None)

    @patch('fetch_congress.fetch_committee_data')
    def test_main_function_committee_subcommand(self, mock_fetch_committee_data):
        """Test main function routing for committee subcommand."""
        sys.argv = ["fetch_congress.py", "committee", "--chamber", "senate", "--congress", "118"]
        fetch_congress.main()
        mock_fetch_committee_data.assert_called_once_with(chamber="senate", congress=118, committee_code=None)

    @patch('fetch_congress.fetch_amendment_data')
    def test_main_function_amendment_subcommand_with_filters(self, mock_fetch_amendment_data):
        """Test main function routing for amendment subcommand with filters."""
        sys.argv = ["fetch_congress.py", "amendment", "--congress", "117", "--amendment-type", "samdt"]
        fetch_congress.main()
        mock_fetch_amendment_data.assert_called_once_with(congress=117, amendment_type="samdt")

    @patch('fetch_congress.fetch_amendment_data')
    def test_main_function_amendment_subcommand_no_filters(self, mock_fetch_amendment_data):
        """Test main function routing for amendment subcommand without filters."""
        sys.argv = ["fetch_congress.py", "amendment"]
        fetch_congress.main()
        mock_fetch_amendment_data.assert_called_once_with(congress=None, amendment_type=None)

    @patch('fetch_congress.fetch_committee_report_data')
    def test_main_function_committee_report_subcommand_with_filter(self, mock_fetch_committee_report_data):
        """Test main function routing for committee-report subcommand with a filter."""
        sys.argv = ["fetch_congress.py", "committee-report", "--congress", "117"]
        fetch_congress.main()
        mock_fetch_committee_report_data.assert_called_once_with(congress=117)

    @patch('fetch_congress.fetch_committee_report_data')
    def test_main_function_committee_report_subcommand_no_filter(self, mock_fetch_committee_report_data):
        """Test main function routing for committee-report subcommand without filters."""
        sys.argv = ["fetch_congress.py", "committee-report"]
        fetch_congress.main()
        mock_fetch_committee_report_data.assert_called_once_with(congress=None)

    @patch('fetch_congress.fetch_treaty_data')
    def test_main_function_treaty_subcommand_with_filter(self, mock_fetch_treaty_data):
        """Test main function routing for treaty subcommand with a filter."""
        sys.argv = ["fetch_congress.py", "treaty", "--congress", "116"]
        fetch_congress.main()
        mock_fetch_treaty_data.assert_called_once_with(congress=116)

    @patch('fetch_congress.fetch_treaty_data')
    def test_main_function_treaty_subcommand_no_filter(self, mock_fetch_treaty_data):
        """Test main function routing for treaty subcommand without filters."""
        sys.argv = ["fetch_congress.py", "treaty"]
        fetch_congress.main()
        mock_fetch_treaty_data.assert_called_once_with(congress=None)

    @patch('fetch_congress.fetch_nomination_data')
    def test_main_function_nomination_subcommand(self, mock_fetch_nomination_data):
        """Test main function routing for nomination subcommand."""
        sys.argv = ["fetch_congress.py", "nomination", "--congress", "117"]
        fetch_congress.main()
        mock_fetch_nomination_data.assert_called_once_with(congress=117)

    def test_main_function_nomination_subcommand_missing_congress(self):
        """Test main function for nomination subcommand fails if --congress is missing."""
        sys.argv = ["fetch_congress.py", "nomination"]
        with self.assertRaises(SystemExit): # Argparse calls sys.exit on error
            fetch_congress.main()

    @patch('fetch_congress.fetch_congressional_record_data')
    def test_main_function_congressional_record_subcommand_with_filters(self, mock_fetch_cr_data):
        """Test main function routing for congressional-record subcommand with filters."""
        sys.argv = ["fetch_congress.py", "congressional-record", "--congress", "117", "--date", "2023-01-01"]
        fetch_congress.main()
        mock_fetch_cr_data.assert_called_once_with(congress=117, date="2023-01-01")

    @patch('fetch_congress.fetch_congressional_record_data')
    def test_main_function_congressional_record_subcommand_no_filters(self, mock_fetch_cr_data):
        """Test main function routing for congressional-record subcommand without filters."""
        sys.argv = ["fetch_congress.py", "congressional-record"]
        fetch_congress.main()
        mock_fetch_cr_data.assert_called_once_with(congress=None, date=None)

    @patch('fetch_congress.fetch_senate_communication_data')
    def test_main_function_senate_communication_subcommand_with_filters(self, mock_fetch_sc_data):
        """Test main function routing for senate-communication subcommand with filters."""
        sys.argv = [
            "fetch_congress.py", "senate-communication", 
            "--congress", "117", 
            "--type", "ec", 
            "--from-date", "2023-01-01", 
            "--to-date", "2023-01-31"
        ]
        fetch_congress.main()
        mock_fetch_sc_data.assert_called_once_with(
            congress=117, communication_type="ec", from_date="2023-01-01", to_date="2023-01-31"
        )

    @patch('fetch_congress.fetch_senate_communication_data')
    def test_main_function_senate_communication_subcommand_no_filters(self, mock_fetch_sc_data):
        """Test main function routing for senate-communication subcommand without filters."""
        sys.argv = ["fetch_congress.py", "senate-communication"]
        fetch_congress.main()
        mock_fetch_sc_data.assert_called_once_with(
            congress=None, communication_type=None, from_date=None, to_date=None
        )

    def test_api_key_retrieval_and_usage(self):
        """Test that API key is correctly retrieved and used in headers."""
        # This is implicitly tested in test_fetch_bill_data_success and test_fetch_member_data_success
        # by checking the headers in mock_requests_get.assert_called_once_with.
        # We can add a specific check here if needed, but it might be redundant.
        self.assertEqual(fetch_congress.CONGRESS_API_KEY, DUMMY_API_KEY)
        # Trigger a call that uses the key with at least one filter
        fetch_congress.fetch_member_data(bioguide_id="T000001") 
        self.mock_requests_get.assert_called_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/member", 
            headers={"x-api-key": DUMMY_API_KEY},
            params={'bioguideId': 'T000001'}, # Check params for /member endpoint
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

    # --- Tests for fetch_bills_list_data ---
    @patch('fetch_congress.save_json')
    def test_fetch_bills_list_data_success(self, mock_save_json):
        """Test fetching bills list successfully with various filters."""
        api_response_data = {"bills": ["bill1", "bill2"]}
        self.mock_response.json.return_value = api_response_data
        
        test_cases = [
            ({"congress": 117}, {"congress": 117}),
            ({"bill_type": "hr"}, {"billType": "hr"}),
            ({"introduced_date": "2023-01-01"}, {"introducedDate": "2023-01-01"}),
            ({"congress": 118, "bill_type": "s"}, {"congress": 118, "billType": "s"}),
        ]

        for filters, expected_params in test_cases:
            with self.subTest(filters=filters):
                self.mock_requests_get.reset_mock() # Reset for each subtest call
                mock_save_json.reset_mock()

                fetch_congress.fetch_bills_list_data(**filters)

                self.mock_requests_get.assert_called_once_with(
                    f"{fetch_congress.CONGRESS_API_BASE_URL}/bill",
                    headers={"x-api-key": DUMMY_API_KEY},
                    params=expected_params,
                    timeout=fetch_congress.REQUEST_TIMEOUT
                )
                self.mock_response.raise_for_status.assert_called_once()
                mock_save_json.assert_called_once_with(
                    api_response_data, "bills_list", **filters
                )

    @patch('fetch_congress.sys.exit')
    @patch('fetch_congress.save_json')
    def test_fetch_bills_list_data_no_filters(self, mock_save_json, mock_sys_exit):
        """Test fetch_bills_list_data exits if no filters are provided."""
        fetch_congress.fetch_bills_list_data()
        self.mock_logging_error.assert_called_with("At least one filter (--congress, --bill-type, --introduced-date) must be provided for the bills command.")
        mock_sys_exit.assert_called_once_with(1)
        mock_save_json.assert_not_called()

    @patch('fetch_congress.sys.exit')
    @patch('fetch_congress.save_json')
    def test_fetch_bills_list_data_api_error(self, mock_save_json, mock_sys_exit):
        """Test API error handling for fetch_bills_list_data."""
        self.mock_response.status_code = 500
        self.mock_response.raise_for_status.side_effect = fetch_congress.requests.exceptions.HTTPError("500 Server Error")
        self.mock_requests_get.return_value = self.mock_response

        fetch_congress.fetch_bills_list_data(congress=117) # Needs at least one filter
        self.mock_logging_error.assert_called()
        mock_sys_exit.assert_called_once_with(1)
        mock_save_json.assert_not_called()

    # --- Tests for fetch_committee_data ---
    @patch('fetch_congress.save_json')
    def test_fetch_committee_data_success(self, mock_save_json):
        """Test fetching committee data successfully with various filters."""
        api_response_data = {"committees": ["committee1", "committee2"]}
        self.mock_response.json.return_value = api_response_data

        test_cases = [
            ({"chamber": "house"}, {"chamber": "house"}),
            ({"congress": 117}, {"congress": 117}),
            ({"committee_code": "HSAG"}, {"committeeCode": "HSAG"}),
            ({"chamber": "senate", "congress": 118}, {"chamber": "senate", "congress": 118}),
        ]

        for filters, expected_params in test_cases:
            with self.subTest(filters=filters):
                self.mock_requests_get.reset_mock()
                mock_save_json.reset_mock()

                fetch_congress.fetch_committee_data(**filters)

                self.mock_requests_get.assert_called_once_with(
                    f"{fetch_congress.CONGRESS_API_BASE_URL}/committee",
                    headers={"x-api-key": DUMMY_API_KEY},
                    params=expected_params,
                    timeout=fetch_congress.REQUEST_TIMEOUT
                )
                self.mock_response.raise_for_status.assert_called_once()
                # Construct expected identifiers for save_json, ensuring key names match what fetch_committee_data uses
                expected_identifiers = filters.copy()
                if "committee_code" in expected_identifiers : # script uses committee_code as identifier key
                     pass # it's already correct
                
                mock_save_json.assert_called_once_with(
                    api_response_data, "committee_data", **expected_identifiers
                )

    @patch('fetch_congress.sys.exit')
    @patch('fetch_congress.save_json')
    def test_fetch_committee_data_no_filters(self, mock_save_json, mock_sys_exit):
        """Test fetch_committee_data exits if no filters are provided."""
        fetch_congress.fetch_committee_data()
        self.mock_logging_error.assert_called_with("At least one filter (--chamber, --congress, --committee-code) must be provided for the committee command.")
        mock_sys_exit.assert_called_once_with(1)
        mock_save_json.assert_not_called()

    @patch('fetch_congress.sys.exit')
    @patch('fetch_congress.save_json')
    def test_fetch_committee_data_api_error(self, mock_save_json, mock_sys_exit):
        """Test API error handling for fetch_committee_data."""
        self.mock_response.status_code = 500
        self.mock_response.raise_for_status.side_effect = fetch_congress.requests.exceptions.HTTPError("500 Server Error")
        self.mock_requests_get.return_value = self.mock_response

        fetch_congress.fetch_committee_data(chamber="house") # Needs at least one filter
        self.mock_logging_error.assert_called()
        mock_sys_exit.assert_called_once_with(1)
        mock_save_json.assert_not_called()

    # --- Tests for fetch_amendment_data ---
    @patch('fetch_congress.save_json')
    def test_fetch_amendment_data_success_with_filters(self, mock_save_json):
        """Test fetching amendment data successfully with filters."""
        api_response_data = {"amendments": ["amdt1", "amdt2"]}
        self.mock_response.json.return_value = api_response_data
        
        filters = {"congress": 117, "amendment_type": "samdt"}
        expected_params = {"congress": 117, "amendmentType": "samdt"}

        fetch_congress.fetch_amendment_data(**filters)

        self.mock_requests_get.assert_called_once_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/amendment",
            headers={"x-api-key": DUMMY_API_KEY},
            params=expected_params,
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        mock_save_json.assert_called_once_with(
            api_response_data, "amendment_data", **filters
        )

    @patch('fetch_congress.save_json')
    def test_fetch_amendment_data_success_no_filters(self, mock_save_json):
        """Test fetching amendment data successfully with no filters."""
        api_response_data = {"amendments": ["all_amendments"]}
        self.mock_response.json.return_value = api_response_data

        fetch_congress.fetch_amendment_data() # Call without any filters

        self.mock_requests_get.assert_called_once_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/amendment",
            headers={"x-api-key": DUMMY_API_KEY},
            params={}, # Expect empty params
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        self.mock_logging_info.assert_any_call("Fetching all amendments as no filters were specified. This might be a large request.")
        mock_save_json.assert_called_once_with(
            api_response_data, "amendment_data", all="all" # As per script logic
        )

    @patch('fetch_congress.sys.exit')
    @patch('fetch_congress.save_json')
    def test_fetch_amendment_data_api_error(self, mock_save_json, mock_sys_exit):
        """Test API error handling for fetch_amendment_data."""
        self.mock_response.status_code = 500
        self.mock_response.raise_for_status.side_effect = fetch_congress.requests.exceptions.HTTPError("500 Server Error")
        self.mock_requests_get.return_value = self.mock_response

        fetch_congress.fetch_amendment_data(congress=117) # Call with some filter
        
        self.mock_logging_error.assert_called()
        mock_sys_exit.assert_called_once_with(1)
        mock_save_json.assert_not_called()

    # --- Tests for fetch_committee_report_data ---
    @patch('fetch_congress.save_json')
    def test_fetch_committee_report_data_success_with_filter(self, mock_save_json):
        """Test fetching committee report data successfully with a congress filter."""
        api_response_data = {"committee_reports": ["report1", "report2"]}
        self.mock_response.json.return_value = api_response_data
        
        congress_filter = 117
        expected_params = {"congress": congress_filter}
        expected_identifiers = {"congress": congress_filter}

        fetch_congress.fetch_committee_report_data(congress=congress_filter)

        self.mock_requests_get.assert_called_once_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/committee-report",
            headers={"x-api-key": DUMMY_API_KEY},
            params=expected_params,
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        mock_save_json.assert_called_once_with(
            api_response_data, "committee_report_data", **expected_identifiers
        )

    @patch('fetch_congress.save_json')
    def test_fetch_committee_report_data_success_no_filter(self, mock_save_json):
        """Test fetching committee report data successfully with no filter."""
        api_response_data = {"committee_reports": ["all_reports"]}
        self.mock_response.json.return_value = api_response_data

        fetch_congress.fetch_committee_report_data() # Call without any filter

        self.mock_requests_get.assert_called_once_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/committee-report",
            headers={"x-api-key": DUMMY_API_KEY},
            params={}, # Expect empty params
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        self.mock_logging_info.assert_any_call("Fetching all committee reports as no filters were specified. This might be a large request.")
        mock_save_json.assert_called_once_with(
            api_response_data, "committee_report_data", all="all" # As per script logic
        )

    @patch('fetch_congress.sys.exit')
    @patch('fetch_congress.save_json')
    def test_fetch_committee_report_data_api_error(self, mock_save_json, mock_sys_exit):
        """Test API error handling for fetch_committee_report_data."""
        self.mock_response.status_code = 500
        self.mock_response.raise_for_status.side_effect = fetch_congress.requests.exceptions.HTTPError("500 Server Error")
        self.mock_requests_get.return_value = self.mock_response

        fetch_congress.fetch_committee_report_data(congress=117) # Call with some filter
        
        self.mock_logging_error.assert_called()
        mock_sys_exit.assert_called_once_with(1)
        mock_save_json.assert_not_called()

    # --- Tests for fetch_treaty_data ---
    @patch('fetch_congress.save_json')
    def test_fetch_treaty_data_success_with_filter(self, mock_save_json):
        """Test fetching treaty data successfully with a congress filter."""
        api_response_data = {"treaties": ["treaty1", "treaty2"]}
        self.mock_response.json.return_value = api_response_data
        
        congress_filter = 116
        expected_params = {"congress": congress_filter}
        expected_identifiers = {"congress": congress_filter}

        fetch_congress.fetch_treaty_data(congress=congress_filter)

        self.mock_requests_get.assert_called_once_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/treaty",
            headers={"x-api-key": DUMMY_API_KEY},
            params=expected_params,
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        mock_save_json.assert_called_once_with(
            api_response_data, "treaty_data", **expected_identifiers
        )

    @patch('fetch_congress.save_json')
    def test_fetch_treaty_data_success_no_filter(self, mock_save_json):
        """Test fetching treaty data successfully with no filter."""
        api_response_data = {"treaties": ["all_treaties"]}
        self.mock_response.json.return_value = api_response_data

        fetch_congress.fetch_treaty_data() # Call without any filter

        self.mock_requests_get.assert_called_once_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/treaty",
            headers={"x-api-key": DUMMY_API_KEY},
            params={}, # Expect empty params
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        self.mock_logging_info.assert_any_call("Fetching all treaties as no filters were specified. This might be a large request.")
        mock_save_json.assert_called_once_with(
            api_response_data, "treaty_data", all="all" # As per script logic
        )

    @patch('fetch_congress.sys.exit')
    @patch('fetch_congress.save_json')
    def test_fetch_treaty_data_api_error(self, mock_save_json, mock_sys_exit):
        """Test API error handling for fetch_treaty_data."""
        self.mock_response.status_code = 500
        self.mock_response.raise_for_status.side_effect = fetch_congress.requests.exceptions.HTTPError("500 Server Error")
        self.mock_requests_get.return_value = self.mock_response

        fetch_congress.fetch_treaty_data(congress=116) # Call with some filter
        
        self.mock_logging_error.assert_called()
        mock_sys_exit.assert_called_once_with(1)
        mock_save_json.assert_not_called()

    # --- Tests for fetch_nomination_data ---
    @patch('fetch_congress.save_json')
    def test_fetch_nomination_data_success(self, mock_save_json):
        """Test fetching nomination data successfully."""
        api_response_data = {"nominations": ["nomination1", "nomination2"]}
        self.mock_response.json.return_value = api_response_data
        
        congress_val = 117
        expected_endpoint = f"{fetch_congress.CONGRESS_API_BASE_URL}/nomination/{congress_val}"
        expected_identifiers = {"congress": congress_val}

        fetch_congress.fetch_nomination_data(congress=congress_val)

        self.mock_requests_get.assert_called_once_with(
            expected_endpoint,
            headers={"x-api-key": DUMMY_API_KEY},
            params=None, # No params for this endpoint structure
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        self.mock_logging_info.assert_any_call(f"Fetching all nominations for Congress {congress_val}.")
        mock_save_json.assert_called_once_with(
            api_response_data, "nomination_data", **expected_identifiers
        )

    @patch('fetch_congress.sys.exit')
    @patch('fetch_congress.save_json')
    def test_fetch_nomination_data_api_error(self, mock_save_json, mock_sys_exit):
        """Test API error handling for fetch_nomination_data."""
        self.mock_response.status_code = 500
        self.mock_response.raise_for_status.side_effect = fetch_congress.requests.exceptions.HTTPError("500 Server Error")
        self.mock_requests_get.return_value = self.mock_response

        congress_val = 117
        fetch_congress.fetch_nomination_data(congress=congress_val)
        
        self.mock_logging_error.assert_called()
        mock_sys_exit.assert_called_once_with(1)
        mock_save_json.assert_not_called()

    # --- Tests for fetch_congressional_record_data ---
    @patch('fetch_congress.save_json')
    def test_fetch_congressional_record_data_success_with_filters(self, mock_save_json):
        """Test fetching congressional record data successfully with filters."""
        api_response_data = {"congressional_records": ["record1", "record2"]}
        self.mock_response.json.return_value = api_response_data
        
        filters = {"congress": 117, "date": "2023-01-01"}
        expected_params = {"congress": 117, "date": "2023-01-01"}

        fetch_congress.fetch_congressional_record_data(**filters)

        self.mock_requests_get.assert_called_once_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/congressional-record",
            headers={"x-api-key": DUMMY_API_KEY},
            params=expected_params,
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        mock_save_json.assert_called_once_with(
            api_response_data, "congressional_record_data", **filters
        )

    @patch('fetch_congress.save_json')
    def test_fetch_congressional_record_data_success_no_filters(self, mock_save_json):
        """Test fetching congressional record data successfully with no filters."""
        api_response_data = {"congressional_records": ["all_records"]}
        self.mock_response.json.return_value = api_response_data

        fetch_congress.fetch_congressional_record_data() # Call without any filters

        self.mock_requests_get.assert_called_once_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/congressional-record",
            headers={"x-api-key": DUMMY_API_KEY},
            params={}, # Expect empty params
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        self.mock_logging_info.assert_any_call("Fetching all congressional records as no filters were specified. This might be a large request.")
        mock_save_json.assert_called_once_with(
            api_response_data, "congressional_record_data", all="all" # As per script logic
        )

    @patch('fetch_congress.sys.exit')
    @patch('fetch_congress.save_json')
    def test_fetch_congressional_record_data_api_error(self, mock_save_json, mock_sys_exit):
        """Test API error handling for fetch_congressional_record_data."""
        self.mock_response.status_code = 500
        self.mock_response.raise_for_status.side_effect = fetch_congress.requests.exceptions.HTTPError("500 Server Error")
        self.mock_requests_get.return_value = self.mock_response

        fetch_congress.fetch_congressional_record_data(congress=117) # Call with some filter
        
        self.mock_logging_error.assert_called()
        mock_sys_exit.assert_called_once_with(1)
        mock_save_json.assert_not_called()

    # --- Tests for fetch_senate_communication_data ---
    @patch('fetch_congress.save_json')
    def test_fetch_senate_communication_data_success_with_filters(self, mock_save_json):
        """Test fetching senate communication data successfully with filters."""
        api_response_data = {"senate_communications": ["comm1", "comm2"]}
        self.mock_response.json.return_value = api_response_data
        
        filters = {
            "congress": 117, 
            "communication_type": "ec", 
            "from_date": "2023-01-01", 
            "to_date": "2023-01-31"
        }
        expected_params = {
            "congress": 117, 
            "type": "ec", 
            "fromDateTime": "2023-01-01T00:00:00Z", 
            "toDateTime": "2023-01-31T23:59:59Z"
        }
        # Identifiers for save_json should match the function's input arg names
        expected_identifiers = filters.copy()


        fetch_congress.fetch_senate_communication_data(**filters)

        self.mock_requests_get.assert_called_once_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/senate-communication",
            headers={"x-api-key": DUMMY_API_KEY},
            params=expected_params,
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        mock_save_json.assert_called_once_with(
            api_response_data, "senate_communication_data", **expected_identifiers
        )

    @patch('fetch_congress.save_json')
    def test_fetch_senate_communication_data_success_no_filters(self, mock_save_json):
        """Test fetching senate communication data successfully with no filters."""
        api_response_data = {"senate_communications": ["all_comms"]}
        self.mock_response.json.return_value = api_response_data

        fetch_congress.fetch_senate_communication_data() # Call without any filters

        self.mock_requests_get.assert_called_once_with(
            f"{fetch_congress.CONGRESS_API_BASE_URL}/senate-communication",
            headers={"x-api-key": DUMMY_API_KEY},
            params={}, # Expect empty params
            timeout=fetch_congress.REQUEST_TIMEOUT
        )
        self.mock_response.raise_for_status.assert_called_once()
        self.mock_logging_info.assert_any_call(
            "Fetching all senate communications as no filters were specified. This might be a large request."
        )
        mock_save_json.assert_called_once_with(
            api_response_data, "senate_communication_data", all="all" # As per script logic
        )

    @patch('fetch_congress.sys.exit')
    @patch('fetch_congress.save_json')
    def test_fetch_senate_communication_data_api_error(self, mock_save_json, mock_sys_exit):
        """Test API error handling for fetch_senate_communication_data."""
        self.mock_response.status_code = 500
        self.mock_response.raise_for_status.side_effect = fetch_congress.requests.exceptions.HTTPError("500 Server Error")
        self.mock_requests_get.return_value = self.mock_response

        fetch_congress.fetch_senate_communication_data(congress=117) # Call with some filter
        
        self.mock_logging_error.assert_called()
        mock_sys_exit.assert_called_once_with(1)
        mock_save_json.assert_not_called()


if __name__ == "__main__":
    unittest.main()
