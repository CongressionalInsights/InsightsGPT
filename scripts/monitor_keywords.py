import argparse
import json
import os


def monitor_keywords(input_folder, output_folder, keywords):
    """
    Scans JSON files for entries containing specified keywords and saves flagged entries.

    Parameters:
        input_folder (str): Folder containing JSON files to scan.
        output_folder (str): Folder to save flagged results.
        keywords (list): List of keywords to monitor.
    """
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if not filename.endswith(".json"):
            continue

        input_path = os.path.join(input_folder, filename)

        with open(input_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error decoding {input_path}: {e}")
                continue

        results = data.get("results", [])
        flagged_results = []

        for entry in results:
            for keyword in keywords:
                if keyword.lower() in json.dumps(entry).lower():
                    flagged_results.append(entry)
                    break

        if flagged_results:
            output_filename = f"flagged_{filename}"
            output_path = os.path.join(output_folder, output_filename)

            with open(output_path, "w", encoding="utf-8") as out_f:
                json.dump(
                    {"results": flagged_results}, out_f, indent=2, ensure_ascii=False
                )

            print(f"Flagged results saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor keywords in JSON data.")
    parser.add_argument(
        "--input_folder", required=True, help="Folder containing JSON files to monitor."
    )
    parser.add_argument(
        "--output_folder", required=True, help="Folder to save flagged results."
    )
    parser.add_argument(
        "--keywords", nargs="+", required=True, help="List of keywords to monitor."
    )

    args = parser.parse_args()

    monitor_keywords(
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        keywords=args.keywords,
    )
