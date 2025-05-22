import unittest
from unittest.mock import patch, MagicMock, call
import os
import json
import tempfile
import shutil
import sys

# Adjust path to allow direct import of scripts.monitor_keywords
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.monitor_keywords import monitor_keywords, main as monitor_keywords_main

class TestMonitorKeywords(unittest.TestCase):

    def setUp(self):
        # Create temporary directories for input and output
        self.input_dir = tempfile.mkdtemp(prefix="test_monitor_input_")
        self.output_dir = tempfile.mkdtemp(prefix="test_monitor_output_")

    def tearDown(self):
        # Remove the temporary directories and their contents
        shutil.rmtree(self.input_dir)
        shutil.rmtree(self.output_dir)

    def _create_temp_json_file(self, dir_path, filename, content_data, is_malformed=False):
        file_path = os.path.join(dir_path, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            if is_malformed:
                f.write(content_data) # Write the malformed string directly
            else:
                json.dump(content_data, f, indent=2)
        return file_path

    def test_keyword_present_creates_alert(self):
        doc_content = {
            "results": [
                {"id": 1, "text": "This document talks about delicious bananas.", "field": "value1"},
                {"id": 2, "text": "Another entry here.", "misc": "data"}
            ]
        }
        input_file = self._create_temp_json_file(self.input_dir, "doc_with_keyword.json", doc_content)
        
        monitor_keywords(self.input_dir, self.output_dir, keywords=['banana'])
        
        expected_alert_filename = f"flagged_{os.path.basename(input_file)}"
        expected_alert_path = os.path.join(self.output_dir, expected_alert_filename)
        
        self.assertTrue(os.path.exists(expected_alert_path), "Alert file was not created.")
        
        with open(expected_alert_path, 'r', encoding='utf-8') as f_alert:
            alert_data = json.load(f_alert)
        
        self.assertEqual(len(alert_data["results"]), 1)
        self.assertEqual(alert_data["results"][0]["id"], 1)
        self.assertIn("banana", alert_data["results"][0]["text"].lower())

    def test_keyword_absent_no_alert(self):
        doc_content = {
            "results": [
                {"id": 1, "text": "This document talks about apples and oranges.", "field": "value1"},
                {"id": 2, "text": "Another entry here.", "misc": "data"}
            ]
        }
        input_file = self._create_temp_json_file(self.input_dir, "doc_without_keyword.json", doc_content)
        
        monitor_keywords(self.input_dir, self.output_dir, keywords=['banana'])
        
        expected_alert_filename = f"flagged_{os.path.basename(input_file)}"
        expected_alert_path = os.path.join(self.output_dir, expected_alert_filename)
        
        self.assertFalse(os.path.exists(expected_alert_path), "Alert file should not have been created.")
        self.assertEqual(len(os.listdir(self.output_dir)), 0, "Output directory should be empty.")

    def test_multiple_keywords_and_files(self):
        content_a = {"results": [{"id": "A1", "text": "An apple a day."}]}
        content_b = {"results": [{"id": "B1", "text": "A bunch of bananas."}]}
        content_c = {"results": [{"id": "C1", "text": "Oranges are great."}]}

        file_a = self._create_temp_json_file(self.input_dir, "file_a.json", content_a)
        file_b = self._create_temp_json_file(self.input_dir, "file_b.json", content_b)
        file_c = self._create_temp_json_file(self.input_dir, "file_c.json", content_c)

        monitor_keywords(self.input_dir, self.output_dir, keywords=['apple', 'banana'])

        expected_alert_a = os.path.join(self.output_dir, f"flagged_{os.path.basename(file_a)}")
        expected_alert_b = os.path.join(self.output_dir, f"flagged_{os.path.basename(file_b)}")
        expected_alert_c = os.path.join(self.output_dir, f"flagged_{os.path.basename(file_c)}")

        self.assertTrue(os.path.exists(expected_alert_a))
        self.assertTrue(os.path.exists(expected_alert_b))
        self.assertFalse(os.path.exists(expected_alert_c))

        with open(expected_alert_a, 'r') as f:
            data_a = json.load(f)
            self.assertEqual(data_a["results"][0]["id"], "A1")
        with open(expected_alert_b, 'r') as f:
            data_b = json.load(f)
            self.assertEqual(data_b["results"][0]["id"], "B1")

    @patch('builtins.print') # scripts.monitor_keywords uses print for errors
    def test_malformed_json_file_graceful_handling(self, mock_print):
        valid_content = {"results": [{"id": "valid1", "text": "This has mykeyword."}]}
        malformed_str = '{"results": [{"id": "malformed1", "text": "Another mykeyword entry"} BAD JSON'

        valid_file = self._create_temp_json_file(self.input_dir, "valid_doc.json", valid_content)
        malformed_file = self._create_temp_json_file(self.input_dir, "malformed_doc.json", malformed_str, is_malformed=True)

        monitor_keywords(self.input_dir, self.output_dir, keywords=['mykeyword'])

        expected_alert_valid = os.path.join(self.output_dir, f"flagged_{os.path.basename(valid_file)}")
        expected_alert_malformed = os.path.join(self.output_dir, f"flagged_{os.path.basename(malformed_file)}")

        self.assertTrue(os.path.exists(expected_alert_valid))
        self.assertFalse(os.path.exists(expected_alert_malformed), "Alert file should not be created for malformed JSON.")
        
        # Check if print was called with an error message for the malformed file
        error_message_found = False
        for call_args in mock_print.call_args_list:
            if "Error decoding" in str(call_args) and os.path.basename(malformed_file) in str(call_args):
                error_message_found = True
                break
        self.assertTrue(error_message_found, "Error message for malformed JSON was not printed.")


    def test_empty_input_directory(self):
        monitor_keywords(self.input_dir, self.output_dir, keywords=['anykeyword'])
        self.assertEqual(len(os.listdir(self.output_dir)), 0, "Output directory should be empty when input is empty.")

    @patch('scripts.monitor_keywords.monitor_keywords') # Patch the core function
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_function_cli_args(self, mock_parse_args, mock_core_monitor_keywords):
        # Setup mock_parse_args to return a specific Namespace object
        mock_cli_args = MagicMock()
        mock_cli_args.input_folder = "cli_input_folder"
        mock_cli_args.output_folder = "cli_output_folder"
        mock_cli_args.keywords = ["cli_keyword1", "cli_keyword2"]
        mock_parse_args.return_value = mock_cli_args
        
        # Call the main function from the script
        # This requires monitor_keywords_main to be the `if __name__ == "__main__":` block's logic
        # or a refactored main function. Given the script structure, we call the imported main.
        monitor_keywords_main() 

        mock_parse_args.assert_called_once() 
        mock_core_monitor_keywords.assert_called_once_with(
            input_folder="cli_input_folder",
            output_folder="cli_output_folder",
            keywords=["cli_keyword1", "cli_keyword2"]
        )

if __name__ == '__main__':
    unittest.main(verbosity=2)
