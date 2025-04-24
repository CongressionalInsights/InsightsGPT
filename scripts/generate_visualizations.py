import argparse
import json
import os

import matplotlib.pyplot as plt


def load_data(input_folder):
    """
    Loads JSON data from all files in the input folder.

    Parameters:
        input_folder (str): Path to the folder containing JSON files.

    Returns:
        list: Combined list of JSON entries from all files.
    """
    all_data = []

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(input_folder, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    all_data.extend(data.get("results", []))
                except json.JSONDecodeError as e:
                    print(f"Error decoding {file_path}: {e}")

    return all_data


def plot_publication_trends(data, output_folder):
    """
    Generates a time-series plot of publication trends by year.

    Parameters:
        data (list): List of JSON entries.
        output_folder (str): Folder to save the plot.
    """
    years = {}

    for entry in data:
        publication_date = entry.get("publication_date", "")
        if publication_date:
            year = publication_date[:4]
            if year.isdigit():
                years[year] = years.get(year, 0) + 1

    if not years:
        print("No publication date data found for plotting.")
        return

    # Sort years
    sorted_years = sorted(years.items())
    x, y = zip(*sorted_years)

    plt.figure(figsize=(10, 6))
    plt.plot(x, y, marker="o")
    plt.title("Publication Trends by Year")
    plt.xlabel("Year")
    plt.ylabel("Number of Publications")
    plt.grid()
    plt.tight_layout()

    output_path = os.path.join(output_folder, "publication_trends.png")
    os.makedirs(output_folder, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Plot saved to {output_path}")


def plot_agency_distribution(data, output_folder):
    """
    Generates a bar chart of document counts by agency.

    Parameters:
        data (list): List of JSON entries.
        output_folder (str): Folder to save the plot.
    """
    agencies = {}

    for entry in data:
        agency = entry.get("agency", "Unknown")
        agencies[agency] = agencies.get(agency, 0) + 1

    # Sort by document count
    sorted_agencies = sorted(agencies.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]  # Top 10 agencies
    x, y = zip(*sorted_agencies)

    plt.figure(figsize=(12, 8))
    plt.barh(x, y, color="skyblue")
    plt.title("Top 10 Agencies by Document Count")
    plt.xlabel("Number of Documents")
    plt.ylabel("Agency")
    plt.tight_layout()

    output_path = os.path.join(output_folder, "agency_distribution.png")
    os.makedirs(output_folder, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Plot saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate visualizations from JSON datasets."
    )
    parser.add_argument(
        "--input_folder", required=True, help="Folder containing JSON files to analyze."
    )
    parser.add_argument(
        "--output_folder",
        required=True,
        help="Folder to save generated visualizations.",
    )

    args = parser.parse_args()

    data = load_data(args.input_folder)

    if data:
        plot_publication_trends(data, args.output_folder)
        plot_agency_distribution(data, args.output_folder)
    else:
        print("No valid data found for visualization.")
