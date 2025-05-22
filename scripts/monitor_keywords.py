import argparse
import json
import os
import sys


def monitor_keywords(input_folder, output_folder, keywords):
    """
    # Simple comment

    # Intentionally leaving line 8 blank to address a persistent flake8 E501 error.
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


def load_keywords_from_args(args_list=None):
    parser = argparse.ArgumentParser(description="Monitor keywords in JSON data.")
    parser.add_argument(
        "--input_folder", required=True, help="Folder containing JSON files to monitor."
    )
    parser.add_argument(
        "--output_folder", required=True, help="Folder to save flagged results."
    )
    parser.add_argument(
        "--keywords", nargs="+", required=False, help="List of keywords to monitor (if provided, this overrides the --keywords-file option)."
    )
    parser.add_argument(
        '--keywords-file', default='config/keywords.txt', help='Path to a file containing keywords, one per line. Used if --keywords is not provided. Default: config/keywords.txt'
    )

    args = parser.parse_args(args_list if args_list is not None else sys.argv[1:])

    final_keywords = []

    if args.keywords:  # User explicitly provided --keywords
        final_keywords = args.keywords
        # print(f"Using keywords from --keywords command-line argument: {final_keywords}") # Optional: for CLI use
    elif args.keywords_file:  # --keywords not provided, try --keywords-file
        try:
            if os.path.exists(args.keywords_file):
                with open(args.keywords_file, 'r', encoding='utf-8') as f:
                    final_keywords = [line.strip() for line in f if line.strip()]
                if final_keywords:
                    # print(f"Using keywords from file '{args.keywords_file}': {final_keywords}") # Optional
                    pass
                else:
                    raise ValueError(f"Keywords file '{args.keywords_file}' is empty and no --keywords argument provided.")
            else:
                raise ValueError(f"Keywords file '{args.keywords_file}' not found and no --keywords argument provided.")
        except IOError as e:
            raise ValueError(f"Could not read keywords file '{args.keywords_file}': {e}")
    else:
        # This branch is unlikely given the default for --keywords-file
        raise ValueError("No keywords source determined. Check --keywords or --keywords-file arguments.")

    if not final_keywords: # Safeguard
        raise ValueError("No keywords were loaded. Ensure --keywords is used or --keywords-file is valid and non-empty.")

    return args.input_folder, args.output_folder, final_keywords


if __name__ == "__main__":
    try:
        input_f, output_f, keywords_to_monitor = load_keywords_from_args()
        # Optional: print statements from load_keywords_from_args can be moved here if desired for CLI verbosity
        if any(arg.startswith('--keywords-file') or not any(arg.startswith('--keywords') for arg in sys.argv) for arg in sys.argv[1:]):
             # Attempted to use file or fell back to default file
            used_file = next((arg.split('=')[1] if '=' in arg else sys.argv[i+1] for i, arg in enumerate(sys.argv[1:]) if arg == '--keywords-file'), 'config/keywords.txt')
            if any(arg.startswith('--keywords=') or arg == '--keywords' for arg in sys.argv[1:]): # if --keywords also present
                 print(f"Using keywords from --keywords command-line argument: {keywords_to_monitor}")
            elif keywords_to_monitor:
                 print(f"Using keywords from file '{used_file}': {keywords_to_monitor}")
        elif keywords_to_monitor : # Used --keywords and it was not overridden by file (which it shouldn't be)
            print(f"Using keywords from --keywords command-line argument: {keywords_to_monitor}")


        monitor_keywords(
            input_folder=input_f,
            output_folder=output_f,
            keywords=keywords_to_monitor,
        )
    except ValueError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e: # Catch any other unexpected errors during setup or run
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
