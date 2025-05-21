import unittest
import json
import tempfile
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.validate_data import validate_file, validate_folder

class TestValidateData(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        # Clean up the temporary directory
        self.test_dir.cleanup()

    def test_validate_file_valid_json(self):
        # Create a temporary valid JSON file
        valid_data = {"results": [{"title": "Test Title", "publication_date": "2023-01-01", "agency": "Test Agency"}]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", dir=self.test_dir.name, delete=False) as tmp_file:
            json.dump(valid_data, tmp_file)
            tmp_file_path = tmp_file.name

        required_fields = ["title", "publication_date", "agency"]
        result = validate_file(tmp_file_path, required_fields)

        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["total_entries"], 1)
        self.assertEqual(result["filename"], os.path.basename(tmp_file_path))

    def test_validate_file_invalid_json_syntax(self):
        # Create a temporary file with invalid JSON content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", dir=self.test_dir.name, delete=False) as tmp_file:
            tmp_file.write('{"results": [') # Invalid JSON
            tmp_file_path = tmp_file.name

        required_fields = ["title", "publication_date", "agency"]
        result = validate_file(tmp_file_path, required_fields)

        self.assertTrue(result["error"].startswith("JSON decode error:"))
        self.assertEqual(result["filename"], os.path.basename(tmp_file_path))

    def test_validate_file_missing_fields(self):
        # Create a temporary valid JSON file with missing fields
        data_missing_fields = {"results": [{"title": "Test Title Only"}]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", dir=self.test_dir.name, delete=False) as tmp_file:
            json.dump(data_missing_fields, tmp_file)
            tmp_file_path = tmp_file.name

        required_fields = ["title", "publication_date", "agency"]
        result = validate_file(tmp_file_path, required_fields)

        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["total_entries"], 1)
        self.assertEqual(result["errors"][0]["entry_index"], 0)
        self.assertEqual(result["errors"][0]["entry_content"]["title"], "Test Title Only")
        self.assertIn("publication_date", result["errors"][0]["missing_fields"])
        self.assertIn("agency", result["errors"][0]["missing_fields"])
        self.assertEqual(result["filename"], os.path.basename(tmp_file_path))

    def test_validate_folder_valid_file(self):
        # Create a temporary output file path
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_out:
            output_file_path = tmp_out.name

        # Case 1: Valid JSON file
        valid_data = {"results": [{"title": "Test Title", "publication_date": "2023-01-01", "agency": "Test Agency"}]}
        valid_file_path = os.path.join(self.test_dir.name, "valid.json")
        with open(valid_file_path, "w") as f:
            json.dump(valid_data, f)

        required_fields = ["title", "publication_date", "agency"]
        validate_folder(self.test_dir.name, required_fields, output_file_path)

        self.assertTrue(os.path.exists(output_file_path))
        with open(output_file_path, "r") as f:
            report_data = json.load(f)

        self.assertEqual(len(report_data), 1)
        self.assertEqual(report_data[0]["filename"], "valid.json")
        self.assertEqual(len(report_data[0]["errors"]), 0)
        self.assertEqual(report_data[0]["total_entries"], 1)

        os.remove(output_file_path) # Clean up output file

    def test_validate_folder_invalid_json_file(self):
        # Create a temporary output file path
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_out:
            output_file_path = tmp_out.name

        # Case 2: Invalid JSON file
        invalid_file_path = os.path.join(self.test_dir.name, "invalid.json")
        with open(invalid_file_path, "w") as f:
            f.write('{"results": [') # Invalid JSON

        required_fields = ["title", "publication_date", "agency"]
        validate_folder(self.test_dir.name, required_fields, output_file_path)

        self.assertTrue(os.path.exists(output_file_path))
        with open(output_file_path, "r") as f:
            report_data = json.load(f)
        
        self.assertEqual(len(report_data), 1)
        self.assertEqual(report_data[0]["filename"], "invalid.json")
        self.assertTrue(report_data[0]["error"].startswith("JSON decode error:"))

        os.remove(invalid_file_path) # Clean up invalid file for next test
        os.remove(output_file_path) # Clean up output file


    def test_validate_folder_missing_fields_file(self):
        # Create a temporary output file path
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_out:
            output_file_path = tmp_out.name

        # Case 3: File with missing fields
        missing_fields_data = {"results": [{"title": "Test Title Only"}]}
        missing_fields_file_path = os.path.join(self.test_dir.name, "missing.json")
        with open(missing_fields_file_path, "w") as f:
            json.dump(missing_fields_data, f)

        required_fields = ["title", "publication_date", "agency"]
        validate_folder(self.test_dir.name, required_fields, output_file_path)

        self.assertTrue(os.path.exists(output_file_path))
        with open(output_file_path, "r") as f:
            report_data = json.load(f)

        self.assertEqual(len(report_data), 1)
        self.assertEqual(report_data[0]["filename"], "missing.json")
        self.assertEqual(len(report_data[0]["errors"]), 1)
        self.assertEqual(report_data[0]["total_entries"], 1)
        self.assertIn("publication_date", report_data[0]["errors"][0]["missing_fields"])
        self.assertIn("agency", report_data[0]["errors"][0]["missing_fields"])
        
        os.remove(missing_fields_file_path) # Clean up missing fields file
        os.remove(output_file_path) # Clean up output file


    def test_validate_folder_multiple_files(self):
        # Create a temporary output file path
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_out:
            output_file_path = tmp_out.name

        # Create a mix of files
        # Valid file
        valid_data = {"results": [{"title": "Valid Title", "publication_date": "2023-01-01", "agency": "Valid Agency"}]}
        valid_file_path = os.path.join(self.test_dir.name, "valid.json")
        with open(valid_file_path, "w") as f:
            json.dump(valid_data, f)

        # Invalid JSON file
        invalid_file_path = os.path.join(self.test_dir.name, "invalid.json")
        with open(invalid_file_path, "w") as f:
            f.write('{"results": [')

        # File with missing fields
        missing_fields_data = {"results": [{"title": "Missing Fields Title"}]} # Missing pub_date and agency
        missing_fields_file_path = os.path.join(self.test_dir.name, "missing.json")
        with open(missing_fields_file_path, "w") as f:
            json.dump(missing_fields_data, f)

        required_fields = ["title", "publication_date", "agency"]
        validate_folder(self.test_dir.name, required_fields, output_file_path)

        self.assertTrue(os.path.exists(output_file_path))
        with open(output_file_path, "r") as f:
            report_data = json.load(f)
        
        # Sort report data by filename to ensure consistent order for assertions
        report_data.sort(key=lambda x: x.get("filename", ""))

        self.assertEqual(len(report_data), 3)

        # Check invalid.json
        self.assertEqual(report_data[0]["filename"], "invalid.json")
        self.assertTrue(report_data[0]["error"].startswith("JSON decode error:"))

        # Check missing.json
        self.assertEqual(report_data[1]["filename"], "missing.json")
        self.assertEqual(len(report_data[1]["errors"]), 1)
        self.assertEqual(report_data[1]["total_entries"], 1)
        self.assertIn("publication_date", report_data[1]["errors"][0]["missing_fields"])
        self.assertIn("agency", report_data[1]["errors"][0]["missing_fields"])


        # Check valid.json
        self.assertEqual(report_data[2]["filename"], "valid.json")
        self.assertEqual(len(report_data[2]["errors"]), 0)
        self.assertEqual(report_data[2]["total_entries"], 1)

        os.remove(output_file_path) # Clean up output file


if __name__ == '__main__':
    unittest.main()
