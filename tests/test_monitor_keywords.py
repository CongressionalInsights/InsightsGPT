import unittest
import json
import tempfile
import os
import shutil
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.monitor_keywords import monitor_keywords, load_keywords_from_args

class TestMonitorKeywords(unittest.TestCase):

    def setUp(self):
        # self.input_dir and self.output_dir are used by original tests
        # and can be used for temporary keyword files for new tests.
        self.input_dir_obj = tempfile.TemporaryDirectory()
        self.output_dir_obj = tempfile.TemporaryDirectory()
        self.input_dir = self.input_dir_obj.name
        self.output_dir = self.output_dir_obj.name
        # For tests that need the default config/keywords.txt, we might need to ensure it exists
        # or mock its behavior. For now, assume it exists as per previous steps.
        self.default_keywords_file_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'keywords.txt')


    def tearDown(self):
        self.input_dir_obj.cleanup()
        self.output_dir_obj.cleanup()

    def _create_dummy_json(self, filename, data):
        """Helper function to create a JSON file in the input directory."""
        filepath = os.path.join(self.input_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f)
        return filepath

    def _create_dummy_keywords_file(self, filename_suffix, keywords_list):
        """Helper function to create a keywords file in a temporary directory."""
        # Using self.input_dir (a temp dir) as a convenient place for temp keyword files
        filepath = os.path.join(self.input_dir, f"temp_keywords_{filename_suffix}.txt")
        with open(filepath, 'w') as f:
            for keyword in keywords_list:
                f.write(f"{keyword}\n")
        return filepath

    # --- Tests for monitor_keywords function (existing tests) ---
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

    # --- Tests for load_keywords_from_args function ---
    def test_load_from_specified_keywords_file(self):
        keywords_content = ["file_kw1", "file_kw2"]
        temp_kw_file = self._create_dummy_keywords_file("specified.txt", keywords_content)
        
        args = ['--input_folder', self.input_dir, '--output_folder', self.output_dir, '--keywords-file', temp_kw_file]
        input_f, output_f, loaded_kws = load_keywords_from_args(args)
        
        self.assertEqual(input_f, self.input_dir)
        self.assertEqual(output_f, self.output_dir)
        self.assertEqual(sorted(loaded_kws), sorted(keywords_content))

    def test_load_from_keywords_arg_precedence(self):
        file_keywords = ["file_kw1"]
        cmd_keywords = ["cmd_kw1", "cmd_kw2"]
        temp_kw_file = self._create_dummy_keywords_file("precedence.txt", file_keywords)

        args = ['--input_folder', 'in_prec', '--output_folder', 'out_prec', 
                '--keywords-file', temp_kw_file, 
                '--keywords'] + cmd_keywords
        input_f, output_f, loaded_kws = load_keywords_from_args(args)

        self.assertEqual(input_f, 'in_prec')
        self.assertEqual(output_f, 'out_prec')
        self.assertEqual(sorted(loaded_kws), sorted(cmd_keywords))

    @unittest.mock.patch('scripts.monitor_keywords.os.path.exists')
    def test_load_from_default_keywords_file(self, mock_exists):
        # This test assumes config/keywords.txt exists and is readable by load_keywords_from_args
        # We need to ensure it's actually read, so we mock os.path.exists for the default path
        # and provide content for the default file.
        
        # Path to the default keywords file as defined in monitor_keywords.py
        default_file_path_in_script = 'config/keywords.txt'
        
        mock_exists.return_value = True # Ensure the script thinks the default file exists

        default_keywords_content = ["default_kw1", "default_kw2", "default_kw3"]
        
        # We need to mock open specifically for the default file path
        # The @unittest.mock.patch decorator for open is tricky with multiple open calls.
        # A more robust way is to provide a side_effect for open.
        
        # For simplicity, we'll assume config/keywords.txt *actually* exists from previous steps
        # and contains known content. If not, this test becomes more complex to mock.
        # Let's assume 'config/keywords.txt' contains ['banana', 'apple', 'orange', 'regulation', 'policy']
        # as per the previous subtask.
        
        expected_default_keywords = []
        if os.path.exists(self.default_keywords_file_path): # Check if actual default file exists
             with open(self.default_keywords_file_path, 'r') as f_actual_default:
                 expected_default_keywords = [line.strip() for line in f_actual_default if line.strip()]

        if not expected_default_keywords:
            self.skipTest("Default config/keywords.txt not found or empty; cannot test default loading effectively without more complex mocking.")

        args = ['--input_folder', 'in_default', '--output_folder', 'out_default']
        # No --keywords or --keywords-file, so it should use default 'config/keywords.txt'
        input_f, output_f, loaded_kws = load_keywords_from_args(args)

        self.assertEqual(input_f, 'in_default')
        self.assertEqual(output_f, 'out_default')
        self.assertEqual(sorted(loaded_kws), sorted(expected_default_keywords))
        mock_exists.assert_any_call(default_file_path_in_script) # Check that it tried to find the default file


    def test_error_non_existent_specified_keywords_file(self):
        non_existent_file = os.path.join(self.input_dir, "non_existent_keywords.txt")
        args = ['--input_folder', 'in_err', '--output_folder', 'out_err', '--keywords-file', non_existent_file]
        
        with self.assertRaisesRegex(ValueError, f"Keywords file '{non_existent_file}' not found"):
            load_keywords_from_args(args)

    def test_error_empty_specified_keywords_file(self):
        empty_kw_file = self._create_dummy_keywords_file("empty.txt", [])
        args = ['--input_folder', 'in_empty', '--output_folder', 'out_empty', '--keywords-file', empty_kw_file]

        with self.assertRaisesRegex(ValueError, f"Keywords file '{empty_kw_file}' is empty"):
            load_keywords_from_args(args)
            
    @unittest.mock.patch('scripts.monitor_keywords.os.path.exists')
    def test_error_no_keywords_loaded_default_missing(self, mock_exists):
        # Simulate default config/keywords.txt not existing
        mock_exists.return_value = False
        
        # Path to the default keywords file as defined in monitor_keywords.py
        default_file_path_in_script = 'config/keywords.txt'

        args = ['--input_folder', 'in_no_kws', '--output_folder', 'out_no_kws']
        # No --keywords, no --keywords-file, and default 'config/keywords.txt' will be mocked as non-existent

        with self.assertRaisesRegex(ValueError, f"Keywords file '{default_file_path_in_script}' not found"):
            load_keywords_from_args(args)
        mock_exists.assert_called_with(default_file_path_in_script)


if __name__ == '__main__':
    unittest.main()
