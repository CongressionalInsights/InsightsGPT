import pytest
import json
import os
import pandas as pd

# Add project root to sys.path for module import
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts import process_and_integrate_signals
# from scripts.sentiment_analysis_tool import get_sentiment_score # Will be mocked

# --- Sample Data ---

SAMPLE_PROCESSED_BILL_METADATA_CSV_CONTENT = """bill_id,title,policy_area,legislative_subjects
117-HR-1,Test Bill One,Economy,Taxation;Budget
117-S-2,Test Bill Two,Health,Healthcare;Research
116-HR-100,Old Bill,Science,Technology
"""

SAMPLE_MEDIA_DATA_CONTENT_BILL1 = {
    "keywords": "117-HR-1", # Matches a bill_id
    "articles": [
        {"title": "Good news for HR1", "description": "This bill is great and positive."},
        {"title": "Concerns about HR1", "description": "Some negative points raised."}
    ]
}

SAMPLE_MEDIA_DATA_CONTENT_TOPIC_HEALTH = {
    "keywords": "Healthcare Policy", # General topic
    "articles": [
        {"title": "Healthcare advancements", "description": "Positive support for new healthcare ideas."},
        {"title": "Healthcare debates", "description": "Neutral stance on ongoing debates."}
    ]
}

SAMPLE_LOBBYING_DATA_CONTENT_BILL1 = { # Matches a bill_id
    "query": {"term": "117-HR-1", "type": "bill_id"},
    "filings": [
        {"filer": "Lobby Firm X", "client": "Client A", "amount_spent": 10000},
        {"filer": "Lobby Firm Y", "client": "Client B", "amount_spent": 5000}
    ]
}

SAMPLE_LOBBYING_DATA_CONTENT_TOPIC_ECONOMY = { # General topic
    "query": {"term": "Economy Policy", "type": "issue"},
    "filings": [
        {"filer": "Corp Z", "client": "Corp Z", "amount_spent": 50000}
    ]
}


# --- Fixtures ---

@pytest.fixture
def temp_raw_signals_dir(tmp_path):
    """Creates a temporary raw signals data directory with sample JSON files."""
    raw_dir = tmp_path / "data"
    raw_dir.mkdir()
    
    with open(raw_dir / "media_data_bill1_id_hr1_20230101000000.json", 'w') as f:
        json.dump(SAMPLE_MEDIA_DATA_CONTENT_BILL1, f)
    with open(raw_dir / "media_data_topic_health_20230101000000.json", 'w') as f:
        json.dump(SAMPLE_MEDIA_DATA_CONTENT_TOPIC_HEALTH, f)
        
    with open(raw_dir / "lobbying_data_bill1_id_hr1_20230101000000.json", 'w') as f:
        json.dump(SAMPLE_LOBBYING_DATA_CONTENT_BILL1, f)
    with open(raw_dir / "lobbying_data_topic_economy_20230101000000.json", 'w') as f:
        json.dump(SAMPLE_LOBBYING_DATA_CONTENT_TOPIC_ECONOMY, f)
        
    return raw_dir

@pytest.fixture
def temp_processed_bill_metadata_dir(tmp_path):
    """Creates a temporary directory for processed bill metadata (input to this script)."""
    processed_dir = tmp_path / "datasets"
    processed_dir.mkdir()
    with open(processed_dir / "processed_bill_metadata.csv", 'w') as f:
        f.write(SAMPLE_PROCESSED_BILL_METADATA_CSV_CONTENT)
    return processed_dir

@pytest.fixture
def mock_sentiment_analyzer(mocker):
    """Mocks the get_sentiment_score function."""
    mock_func = mocker.patch("scripts.process_and_integrate_signals.get_sentiment_score")
    
    def side_effect_func(text):
        text_lower = text.lower()
        if "great and positive" in text_lower:
            return {"label": "positive", "score": 0.8}
        if "negative points" in text_lower:
            return {"label": "negative", "score": -0.6}
        if "healthcare advancements" in text_lower:
            return {"label": "positive", "score": 0.7}
        if "neutral stance" in text_lower: # for "Healthcare debates"
             return {"label": "neutral", "score": 0.1} # Slight positive neutral
        return {"label": "neutral", "score": 0.0}
        
    mock_func.side_effect = side_effect_func
    return mock_func


# --- Tests for Core Processing Functions ---

def test_process_media_files(temp_raw_signals_dir, mock_sentiment_analyzer, mocker):
    """Test processing of media files and sentiment aggregation."""
    mocker.patch("scripts.process_and_integrate_signals.RAW_SIGNALS_DIR", str(temp_raw_signals_dir))
    
    media_summary_df = process_and_integrate_signals.process_media_files()
    
    assert not media_summary_df.empty
    assert len(media_summary_df) == 2 # Two media files processed
    
    # Check data for "117-HR-1"
    hr1_media_row = media_summary_df[media_summary_df["media_search_keyword"] == "117-HR-1"].iloc[0]
    assert hr1_media_row["avg_sentiment_score"] == pytest.approx((0.8 - 0.6) / 2)
    assert hr1_media_row["num_positive_articles"] == 1
    assert hr1_media_row["num_negative_articles"] == 1
    assert hr1_media_row["num_neutral_articles"] == 0
    assert hr1_media_row["total_articles_analyzed"] == 2
    
    # Check data for "Healthcare Policy"
    health_media_row = media_summary_df[media_summary_df["media_search_keyword"] == "Healthcare Policy"].iloc[0]
    assert health_media_row["avg_sentiment_score"] == pytest.approx((0.7 + 0.1) / 2)
    assert health_media_row["num_positive_articles"] == 1
    assert health_media_row["num_neutral_articles"] == 1 # Based on our mock_sentiment_analyzer for "neutral stance"
    assert health_media_row["total_articles_analyzed"] == 2


def test_process_lobbying_files(temp_raw_signals_dir, mocker):
    """Test processing of (simulated) lobbying files."""
    mocker.patch("scripts.process_and_integrate_signals.RAW_SIGNALS_DIR", str(temp_raw_signals_dir))
    
    lobbying_summary_df = process_and_integrate_signals.process_lobbying_files()
    
    assert not lobbying_summary_df.empty
    assert len(lobbying_summary_df) == 2 # Two lobbying files
    
    # Check data for "117-HR-1"
    hr1_lobby_row = lobbying_summary_df[lobbying_summary_df["lobbying_search_topic"] == "117-HR-1"].iloc[0]
    assert hr1_lobby_row["num_lobbying_filings"] == 2
    assert hr1_lobby_row["total_lobbying_amount_simulated"] == 15000
    assert hr1_lobby_row["num_unique_lobbying_filers"] == 2
    assert hr1_lobby_row["num_unique_lobbying_clients"] == 2

    # Check data for "Economy Policy"
    econ_lobby_row = lobbying_summary_df[lobbying_summary_df["lobbying_search_topic"] == "Economy Policy"].iloc[0]
    assert econ_lobby_row["num_lobbying_filings"] == 1
    assert econ_lobby_row["total_lobbying_amount_simulated"] == 50000

# --- Test Main Functionality ---

def test_main_integration_logic(temp_raw_signals_dir, temp_processed_bill_metadata_dir, mock_sentiment_analyzer, mocker):
    """Test the main integration logic and CSV output."""
    
    # Patch constants in the module to use temp directories
    mocker.patch("scripts.process_and_integrate_signals.RAW_SIGNALS_DIR", str(temp_raw_signals_dir))
    mocker.patch("scripts.process_and_integrate_signals.PROCESSED_METADATA_PATH", str(temp_processed_bill_metadata_dir / "processed_bill_metadata.csv"))
    mocker.patch("scripts.process_and_integrate_signals.OUTPUT_DIR", str(temp_processed_bill_metadata_dir)) # Save output in same temp "datasets" dir

    process_and_integrate_signals.main()
    
    output_csv_path = temp_processed_bill_metadata_dir / process_and_integrate_signals.INTEGRATED_OUTPUT_CSV_FILENAME
    assert output_csv_path.exists()
    
    df = pd.read_csv(output_csv_path)
    
    assert len(df) == 3 # Original number of bills from processed_bill_metadata.csv
    
    # Check for integrated columns from media signals
    # For "117-HR-1" (sanitized: "117_hr_1")
    assert "media_117_hr_1_avg_score" in df.columns
    assert "media_117_hr_1_pos_articles" in df.columns
    # For "Healthcare Policy" (sanitized: "healthcare_policy")
    assert "media_healthcare_policy_avg_score" in df.columns
    
    # Check for integrated columns from lobbying signals
    # For "117-HR-1"
    assert "lobby_117_hr_1_num_filings" in df.columns
    assert "lobby_117_hr_1_total_amount_sim" in df.columns
    # For "Economy Policy"
    assert "lobby_economy_policy_num_filings" in df.columns

    # Verify some integrated values (all rows get topic-level signals)
    # Media data for keyword "117-HR-1"
    expected_hr1_media_score = pytest.approx((0.8 - 0.6) / 2)
    assert df["media_117_hr_1_avg_score"].iloc[0] == expected_hr1_media_score 
    assert df["media_117_hr_1_pos_articles"].iloc[0] == 1

    # Lobbying data for keyword "117-HR-1"
    assert df["lobby_117_hr_1_num_filings"].iloc[0] == 2
    assert df["lobby_117_hr_1_total_amount_sim"].iloc[0] == 15000
    
    # Topic "Healthcare Policy" media data should be on all rows
    expected_health_media_score = pytest.approx((0.7 + 0.1) / 2)
    assert df["media_healthcare_policy_avg_score"].iloc[0] == expected_health_media_score
    assert df["media_healthcare_policy_avg_score"].iloc[1] == expected_health_media_score 
    
    # Topic "Economy Policy" lobbying data should be on all rows
    assert df["lobby_economy_policy_num_filings"].iloc[0] == 1
    assert df["lobby_economy_policy_num_filings"].iloc[1] == 1


def test_main_no_processed_metadata_file(tmp_path, mocker, capsys):
    """Test main when processed_bill_metadata.csv is missing."""
    raw_dir = tmp_path / "data"
    raw_dir.mkdir() # Needs to exist to avoid error there
    
    mocker.patch("scripts.process_and_integrate_signals.RAW_SIGNALS_DIR", str(raw_dir))
    mocker.patch("scripts.process_and_integrate_signals.PROCESSED_METADATA_PATH", str(tmp_path / "non_existent_processed_metadata.csv"))
    
    process_and_integrate_signals.main()
    
    captured = capsys.readouterr()
    assert "Error: Processed bill metadata file not found" in captured.out


def test_main_no_signal_files(temp_processed_bill_metadata_dir, mocker, capsys):
    """Test main when no signal files (media or lobbying) are found."""
    empty_raw_signals_dir = temp_processed_bill_metadata_dir / "empty_data" # Use a subfolder of this fixture
    empty_raw_signals_dir.mkdir()

    mocker.patch("scripts.process_and_integrate_signals.RAW_SIGNALS_DIR", str(empty_raw_signals_dir))
    mocker.patch("scripts.process_and_integrate_signals.PROCESSED_METADATA_PATH", str(temp_processed_bill_metadata_dir / "processed_bill_metadata.csv"))
    mocker.patch("scripts.process_and_integrate_signals.OUTPUT_DIR", str(temp_processed_bill_metadata_dir))

    process_and_integrate_signals.main()
    
    captured = capsys.readouterr()
    # Check for messages indicating no files were processed for media/lobbying
    assert "Found 0 media data files to process." in captured.out
    assert "No media sentiment data was processed." in captured.out
    assert "Found 0 lobbying data files to process." in captured.out
    assert "No lobbying data was processed." in captured.out
    
    # CSV should still be created but without new signal columns beyond the original ones
    output_csv_path = temp_processed_bill_metadata_dir / process_and_integrate_signals.INTEGRATED_OUTPUT_CSV_FILENAME
    assert output_csv_path.exists()
    df = pd.read_csv(output_csv_path)
    assert len(df.columns) == len(SAMPLE_PROCESSED_BILL_METADATA_CSV_CONTENT.splitlines()[0].split(',')) # Only original columns
    assert "media_" not in "".join(df.columns) # No media columns added
    assert "lobby_" not in "".join(df.columns) # No lobbying columns added
