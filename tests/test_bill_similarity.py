import pytest
import os
import json
from unittest.mock import patch, MagicMock, mock_open, call
import sys
import io
import contextlib
import logging
import argparse # For creating mock args

# Add scripts directory to sys.path
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    from bill_similarity import (
        main,
        preprocess_text,
        segment_bill,
        find_similar_segments,
        BOILERPLATE_PATTERNS # Import for use in tests
    )
except ImportError as e:
    print(f"Error importing from bill_similarity: {e}")
    print(f"sys.path: {sys.path}")
    pytest.fail(f"Failed to import bill_similarity: {e}")

# --- Fixtures ---

@pytest.fixture
def sample_bill_text_with_boilerplate():
    return """
IN THE SENATE OF THE UNITED STATES, January 1, 2023;
A BILL To do something important.
Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled:
Section 1. This is the first section.
It has some text.

Section 2. This is another section.
With more text for testing.
"""

@pytest.fixture
def sample_bill_text_clean():
    return "this is the first section. it has some text. this is another section. with more text for testing."

@pytest.fixture
def sample_segments1():
    return ["this is segment one from bill one", "common segment for testing similarity"]

@pytest.fixture
def sample_segments2():
    return ["this is segment one from bill two", "common segment for testing similarity", "another segment here"]

@pytest.fixture
def mock_sbert_model():
    mock_model = MagicMock()
    # Mock encode to return simple embeddings (list of lists)
    # The actual values don't matter as much as the structure if cos_sim is also mocked
    mock_model.encode.side_effect = lambda segments, convert_to_tensor: [[float(i+1), float(i+2)] for i, _ in enumerate(segments)]
    return mock_model

@pytest.fixture
def mock_sbert_util():
    mock_util = MagicMock()
    # Mock cos_sim to return a predefined similarity matrix
    # For sample_segments1 (2 segs) and sample_segments2 (3 segs), matrix should be 2x3
    # Let's make seg1[1] and seg2[1] similar
    similarity_matrix = [
        [0.5, 0.2, 0.1],  # Similarities of segs1[0] with segs2
        [0.3, 0.95, 0.4]  # Similarities of segs1[1] with segs2
    ]
    mock_util.cos_sim.return_value = similarity_matrix
    return mock_util

# --- Test Functions ---

def test_preprocess_text_boilerplate_and_case(sample_bill_text_with_boilerplate, sample_bill_text_clean):
    """Test boilerplate removal and lowercasing."""
    processed = preprocess_text(sample_bill_text_with_boilerplate)
    # Exact match might be tricky due to subtle space differences from regex.
    # Check for key phrases' absence and presence.
    assert "in the senate of the united states" not in processed
    assert "be it enacted" not in processed
    assert "section 1" not in processed # The "Section \d+" pattern is removed
    assert "this is the first section" in processed # Content remains
    assert processed == sample_bill_text_clean

def test_preprocess_text_whitespace():
    """Test whitespace normalization."""
    text = "  Extra   spaces  and\nnewlines\t tabs.  "
    expected = "extra spaces and newlines tabs."
    assert preprocess_text(text) == expected

def test_segment_bill_paragraph_based():
    """Test segmentation primarily by paragraphs."""
    text = "First paragraph.\n\nSecond paragraph, quite short.\n\nThird paragraph which is a bit longer and might exceed the segment size if not careful."
    segments = segment_bill(text, segment_size=10, overlap=3) # segment_size in words
    assert len(segments) >= 3 # Expect at least 3 segments, third might be split
    assert "first paragraph." in segments[0]
    assert "second paragraph, quite short." in segments[1]
    assert "third paragraph which is a bit longer" in segments[2] # Start of third paragraph

def test_segment_bill_sliding_window_fallback():
    """Test sliding window fallback for a long paragraph."""
    long_paragraph = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen"
    segments = segment_bill(long_paragraph, segment_size=5, overlap=2)
    # Expected: "one two three four five", "four five six seven eight", "seven eight nine ten eleven", "ten eleven twelve thirteen fourteen", "thirteen fourteen fifteen"
    assert len(segments) == 5
    assert segments[0] == "one two three four five"
    assert segments[1] == "four five six seven eight"
    assert segments[4] == "thirteen fourteen fifteen"

def test_segment_bill_empty_text():
    assert segment_bill("") == []

@patch('scripts.bill_similarity.difflib.unified_diff')
@patch('scripts.bill_similarity.util')
@patch('scripts.bill_similarity.SentenceTransformer')
def test_find_similar_segments_with_sbert(MockSentenceTransformer, mock_util_in_script, mock_unified_diff,
                                         sample_segments1, sample_segments2, mock_sbert_model):
    """Test find_similar_segments when sentence-transformers is available."""
    MockSentenceTransformer.return_value = mock_sbert_model # Our own mock_sbert_model
    scripts.bill_similarity.util = mock_util_in_script # Replace the util in the script's context

    # Define a mock similarity matrix that util.cos_sim would return
    # segs1 has 2 items, segs2 has 3 items. Matrix is 2x3
    # Make segs1[1] ("common segment...") and segs2[1] ("common segment...") highly similar
    mock_similarity_matrix = [[0.1, 0.2, 0.3], [0.4, 0.95, 0.5]]
    mock_util_in_script.cos_sim.return_value = mock_similarity_matrix

    mock_unified_diff.return_value = ["- line1", "+ line2"] # Dummy diff output

    threshold = 0.9
    results = find_similar_segments(sample_segments1, sample_segments2, threshold=threshold)

    MockSentenceTransformer.assert_called_once_with('all-MiniLM-L6-v2')
    mock_sbert_model.encode.assert_any_call(sample_segments1, convert_to_tensor=True)
    mock_sbert_model.encode.assert_any_call(sample_segments2, convert_to_tensor=True)
    mock_util_in_script.cos_sim.assert_called_once()

    assert len(results) == 1
    result = results[0]
    assert result['segment1_index'] == 1
    assert result['segment2_index'] == 1
    assert result['score'] == 0.95
    assert result['text1'] == sample_segments1[1]
    assert result['text2'] == sample_segments2[1]
    assert result['diff'] == "- line1\n+ line2"
    mock_unified_diff.assert_called_once_with(sample_segments1[1].split(), sample_segments2[1].split(), lineterm='')


@patch('scripts.bill_similarity.SentenceTransformer', None)
@patch('scripts.bill_similarity.util', None)
def test_find_similar_segments_no_sbert(caplog, sample_segments1, sample_segments2):
    """Test find_similar_segments when sentence-transformers is not available."""
    with caplog.at_level(logging.WARNING):
        results = find_similar_segments(sample_segments1, sample_segments2, threshold=0.8)

    assert len(results) == 0
    assert "sentence-transformers not installed; TF-IDF fallback not implemented." in caplog.text


# --- Tests for main() function ---

@patch('argparse.ArgumentParser.parse_args')
@patch('builtins.open', new_callable=mock_open, read_data="Sample bill text content.")
@patch('scripts.bill_similarity.preprocess_text')
@patch('scripts.bill_similarity.segment_bill')
@patch('scripts.bill_similarity.find_similar_segments')
@patch('json.dump') # To check if it's called for file output
@patch('logging.info') # To check logging messages
def test_main_file_output(mock_logging_info, mock_json_dump, mock_find_similar, mock_segment, mock_preprocess, mock_file_open, mock_parse_args, tmp_path):
    """Test main function with file output."""
    output_filename = tmp_path / "output.json"
    mock_parse_args.return_value = argparse.Namespace(
        bill1="bill1.txt", bill2="bill2.txt", threshold=0.75,
        segment_size=150, overlap=30, output=str(output_filename)
    )

    mock_preprocess.side_effect = lambda x: f"processed {x}"
    mock_segment.side_effect = lambda text, size, overlap: [f"segment of {text[:10]}"]
    mock_find_similar.return_value = [{"similarity": "high"}]

    # Capture stdout to check console output (if any, though should be logging)
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        main() # Execute the main function

    # Check file reading calls
    mock_file_open.assert_any_call("bill1.txt", 'r', encoding='utf-8')
    mock_file_open.assert_any_call("bill2.txt", 'r', encoding='utf-8')

    # Check preprocessing calls
    mock_preprocess.assert_any_call("Sample bill text content.") # Called twice with same mock read_data

    # Check segmentation calls
    mock_segment.assert_any_call("processed Sample bill text content.", 150, 30)

    # Check find_similar_segments call
    mock_find_similar.assert_called_once_with(
        ["segment of processed S"], ["segment of processed S"], 0.75
    ) # Based on mock_segment output

    # Check file writing for output
    mock_file_open.assert_any_call(str(output_filename), 'w', encoding='utf-8')
    mock_json_dump.assert_called_once_with([{"similarity": "high"}], mock_file_open(), indent=2)

    # Check logging info
    mock_logging_info.assert_any_call(f"Results written to {output_filename}")


@patch('argparse.ArgumentParser.parse_args')
@patch('builtins.open', new_callable=mock_open, read_data="Sample bill text.")
@patch('scripts.bill_similarity.preprocess_text', return_value="processed text")
@patch('scripts.bill_similarity.segment_bill', return_value=["segment1", "segment2"])
@patch('scripts.bill_similarity.find_similar_segments', return_value=[{"match": "found"}])
def test_main_console_output(mock_find_similar, mock_segment_bill, mock_preprocess_text, mock_file_open, mock_parse_args):
    """Test main function with console output."""
    mock_parse_args.return_value = argparse.Namespace(
        bill1="b1.txt", bill2="b2.txt", threshold=0.8,
        segment_size=100, overlap=20, output=None # No output file
    )

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        main()
        console_output = buf.getvalue()

    expected_json_output = json.dumps([{"match": "found"}], indent=2)
    assert console_output.strip() == expected_json_output.strip()

    # Verify other calls as in the file output test if necessary
    mock_file_open.assert_any_call("b1.txt", 'r', encoding='utf-8')
    mock_preprocess_text.assert_called()
    mock_segment_bill.assert_called()
    mock_find_similar.assert_called()


if __name__ == "__main__":
    pytest.main()
