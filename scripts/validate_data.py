import argparse
import json
import os


def validate_file(file_path, required_fields):
    """
    Validates a single JSON file against required fields.

    Parameters:
        file_path (str): Path to the JSON file.
        required_fields (list): List of fields that must exist in each JSON entry.

    Returns:
        dict: Validation results including errors and summary.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            return {"file": file_path, "error": f"JSON decode error: {e}"}

    results = data.get("results", [])
    errors = []

    for idx, entry in enumerate(results):
        missing_fields = [field for field in required_fields if field not in entry]
        if missing_fields:
            errors.append(
                {
                    "index": idx,
                    "missing_fields": missing_fields,
                    "entry_summary": {
                        k: entry.get(k, None) for k in required_fields if k in entry
                    },
                }
            )

    return {
        "file": file_path,
        "total_entries": len(results),
        "errors": errors,
    }


def validate_folder(input_folder, required_fields, output_file):
    """
    Validates all JSON files in a folder.

    Parameters:
        input_folder (str): Path to the folder containing JSON files.
        required_fields (list): List of fields that must exist in each JSON entry.
        output_file (str): Path to save the validation summary.
    """
    validation_results = []

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(input_folder, filename)
            result = validate_file(file_path, required_fields)
            validation_results.append(result)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)

    print(f"Validation results saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate JSON data files against required fields."
    )
    parser.add_argument(
        "--input_folder",
        required=True,
        help="Folder containing JSON files to validate.",
    )
    parser.add_argument(
        "--output_file", required=True, help="File to save validation results."
    )
    parser.add_argument(
        "--required_fields",
        nargs="+",
        default=["title", "publication_date", "agency"],
        help="Required JSON fields. Default: title, publication_date, agency.",
    )

    args = parser.parse_args()

    validate_folder(
        input_folder=args.input_folder,
        required_fields=args.required_fields,
        output_file=args.output_file,
    )
