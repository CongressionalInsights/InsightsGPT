import unittest
from unittest.mock import patch, MagicMock, call
import os
import json
import tempfile
import sys

# Adjust path to allow direct import of scripts.validate_data
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.validate_data import validate_file, validate_folder, main as validate_data_main

class TestValidateData(unittest.TestCase):

    def _create_temp_json_file(self, dir_path, filename_prefix, content_data, is_malformed=False):
        # For malformed JSON, content_data should be a string.
        # Otherwise, content_data should be a Python dict/list to be dumped as JSON.
        
        # Generate a unique filename using tempfile.mktemp to avoid collisions if prefix is same
        # but ensure it's within the provided dir_path.
        base_path = os.path.join(dir_path, filename_prefix)
        temp_file_path = tempfile.mktemp(prefix=filename_prefix, suffix='.json', dir=dir_path)

        with open(temp_file_path, 'w', encoding='utf-8') as f:
            if is_malformed:
                f.write(content_data) # Write the malformed string directly
            else:
                json.dump(content_data, f)
        
        self.files_to_cleanup.append(temp_file_path) # Register for cleanup
        return temp_file_path

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_validate_") 
        self.files_to_cleanup = []
        self.default_required_fields = ["title", "publication_date", "agency"]

    def tearDown(self):
        for f_path in self.files_to_cleanup:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except OSError as e:
                    print(f"Error removing file {f_path}: {e}", file=sys.stderr)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError as e:
                 print(f"Error removing directory {self.test_dir}: {e}", file=sys.stderr)


    def test_validate_file_valid_json(self):
        valid_content = {
            "results": [
                {"title": "Valid Title 1", "publication_date": "2023-01-01", "agency": "Agency A"},
                {"title": "Valid Title 2", "publication_date": "2023-01-02", "agency": "Agency B"}
            ]
        }
        temp_file_path = self._create_temp_json_file(self.test_dir, "valid_", valid_content)
        
        result = validate_file(temp_file_path, self.default_required_fields)
        
        self.assertNotIn("error", result, "Result should not contain a top-level 'error' key for valid JSON structure.")
        self.assertEqual(len(result["errors"]), 0, f"Expected 0 errors, got {len(result['errors'])}: {result['errors']}")
        self.assertEqual(result["total_entries"], 2)

    def test_validate_file_malformed_json(self):
        malformed_content_str = '{"results": [{"title": "Malformed", "publication_date": "2023-01-01", "agency": "Agency C"},]' # Trailing comma
        temp_file_path = self._create_temp_json_file(self.test_dir, "malformed_", malformed_content_str, is_malformed=True)
        
        result = validate_file(temp_file_path, self.default_required_fields)
        
        self.assertIn("error", result)
        self.assertTrue("JSON decode error" in result["error"])

    def test_validate_file_missing_required_fields(self):
        content_missing_fields = {
            "results": [
                {"title": "Title OK", "publication_date": "2023-01-01", "agency": "Agency D"}, # Valid
                {"publication_date": "2023-01-02", "agency": "Agency E"}, # Missing title
                {"title": "Title OK Too", "agency": "Agency F"} # Missing publication_date
            ]
        }
        temp_file_path = self._create_temp_json_file(self.test_dir, "missing_", content_missing_fields)
        
        result = validate_file(temp_file_path, self.default_required_fields)
        
        self.assertNotIn("error", result) # Should not be a JSON decode error
        self.assertEqual(len(result["errors"]), 2)
        self.assertEqual(result["total_entries"], 3)
        
        # Check first error (entry at index 1 missing 'title')
        error1 = result["errors"][0]
        self.assertEqual(error1["index"], 1)
        self.assertIn("title", error1["missing_fields"])
        
        # Check second error (entry at index 2 missing 'publication_date')
        error2 = result["errors"][1]
        self.assertEqual(error2["index"], 2)
        self.assertIn("publication_date", error2["missing_fields"])

    def test_validate_file_no_results_key(self):
        content_no_results = {"data": [{"title": "No results key here"}]}
        temp_file_path = self._create_temp_json_file(self.test_dir, "no_results_", content_no_results)
        result = validate_file(temp_file_path, self.default_required_fields)
        self.assertEqual(result["total_entries"], 0)
        self.assertEqual(len(result["errors"]), 0) # No entries to have errors

    def test_validate_file_results_not_a_list(self):
        content_results_not_list = {"results": {"title": "Results is a dict, not a list"}}
        temp_file_path = self._create_temp_json_file(self.test_dir, "results_not_list_", content_results_not_list)
        # The current implementation of validate_file in scripts/validate_data.py
        # uses data.get("results", []), which would return an empty list if "results" is not a list
        # or if it's a dict. This means it would report 0 entries and 0 errors.
        # This test verifies that behavior. If stricter checking is desired, the script would need modification.
        result = validate_file(temp_file_path, self.default_required_fields)
        self.assertEqual(result["total_entries"], 0)
        self.assertEqual(len(result["errors"]), 0)

    def test_validate_folder_multiple_files(self):
        # File 1: Valid
        valid_content = {"results": [{"title": "Valid", "publication_date": "2023-01-01", "agency": "A"}]}
        self._create_temp_json_file(self.test_dir, "file1_valid_", valid_content)
        
        # File 2: Malformed
        malformed_content_str = '{"results": BAD JSON'
        self._create_temp_json_file(self.test_dir, "file2_malformed_", malformed_content_str, is_malformed=True)
        
        # File 3: Missing fields
        missing_fields_content = {"results": [{"title": "Missing Agency"}]} # Missing agency and pub_date
        self._create_temp_json_file(self.test_dir, "file3_missing_", missing_fields_content)

        # Non-JSON file, should be ignored
        with open(os.path.join(self.test_dir, "ignore_me.txt"), "w") as f_txt:
            f_txt.write("This is not JSON")
        self.files_to_cleanup.append(os.path.join(self.test_dir, "ignore_me.txt"))

        output_summary_file_path = os.path.join(self.test_dir, "summary_output.json")
        self.files_to_cleanup.append(output_summary_file_path) # Ensure summary is cleaned up

        validate_folder(self.test_dir, self.default_required_fields, output_summary_file_path)
        
        self.assertTrue(os.path.exists(output_summary_file_path))
        with open(output_summary_file_path, "r") as f_summary:
            summary_data = json.load(f_summary)
            
        self.assertEqual(len(summary_data), 3) # Only JSON files processed

        found_valid = False
        found_malformed = False
        found_missing_fields = False

        for res in summary_data:
            if "file1_valid_" in res["file"]:
                found_valid = True
                self.assertNotIn("error", res)
                self.assertEqual(len(res["errors"]), 0)
            elif "file2_malformed_" in res["file"]:
                found_malformed = True
                self.assertIn("error", res)
                self.assertTrue("JSON decode error" in res["error"])
            elif "file3_missing_" in res["file"]:
                found_missing_fields = True
                self.assertNotIn("error", res)
                self.assertEqual(len(res["errors"]), 1)
                self.assertIn("publication_date", res["errors"][0]["missing_fields"])
                self.assertIn("agency", res["errors"][0]["missing_fields"])

        self.assertTrue(found_valid, "Valid file result not found in summary.")
        self.assertTrue(found_malformed, "Malformed file result not found in summary.")
        self.assertTrue(found_missing_fields, "Missing fields file result not found in summary.")

    @patch('scripts.validate_data.validate_folder')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_function_calls_validate_folder(self, mock_parse_args, mock_validate_folder):
        # Setup mock_parse_args to return a specific Namespace object
        mock_args = MagicMock()
        mock_args.input_folder = "test_input_folder"
        mock_args.output_file = "test_output_file.json"
        mock_args.required_fields = ["field1", "field2"]
        mock_parse_args.return_value = mock_args
        
        # Call the main function which is effectively `if __name__ == "__main__":` block
        # To do this, we can try to run validate_data_main if it's refactored
        # or simulate the `if __name__ == "__main__"` block by calling the core logic.
        # The script structure `if __name__ == "__main__":` means `validate_data_main` is not directly defined.
        # We will call validate_data_main by importing it.
        
        validate_data_main() # This will run the arg parsing and call validate_folder

        mock_parse_args.assert_called_once() # Check that arg parsing happened
        mock_validate_folder.assert_called_once_with(
            input_folder="test_input_folder",
            required_fields=["field1", "field2"],
            output_file="test_output_file.json"
        )

if __name__ == '__main__':
    unittest.main(verbosity=2)
