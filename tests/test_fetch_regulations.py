import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import shutil
import sys

# Add scripts directory to sys.path to allow direct import
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

import fetch_regulations

TEST_DATA_REGULATIONS_DIR = os.path.join("data", "regulations_test")
ORIGINAL_DATA_DIR_REGULATIONS = None 
ORIGINAL_API_KEY_REGULATIONS = None

class TestFetchRegulations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global ORIGINAL_DATA_DIR_REGULATIONS, ORIGINAL_API_KEY_REGULATIONS
        
        ORIGINAL_DATA_DIR_REGULATIONS = fetch_regulations.DATA_DIR
        fetch_regulations.DATA_DIR = TEST_DATA_REGULATIONS_DIR

        ORIGINAL_API_KEY_REGULATIONS = fetch_regulations.REGULATIONS_API_KEY
        # The actual API key will be set in setUp using os.environ and then patching the module var

        if not os.path.exists("data"):
            os.makedirs("data")
        if os.path.exists(TEST_DATA_REGULATIONS_DIR):
            shutil.rmtree(TEST_DATA_REGULATIONS_DIR)
        os.makedirs(TEST_DATA_REGULATIONS_DIR, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        global ORIGINAL_DATA_DIR_REGULATIONS, ORIGINAL_API_KEY_REGULATIONS
        if os.path.exists(TEST_DATA_REGULATIONS_DIR):
            shutil.rmtree(TEST_DATA_REGULATIONS_DIR)
        if os.path.exists("data") and not os.listdir("data") and TEST_DATA_REGULATIONS_DIR.startswith("data/"):
            try:
                os.rmdir("data")
            except OSError:
                pass
        
        if ORIGINAL_DATA_DIR_REGULATIONS:
            fetch_regulations.DATA_DIR = ORIGINAL_DATA_DIR_REGULATIONS
        if ORIGINAL_API_KEY_REGULATIONS is not None: # Ensure it was captured
             fetch_regulations.REGULATIONS_API_KEY = ORIGINAL_API_KEY_REGULATIONS


    def setUp(self):
        self.dummy_api_key = "TEST_KEY_REGULATIONS"
        os.environ["REGULATIONS_API_KEY"] = self.dummy_api_key
        fetch_regulations.REGULATIONS_API_KEY = self.dummy_api_key

        self.load_dotenv_patch = patch('fetch_regulations.load_dotenv')
        self.mock_load_dotenv = self.load_dotenv_patch.start()

        self.requests_get_patch = patch('fetch_regulations.requests.get')
        self.mock_requests_get = self.requests_get_patch.start()

        self.logging_info_patch = patch('fetch_regulations.logging.info')
        self.mock_logging_info = self.logging_info_patch.start()

        self.logging_error_patch = patch('fetch_regulations.logging.error')
        self.mock_logging_error = self.logging_error_patch.start()

        self.logging_warning_patch = patch('fetch_regulations.logging.warning')
        self.mock_logging_warning = self.logging_warning_patch.start()

        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {"status": "success_reg_response"}
        self.mock_requests_get.return_value = self.mock_response

        if os.path.exists(TEST_DATA_REGULATIONS_DIR):
            shutil.rmtree(TEST_DATA_REGULATIONS_DIR)
        os.makedirs(TEST_DATA_REGULATIONS_DIR, exist_ok=True)

    def tearDown(self):
        self.load_dotenv_patch.stop()
        self.requests_get_patch.stop()
        self.logging_info_patch.stop()
        self.logging_error_patch.stop()
        self.logging_warning_patch.stop()

        if "REGULATIONS_API_KEY" in os.environ:
            del os.environ["REGULATIONS_API_KEY"]
        fetch_regulations.REGULATIONS_API_KEY = ORIGINAL_API_KEY_REGULATIONS # Restore original captured one


    # --- Tests for save_json ---
    @patch('fetch_regulations.os.makedirs', wraps=os.makedirs)
    @patch('builtins.open', new_callable=mock_open)
    def test_save_json_basic(self, mock_file_open, mock_os_makedirs_actual):
        sample_data = {"test_reg": "data_reg"}
        file_prefix = "reg_test_file"
        identifiers = {"regId": "789"}
        
        fetch_regulations.save_json(sample_data, file_prefix, **identifiers)
        
        expected_path = os.path.join(TEST_DATA_REGULATIONS_DIR, "reg_test_file_regId_789.json")
        mock_os_makedirs_actual.assert_any_call(TEST_DATA_REGULATIONS_DIR, exist_ok=True)
        mock_file_open.assert_called_once_with(expected_path, "w")
        mock_file_open().write.assert_called_once_with(json.dumps(sample_data, indent=4))

    @patch('fetch_regulations.os.makedirs', wraps=os.makedirs)
    @patch('builtins.open', new_callable=mock_open)
    def test_save_json_with_subdir(self, mock_file_open, mock_os_makedirs_actual):
        sample_data = {"test_reg_subdir": "data_reg_subdir"}
        file_prefix = "reg_test_file_subdir"
        sub_dir = "my_reg_subdir"
        identifiers = {"codeReg": "DEF"}

        fetch_regulations.save_json(sample_data, file_prefix, sub_dir=sub_dir, **identifiers)
        
        expected_subdir_path = os.path.join(TEST_DATA_REGULATIONS_DIR, sub_dir)
        expected_filepath = os.path.join(expected_subdir_path, "reg_test_file_subdir_codeReg_DEF.json")
        
        mock_os_makedirs_actual.assert_any_call(expected_subdir_path, exist_ok=True)
        mock_file_open.assert_called_once_with(expected_filepath, "w")

    # --- Tests for make_regulations_request ---
    def test_make_regulations_request_success(self):
        endpoint = "/test_reg_endpoint"
        params = {"paramReg": "valueReg"}
        expected_json_response = {"data_reg": "test_reg_data"}
        self.mock_response.json.return_value = expected_json_response

        response = fetch_regulations.make_regulations_request(endpoint, params)

        expected_url = f"{fetch_regulations.API_BASE}{endpoint}"
        expected_headers = {
            "X-Api-Key": self.dummy_api_key,
            "Accept": "application/vnd.api+json"
        }
        self.mock_requests_get.assert_called_once_with(
            expected_url, params=params, headers=expected_headers, timeout=fetch_regulations.REQUEST_TIMEOUT
        )
        # self.mock_response.raise_for_status.assert_called_once() # Not used in this func
        self.assertEqual(response, expected_json_response)

    @patch('fetch_regulations.sys.exit')
    def test_make_regulations_request_no_api_key_module_level(self, mock_sys_exit):
        # This tests the initial check at module load by temporarily unpatching
        # For this to work, we'd need to reload the module or test differently.
        # The check in make_regulations_request itself is easier to test:
        fetch_regulations.REGULATIONS_API_KEY = None
        fetch_regulations.make_regulations_request("/test_no_key")
        self.mock_logging_error.assert_any_call("REGULATIONS_API_KEY is not available. Cannot make API request.")
        mock_sys_exit.assert_called_with(1)

    def test_make_regulations_request_http_error_non_200(self):
        self.mock_response.status_code = 404
        self.mock_response.text = "Not Found Error Text"
        
        response = fetch_regulations.make_regulations_request("/notfound_reg")
        self.assertIsNone(response)
        self.mock_logging_error.assert_any_call("API request failed with status 404: Not Found Error Text")

    def test_make_regulations_request_request_exception(self):
        self.mock_requests_get.side_effect = requests.exceptions.Timeout("Timeout Error")
        response = fetch_regulations.make_regulations_request("/timeout_test")
        self.assertIsNone(response)
        self.mock_logging_error.assert_any_call(unittest.mock.ANY)


    # --- Tests for fetch_documents_data ---
    @patch('fetch_regulations.save_json')
    def test_fetch_documents_data_success(self, mock_save_json):
        mock_args = MagicMock(
            search_term="climate", docket_id="EPA-HQ-XYZ", title_filter="guidance",
            page_size=10, page_number=2
        )
        fetch_regulations.fetch_documents_data(mock_args)
        expected_params = {
            "filter[searchTerm]": "climate",
            "filter[docketId]": "EPA-HQ-XYZ",
            "filter[title]": "guidance",
            "page[size]": 10,
            "page[number]": 2
        }
        self.mock_requests_get.assert_called_with(
            unittest.mock.ANY, params=expected_params, headers=unittest.mock.ANY, timeout=unittest.mock.ANY
        )
        expected_identifiers = {
            "searchTerm": "climate", "docketId": "EPA-HQ-XYZ", "title": "guidance"
        }
        mock_save_json.assert_called_once_with(
            self.mock_response.json.return_value, "documents_list", sub_dir="documents", **expected_identifiers
        )

    @patch('fetch_regulations.make_regulations_request', return_value=None)
    def test_fetch_documents_data_failure(self, mock_make_request):
        mock_args = MagicMock(search_term="fail_term", docket_id=None, title_filter=None, page_size=25, page_number=1)
        fetch_regulations.fetch_documents_data(mock_args)
        self.mock_logging_error.assert_called_with(f"Failed to fetch documents for filters: {{'searchTerm': 'fail_term'}}")


    # --- Tests for fetch_single_document_data ---
    @patch('fetch_regulations.save_json')
    def test_fetch_single_document_data_success(self, mock_save_json):
        doc_id = "MY-DOC-ID-001"
        mock_args = MagicMock(document_id=doc_id, include_attachments=False)
        fetch_regulations.fetch_single_document_data(mock_args)
        self.mock_requests_get.assert_called_with(
            f"{fetch_regulations.API_BASE}/documents/{doc_id}", params=None, headers=unittest.mock.ANY, timeout=unittest.mock.ANY
        )
        mock_save_json.assert_called_once_with(
            self.mock_response.json.return_value, "document_details", 
            sub_dir=f"documents/{doc_id}", documentId=doc_id
        )

    @patch('fetch_regulations.save_json')
    def test_fetch_single_document_data_with_attachments(self, mock_save_json):
        doc_id = "MY-DOC-ID-002"
        mock_args = MagicMock(document_id=doc_id, include_attachments=True)
        fetch_regulations.fetch_single_document_data(mock_args)
        expected_params = {"include": "attachments"}
        self.mock_requests_get.assert_called_with(
            f"{fetch_regulations.API_BASE}/documents/{doc_id}", params=expected_params, headers=unittest.mock.ANY, timeout=unittest.mock.ANY
        )
        expected_identifiers = {"documentId": doc_id, "attachments": "true"}
        mock_save_json.assert_called_once_with(
            self.mock_response.json.return_value, "document_details", 
            sub_dir=f"documents/{doc_id}", **expected_identifiers
        )

    @patch('fetch_regulations.make_regulations_request', return_value=None)
    def test_fetch_single_document_data_failure(self, mock_make_request):
        doc_id = "FAIL-DOC-ID"
        mock_args = MagicMock(document_id=doc_id, include_attachments=False)
        fetch_regulations.fetch_single_document_data(mock_args)
        self.mock_logging_error.assert_called_with(f"Failed to fetch document: {doc_id}")


    # --- Tests for fetch_dockets_data ---
    @patch('fetch_regulations.save_json')
    def test_fetch_dockets_data_success(self, mock_save_json):
        mock_args = MagicMock(search_term="energy", page_size=50, page_number=3)
        fetch_regulations.fetch_dockets_data(mock_args)
        expected_params = {"filter[searchTerm]": "energy", "page[size]": 50, "page[number]": 3}
        self.mock_requests_get.assert_called_with(
            unittest.mock.ANY, params=expected_params, headers=unittest.mock.ANY, timeout=unittest.mock.ANY
        )
        mock_save_json.assert_called_once_with(
            self.mock_response.json.return_value, "dockets_list", sub_dir="dockets", searchTerm="energy"
        )

    @patch('fetch_regulations.make_regulations_request', return_value=None)
    def test_fetch_dockets_data_failure(self, mock_make_request):
        mock_args = MagicMock(search_term="fail_docket_term", page_size=25, page_number=1)
        fetch_regulations.fetch_dockets_data(mock_args)
        self.mock_logging_error.assert_called_with(f"Failed to fetch dockets for filters: {{'searchTerm': 'fail_docket_term'}}")


    # --- Tests for fetch_single_docket_data ---
    @patch('fetch_regulations.save_json')
    def test_fetch_single_docket_data_success(self, mock_save_json):
        docket_id = "MY-DKT-ID-001"
        mock_args = MagicMock(docket_id=docket_id)
        fetch_regulations.fetch_single_docket_data(mock_args)
        self.mock_requests_get.assert_called_with(
            f"{fetch_regulations.API_BASE}/dockets/{docket_id}", params=None, headers=unittest.mock.ANY, timeout=unittest.mock.ANY
        )
        mock_save_json.assert_called_once_with(
            self.mock_response.json.return_value, "docket_details", 
            sub_dir=f"dockets/{docket_id}", docket_id=docket_id
        )
        
    @patch('fetch_regulations.make_regulations_request', return_value=None)
    def test_fetch_single_docket_data_failure(self, mock_make_request):
        docket_id = "FAIL-DKT-ID"
        mock_args = MagicMock(docket_id=docket_id)
        fetch_regulations.fetch_single_docket_data(mock_args)
        self.mock_logging_error.assert_called_with(f"Failed to fetch docket: {docket_id}")


    # --- Tests for fetch_comments_data ---
    @patch('fetch_regulations.save_json')
    def test_fetch_comments_data_success(self, mock_save_json):
        mock_args = MagicMock(search_term="public input", page_size=20, page_after="XYZ123")
        fetch_regulations.fetch_comments_data(mock_args)
        expected_params = {"filter[searchTerm]": "public input", "page[size]": 20, "page[after]": "XYZ123"}
        self.mock_requests_get.assert_called_with(
            unittest.mock.ANY, params=expected_params, headers=unittest.mock.ANY, timeout=unittest.mock.ANY
        )
        expected_identifiers = {"searchTerm": "public_input", "pageAfter": "XYZ123"}
        mock_save_json.assert_called_once_with(
            self.mock_response.json.return_value, "comments_list", sub_dir="comments", **expected_identifiers
        )

    @patch('fetch_regulations.make_regulations_request', return_value=None)
    def test_fetch_comments_data_failure(self, mock_make_request):
        mock_args = MagicMock(search_term="fail_comment_term", page_size=10, page_after=None)
        fetch_regulations.fetch_comments_data(mock_args)
        self.mock_logging_error.assert_called_with(f"Failed to fetch comments for filters: {{'searchTerm': 'fail_comment_term'}}")


    # --- Tests for fetch_single_comment_data ---
    @patch('fetch_regulations.save_json')
    def test_fetch_single_comment_data_success(self, mock_save_json):
        comment_id = "MY-CMT-ID-001"
        mock_args = MagicMock(comment_id=comment_id, include_attachments=False)
        fetch_regulations.fetch_single_comment_data(mock_args)
        self.mock_requests_get.assert_called_with(
            f"{fetch_regulations.API_BASE}/comments/{comment_id}", params=None, headers=unittest.mock.ANY, timeout=unittest.mock.ANY
        )
        mock_save_json.assert_called_once_with(
            self.mock_response.json.return_value, "comment_details", 
            sub_dir=f"comments/{comment_id}", commentId=comment_id
        )

    @patch('fetch_regulations.save_json')
    def test_fetch_single_comment_data_with_attachments(self, mock_save_json):
        comment_id = "MY-CMT-ID-002"
        mock_args = MagicMock(comment_id=comment_id, include_attachments=True)
        fetch_regulations.fetch_single_comment_data(mock_args)
        expected_params = {"include": "attachments"}
        self.mock_requests_get.assert_called_with(
            f"{fetch_regulations.API_BASE}/comments/{comment_id}", params=expected_params, headers=unittest.mock.ANY, timeout=unittest.mock.ANY
        )
        expected_identifiers = {"commentId": comment_id, "attachments": "true"}
        mock_save_json.assert_called_once_with(
            self.mock_response.json.return_value, "comment_details", 
            sub_dir=f"comments/{comment_id}", **expected_identifiers
        )
        
    @patch('fetch_regulations.make_regulations_request', return_value=None)
    def test_fetch_single_comment_data_failure(self, mock_make_request):
        comment_id = "FAIL-CMT-ID"
        mock_args = MagicMock(comment_id=comment_id, include_attachments=False)
        fetch_regulations.fetch_single_comment_data(mock_args)
        self.mock_logging_error.assert_called_with(f"Failed to fetch comment: {comment_id}")


    # --- Tests for main function routing ---
    @patch('fetch_regulations.fetch_documents_data')
    def test_main_documents_command(self, mock_fetch_func):
        sys.argv = ["fetch_regulations.py", "documents", "--search-term", "test"]
        fetch_regulations.main()
        mock_fetch_func.assert_called_once()

    @patch('fetch_regulations.fetch_single_document_data')
    def test_main_document_command(self, mock_fetch_func):
        sys.argv = ["fetch_regulations.py", "document", "--document-id", "DOC-001"]
        fetch_regulations.main()
        mock_fetch_func.assert_called_once()
        self.assertEqual(mock_fetch_func.call_args[0][0].document_id, "DOC-001")

    def test_main_document_command_missing_arg(self):
        sys.argv = ["fetch_regulations.py", "document"]
        with self.assertRaises(SystemExit):
            fetch_regulations.main()

    @patch('fetch_regulations.fetch_dockets_data')
    def test_main_dockets_command(self, mock_fetch_func):
        sys.argv = ["fetch_regulations.py", "dockets", "--search-term", "docket_test"]
        fetch_regulations.main()
        mock_fetch_func.assert_called_once()

    @patch('fetch_regulations.fetch_single_docket_data')
    def test_main_docket_command(self, mock_fetch_func): # Singular docket
        sys.argv = ["fetch_regulations.py", "docket", "--docket-id", "DKT-001"]
        fetch_regulations.main()
        mock_fetch_func.assert_called_once()
        self.assertEqual(mock_fetch_func.call_args[0][0].docket_id, "DKT-001")

    def test_main_docket_command_missing_arg(self): # Singular docket
        sys.argv = ["fetch_regulations.py", "docket"]
        with self.assertRaises(SystemExit):
            fetch_regulations.main()

    @patch('fetch_regulations.fetch_comments_data')
    def test_main_comments_command(self, mock_fetch_func):
        sys.argv = ["fetch_regulations.py", "comments", "--search-term", "comment_test"]
        fetch_regulations.main()
        mock_fetch_func.assert_called_once()

    @patch('fetch_regulations.fetch_single_comment_data')
    def test_main_comment_command(self, mock_fetch_func): # Singular comment
        sys.argv = ["fetch_regulations.py", "comment", "--comment-id", "CMT-001"]
        fetch_regulations.main()
        mock_fetch_func.assert_called_once()
        self.assertEqual(mock_fetch_func.call_args[0][0].comment_id, "CMT-001")

    def test_main_comment_command_missing_arg(self): # Singular comment
        sys.argv = ["fetch_regulations.py", "comment"]
        with self.assertRaises(SystemExit):
            fetch_regulations.main()

if __name__ == "__main__":
    unittest.main()
