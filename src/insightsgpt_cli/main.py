import argparse
import subprocess
import sys
import os

# Determine the base directory of the project (where 'scripts/' lives)
# 'insightsgpt_cli' is in 'src/', so we need to go up three levels from __file__
# (main.py -> insightsgpt_cli -> src -> project_root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')

def main():
    parser = argparse.ArgumentParser(
        description="InsightsGPT CLI tool. Provides access to project scripts.",
        formatter_class=argparse.RawTextHelpFormatter # To allow for better formatting in help messages
    )
    # Add version argument
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.1.0', # Corresponds to pyproject.toml version
        help="Show program's version number and exit."
    )
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available subcommands. Use <subcommand> --help for more details.",
        required=True,
        metavar="<subcommand>"
    )

    # Script mapping
    script_map = {
        "fetch": {
            "script": "fetch_fr.py",
            "help": "Fetches data using scripts/fetch_fr.py.\nAll subsequent arguments are passed directly to the script.\nExample: insightsgpt fetch documents-search --term \"climate change\""
        },
        "validate": {
            "script": "validate_data.py",
            "help": "Validates data using scripts/validate_data.py.\nAll subsequent arguments are passed directly to the script.\nExample: insightsgpt validate --input_folder data/"
        },
        "keywords": {
            "script": "monitor_keywords.py",
            "help": "Monitors keywords using scripts/monitor_keywords.py.\nAll subsequent arguments are passed directly to the script.\nExample: insightsgpt keywords --keywords \"AI,policy\""
        },
        "visualize": {
            "script": "generate_visualizations.py",
            "help": "Generates visualizations using scripts/generate_visualizations.py.\nAll subsequent arguments are passed directly to the script.\nExample: insightsgpt visualize --input_folder data/ --output_folder visualizations/"
        },
    }

    # Dynamically create subparsers
    for cmd, info in script_map.items():
        cmd_parser = subparsers.add_parser(
            cmd,
            help=info["help"],
            description=info["help"] # Show full help on subcommand --help
        )
        cmd_parser.add_argument(
            "script_args",
            nargs=argparse.REMAINDER,
            help="Arguments to be passed to the underlying script."
        )

    args = parser.parse_args()

    script_name = script_map.get(args.command, {}).get("script")
    if not script_name:
        # This case should ideally not be reached if subparsers are set to required.
        parser.error(f"Internal error: Unknown command '{args.command}' without a script mapping.")

    script_path = os.path.join(SCRIPTS_DIR, script_name)
    
    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}", file=sys.stderr)
        print(f"BASE_DIR was: {BASE_DIR}", file=sys.stderr)
        print(f"SCRIPTS_DIR was: {SCRIPTS_DIR}", file=sys.stderr)
        sys.exit(1)

    # Construct the command to run
    command_to_run = [sys.executable, script_path] + args.script_args
    
    try:
        # Execute the command
        # We use check=False because we want to manually handle the exit code
        # and print stdout/stderr.
        result = subprocess.run(command_to_run, capture_output=True, text=True, check=False)
        
        # Print stdout and stderr from the script
        if result.stdout:
            print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, end='', file=sys.stderr)
        
        # Exit with the script's return code
        sys.exit(result.returncode)
        
    except FileNotFoundError:
        print(f"Error: Python interpreter or script not found. Ensure Python is in your PATH and the script exists.", file=sys.stderr)
        print(f"Attempted command: {' '.join(command_to_run)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while trying to run the script '{script_name}': {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
