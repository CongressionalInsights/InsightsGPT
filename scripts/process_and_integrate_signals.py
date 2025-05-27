import os
import json
import pandas as pd
from sentiment_analysis_tool import get_sentiment_score # Assuming it's in the same directory or Python path

# --- Configuration ---
RAW_SIGNALS_DIR = "data"
PROCESSED_METADATA_PATH = os.path.join("datasets", "processed_bill_metadata.csv")
OUTPUT_DIR = "datasets"
INTEGRATED_OUTPUT_CSV_FILENAME = "integrated_bill_data_with_signals.csv"

# --- Helper Functions ---
def load_json_file(filepath: str) -> dict | None:
    """Loads a JSON file and returns its content as a dictionary."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {filepath}")
    except IOError:
        print(f"Error reading file: {filepath}")
    return None

def sanitize_column_name(name: str) -> str:
    """Sanitizes a string to be used as a DataFrame column name."""
    return "".join(c if c.isalnum() else "_" for c in name).lower()

# --- Process Media Sentiment Data ---
def process_media_files() -> pd.DataFrame:
    """
    Loads all media_data_*.json files, performs sentiment analysis, 
    and aggregates sentiment per search keyword.
    """
    all_media_keywords_sentiment = []
    media_files = [f for f in os.listdir(RAW_SIGNALS_DIR) if f.startswith("media_data_") and f.endswith(".json")]
    
    print(f"Found {len(media_files)} media data files to process.")

    for filename in media_files:
        filepath = os.path.join(RAW_SIGNALS_DIR, filename)
        content = load_json_file(filepath)

        if not content or "articles" not in content or "keywords" not in content:
            print(f"Skipping media file {filename}: Invalid format or missing essential keys.")
            continue
        
        search_keywords = content["keywords"]
        articles = content["articles"]
        
        if not articles:
            print(f"No articles found for keywords '{search_keywords}' in {filename}.")
            continue

        sentiment_scores = []
        num_positive = 0
        num_negative = 0
        num_neutral = 0

        for article in articles:
            text_to_analyze = article.get("description") or article.get("title") or ""
            if text_to_analyze:
                sentiment_result = get_sentiment_score(text_to_analyze)
                sentiment_scores.append(sentiment_result["score"])
                if sentiment_result["label"] == "positive":
                    num_positive += 1
                elif sentiment_result["label"] == "negative":
                    num_negative += 1
                else:
                    num_neutral += 1
        
        avg_sentiment_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        all_media_keywords_sentiment.append({
            "media_search_keyword": search_keywords, # This is the key for joining/mapping
            "avg_sentiment_score": round(avg_sentiment_score, 4),
            "num_positive_articles": num_positive,
            "num_negative_articles": num_negative,
            "num_neutral_articles": num_neutral,
            "total_articles_analyzed": len(sentiment_scores)
        })
        print(f"Processed media sentiment for keywords: '{search_keywords}' - Avg Score: {avg_sentiment_score:.2f}")

    if not all_media_keywords_sentiment:
        print("No media sentiment data was processed.")
        return pd.DataFrame() # Return empty DataFrame

    return pd.DataFrame(all_media_keywords_sentiment)

# --- Process Lobbying Data ---
def process_lobbying_files() -> pd.DataFrame:
    """
    Loads all lobbying_data_*.json files (simulated), 
    and aggregates data per search query/topic.
    """
    all_lobbying_summary = []
    lobbying_files = [f for f in os.listdir(RAW_SIGNALS_DIR) if f.startswith("lobbying_data_") and f.endswith(".json")]

    print(f"Found {len(lobbying_files)} lobbying data files to process.")

    for filename in lobbying_files:
        filepath = os.path.join(RAW_SIGNALS_DIR, filename)
        content = load_json_file(filepath)

        if not content or "query" not in content or "filings" not in content:
            print(f"Skipping lobbying file {filename}: Invalid format or missing essential keys.")
            continue
            
        search_term = content["query"].get("term", "unknown_topic")
        filings = content.get("filings", [])

        num_filings = len(filings)
        total_amount_spent = 0 # Simulated amounts
        unique_filers = set()
        unique_clients = set()

        for filing in filings:
            total_amount_spent += filing.get("amount_spent", 0)
            if filing.get("filer"):
                unique_filers.add(filing["filer"])
            if filing.get("client"):
                unique_clients.add(filing["client"])
        
        all_lobbying_summary.append({
            "lobbying_search_topic": search_term, # Key for joining/mapping
            "num_lobbying_filings": num_filings,
            "total_lobbying_amount_simulated": total_amount_spent,
            "num_unique_lobbying_filers": len(unique_filers),
            "num_unique_lobbying_clients": len(unique_clients)
        })
        print(f"Processed lobbying data for topic: '{search_term}' - Filings: {num_filings}")

    if not all_lobbying_summary:
        print("No lobbying data was processed.")
        return pd.DataFrame()

    return pd.DataFrame(all_lobbying_summary)

# --- Main Integration Logic ---
def main():
    print("Starting processing and integration of real-time signals...")

    # 1. Load processed bill metadata
    if not os.path.exists(PROCESSED_METADATA_PATH):
        print(f"Error: Processed bill metadata file not found at {PROCESSED_METADATA_PATH}. Exiting.")
        return
    
    bill_metadata_df = pd.read_csv(PROCESSED_METADATA_PATH)
    print(f"Loaded {len(bill_metadata_df)} records from {PROCESSED_METADATA_PATH}")

    # 2. Process media sentiment data
    media_sentiment_summary_df = process_media_files()
    
    # 3. Process lobbying data
    lobbying_summary_df = process_lobbying_files()

    # 4. Integrate data
    # Strategy:
    #   - For media/lobbying data where 'search_keyword'/'search_topic' might be a bill_id:
    #     Try a direct merge on bill_id.
    #   - For media/lobbying data where 'search_keyword'/'search_topic' is a general topic:
    #     These represent general sentiment/lobbying activity for that topic.
    #     We can attach these to bills based on 'policy_area' or 'legislative_subjects'.
    #     For simplicity here, if a direct bill_id match isn't made, we'll store these topic-level
    #     signals separately or decide on a more complex mapping strategy if needed.
    #
    # Let's assume bill_id format is like '117-hr-1' or '117-s-1'.
    # The keywords used in fetch_real_time_signals might be "H.R. 1" or "S.1" or "117 H.R. 1".
    # We need a robust way to map these. For now, we assume search keywords can be directly mapped or are topics.

    integrated_df = bill_metadata_df.copy()

    if not media_sentiment_summary_df.empty:
        print("\nIntegrating media sentiment data...")
        # Attempt to merge if 'media_search_keyword' can be interpreted as a 'bill_id'
        # This is a simplified approach. A more robust solution would normalize bill_ids and keywords.
        # For keywords that are topics, we might add them differently.
        # Example: If media_search_keyword is 'climate_change', we could add columns
        # 'media_sentiment_climate_change_score', etc.
        
        for idx, row in media_sentiment_summary_df.iterrows():
            keyword = row["media_search_keyword"]
            # Attempt to match keyword with bill_id (this is a naive match)
            # A proper match would involve parsing keyword to congress-type-number.
            # For now, let's assume keyword could be a direct bill_id or a topic slug.
            
            # If keyword could be a bill_id
            # matching_bills = integrated_df[integrated_df['bill_id'] == keyword] # This requires exact match
            
            # For this version, let's add keyword-specific columns for all topics/keywords found
            # This will create many columns if many keywords were searched.
            col_prefix = f"media_{sanitize_column_name(keyword)}"
            integrated_df[f"{col_prefix}_avg_score"] = row["avg_sentiment_score"]
            integrated_df[f"{col_prefix}_pos_articles"] = row["num_positive_articles"]
            integrated_df[f"{col_prefix}_neg_articles"] = row["num_negative_articles"]
            integrated_df[f"{col_prefix}_neu_articles"] = row["num_neutral_articles"]
            print(f"Added media sentiment columns for keyword/topic: {keyword}")
            # This is a broad application of topic sentiment to ALL bills.
            # A more targeted approach would be to map topic keywords to bills via 'policy_area' or 'legislative_subjects'.
            # E.g., if bill['policy_area'] == 'Energy' and keyword is 'renewable_energy_legislation'.

    if not lobbying_summary_df.empty:
        print("\nIntegrating lobbying data...")
        # Similar approach for lobbying data
        for idx, row in lobbying_summary_df.iterrows():
            topic = row["lobbying_search_topic"]
            col_prefix = f"lobby_{sanitize_column_name(topic)}"
            integrated_df[f"{col_prefix}_num_filings"] = row["num_lobbying_filings"]
            integrated_df[f"{col_prefix}_total_amount_sim"] = row["total_lobbying_amount_simulated"]
            integrated_df[f"{col_prefix}_num_filers"] = row["num_unique_lobbying_filers"]
            print(f"Added lobbying data columns for topic: {topic}")
            # Again, this broadly applies topic-level lobbying data to all bills.

    # A more refined merge strategy for future consideration:
    # 1. Identify if a media_search_keyword or lobbying_search_topic IS a bill_id.
    #    bill_ids_in_media = media_sentiment_summary_df['media_search_keyword'] # filter these if they are bill_ids
    #    media_bill_specific_df = media_sentiment_summary_df[media_sentiment_summary_df['media_search_keyword'].isin(integrated_df['bill_id'])]
    #    integrated_df = pd.merge(integrated_df, media_bill_specific_df, left_on='bill_id', right_on='media_search_keyword', how='left')
    #
    # 2. For topic-based keywords (those not matching a bill_id):
    #    Map these topics to bills using 'policy_area' or 'legislative_subjects'.
    #    Example:
    #    for topic_keyword in media_topic_keywords:
    #        sentiment_score = media_sentiment_summary_df[media_sentiment_summary_df['media_search_keyword'] == topic_keyword]['avg_sentiment_score'].iloc[0]
    #        # Apply this score to bills where bill['policy_area'] relates to topic_keyword
    #        # This requires a mapping: policy_area -> topic_keyword
    #        relevant_bills_mask = integrated_df['policy_area'].str.contains(topic_keyword, case=False, na=False) # Simple substring match
    #        integrated_df.loc[relevant_bills_mask, f'topic_sentiment_{sanitize_column_name(topic_keyword)}'] = sentiment_score


    # 5. Save integrated data
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    output_path = os.path.join(OUTPUT_DIR, INTEGRATED_OUTPUT_CSV_FILENAME)
    try:
        integrated_df.to_csv(output_path, index=False)
        print(f"\nIntegrated data saved successfully to: {output_path}")
        print(f"DataFrame shape: {integrated_df.shape}")
        print(f"Columns: {integrated_df.columns.tolist()}")
    except IOError as e:
        print(f"Error saving integrated data to CSV: {e}")

if __name__ == "__main__":
    # Ensure pandas is installed: pip install pandas
    # Ensure sentiment_analysis_tool.py is in the same directory or accessible via PYTHONPATH
    main()
    print("Processing and integration script finished.")
