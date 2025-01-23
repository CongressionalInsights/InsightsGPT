import os
import json
import argparse

def filter_data(input_folder, output_folder, keyword=None, agency=None, year=None):
    """
    Filters data from JSON files in the input folder based on keyword, agency, and year.
    Saves the filtered results into the output folder.
    """
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if not filename.endswith(".json"):
            continue

        input_path = os.path.join(input_folder, filename)

        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = data.get("results", [])
        filtered_results = []

        for entry in results:
            if keyword and keyword.lower() not in json.dumps(entry).lower():
                continue
            if agency and agency.lower() != entry.get("agency", "").lower():
                continue
            if year and str(year) not in entry.get("publication_date", "")[:4]:
                continue

            filtered_results.append(entry)

        if filtered_results:
            output_filename = f"filtered_{filename}"
            output_path = os.path.join(output_folder, output_filename)

            with open(output_path, "w", encoding="utf-8") as out_f:
                json.dump({"results": filtered_results}, out_f, indent=2, ensure_ascii=False)

            print(f"Filtered data saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter data from JSON files.")
    parser.add_argument("--input_folder", required=True, help="Folder containing JSON files to filter.")
    parser.add_argument("--output_folder", required=True, help="Folder to save filtered results.")
    parser.add_argument("--keyword", help="Keyword to filter by.")
    parser.add_argument("--agency", help="Agency to filter by.")
    parser.add_argument("--year", type=int, help="Publication year to filter by.")

    args = parser.parse_args()

    filter_data(
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        keyword=args.keyword,
        agency=args.agency,
        year=args.year,
    )
