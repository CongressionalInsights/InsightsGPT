import unittest
import json
import tempfile
import os
import shutil
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.monitor_keywords import monitor_keywords

class TestMonitorKeywords(unittest.TestCase):

    def setUp(self):
        self.input_dir_obj = tempfile.TemporaryDirectory()
        self.output_dir_obj = tempfile.TemporaryDirectory()
        self.input_dir = self.input_dir_obj.name
        self.output_dir = self.output_dir_obj.name

    def tearDown(self):
        self.input_dir_obj.cleanup()
        self.output_dir_obj.cleanup()

    def _create_dummy_json(self, filename, data):
        """Helper function to create a JSON file in the input directory."""
        filepath = os.path.join(self.input_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f)
        return filepath

    def test_keyword_present(self):
        doc_content = {"results": [{"text": "This document contains the keyword banana."}]}
        self._create_dummy_json("doc1.json", doc_content)
        keywords = ["banana"]
        monitor_keywords(self.input_dir, self.output_dir, keywords)

        flagged_file_path = os.path.join(self.output_dir, "flagged_doc1.json")
        self.assertTrue(os.path.exists(flagged_file_path))
        with open(flagged_file_path, 'r') as f:
            content = json.load(f)
        self.assertEqual(content, doc_content)

    def test_keyword_absent(self):
        doc_content = {"results": [{"text": "This document is about apples."}]}
        self._create_dummy_json("doc2.json", doc_content)
        keywords = ["banana"]
        monitor_keywords(self.input_dir, self.output_dir, keywords)

        flagged_file_path = os.path.join(self.output_dir, "flagged_doc2.json")
        self.assertFalse(os.path.exists(flagged_file_path))

    def test_multiple_keywords_one_present(self):
        doc_content = {"results": [{"text": "Contains orange."}]}
        self._create_dummy_json("doc3.json", doc_content)
        keywords = ["banana", "orange", "apple"]
        monitor_keywords(self.input_dir, self.output_dir, keywords)

        flagged_file_path = os.path.join(self.output_dir, "flagged_doc3.json")
        self.assertTrue(os.path.exists(flagged_file_path))
        with open(flagged_file_path, 'r') as f:
            content = json.load(f)
        self.assertEqual(content, doc_content)

    def test_multiple_keywords_multiple_present(self):
        doc_content = {"results": [{"text": "Contains banana and orange."}]}
        self._create_dummy_json("doc4.json", doc_content)
        keywords = ["banana", "orange"]
        monitor_keywords(self.input_dir, self.output_dir, keywords)

        flagged_file_path = os.path.join(self.output_dir, "flagged_doc4.json")
        self.assertTrue(os.path.exists(flagged_file_path))
        with open(flagged_file_path, 'r') as f:
            content = json.load(f)
        self.assertEqual(content, doc_content)

    def test_multiple_files_mixed(self):
        doc_A_content = {"results": [{"text": "This document contains the keyword banana."}]}
        self._create_dummy_json("doc_A.json", doc_A_content)
        doc_B_content = {"results": [{"text": "This document is about apples."}]}
        self._create_dummy_json("doc_B.json", doc_B_content)

        keywords = ["banana"]
        monitor_keywords(self.input_dir, self.output_dir, keywords)

        flagged_doc_A_path = os.path.join(self.output_dir, "flagged_doc_A.json")
        self.assertTrue(os.path.exists(flagged_doc_A_path))
        with open(flagged_doc_A_path, 'r') as f:
            content = json.load(f)
        self.assertEqual(content, doc_A_content)

        flagged_doc_B_path = os.path.join(self.output_dir, "flagged_doc_B.json")
        self.assertFalse(os.path.exists(flagged_doc_B_path))

    def test_case_insensitivity(self):
        doc_content = {"results": [{"text": "Contains BANANA."}]}
        self._create_dummy_json("doc5.json", doc_content)
        keywords = ["banana"]
        monitor_keywords(self.input_dir, self.output_dir, keywords)

        flagged_file_path = os.path.join(self.output_dir, "flagged_doc5.json")
        self.assertTrue(os.path.exists(flagged_file_path))
        with open(flagged_file_path, 'r') as f:
            content = json.load(f)
        self.assertEqual(content, doc_content)

    def test_non_json_file(self):
        non_json_path = os.path.join(self.input_dir, "not_a_json.txt")
        with open(non_json_path, 'w') as f:
            f.write("This is not JSON content.")
        
        keywords = ["banana"]
        monitor_keywords(self.input_dir, self.output_dir, keywords)

        flagged_file_path = os.path.join(self.output_dir, "flagged_not_a_json.txt")
        self.assertFalse(os.path.exists(flagged_file_path))

    @unittest.mock.patch('builtins.print')
    def test_malformed_json_file(self, mock_print):
        malformed_json_path = os.path.join(self.input_dir, "malformed.json")
        with open(malformed_json_path, 'w') as f:
            f.write('{"results": [ {"text": "apple"}, ]') # Malformed JSON

        keywords = ["apple"]
        monitor_keywords(self.input_dir, self.output_dir, keywords)

        flagged_file_path = os.path.join(self.output_dir, "flagged_malformed.json")
        self.assertFalse(os.path.exists(flagged_file_path))
        
        # Check if an error message was printed
        error_found = False
        for call_args in mock_print.call_args_list:
            if "Error decoding JSON" in call_args[0][0] and "malformed.json" in call_args[0][0]:
                error_found = True
                break
        self.assertTrue(error_found, "Expected JSONDecodeError message was not printed.")

    def test_empty_input_folder(self):
        keywords = ["banana"]
        # Ensure the input directory is empty by re-creating it or cleaning it.
        # For this test, TemporaryDirectory handles cleanup, so we just ensure it's empty.
        # If there was a risk of pre-existing files, we'd os.listdir and remove.
        monitor_keywords(self.input_dir, self.output_dir, keywords)
        self.assertEqual(len(os.listdir(self.output_dir)), 0, "Output directory should be empty.")

    def test_empty_keywords_list(self):
        doc_content = {"results": [{"text": "This document contains some text."}]}
        self._create_dummy_json("doc6.json", doc_content)
        keywords = []
        monitor_keywords(self.input_dir, self.output_dir, keywords)

        flagged_file_path = os.path.join(self.output_dir, "flagged_doc6.json")
        self.assertFalse(os.path.exists(flagged_file_path), "File should not be flagged with empty keyword list.")


if __name__ == '__main__':
    unittest.main()
