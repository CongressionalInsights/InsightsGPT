import pytest
import os
import json
from unittest.mock import patch, MagicMock, call
import sys
import io
import contextlib
import numpy as np

# Add scripts directory to sys.path to allow importing bill_similarity
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    from bill_similarity import (
        load_bills,
        preprocess_text,
        segment_bill,
        get_sbert_model,
        generate_embeddings,
        SBERT_MODEL_NAME,
        calculate_similarity_scores,
        find_similar_segments,
        report_similarities
    )
except ImportError as e:
    print(f"Error importing from bill_similarity: {e}")
    print(f"sys.path: {sys.path}")
    pytest.fail(f"Failed to import bill_similarity: {e}")

@pytest.fixture(autouse=True)
def reset_sbert_model_cache():
    try:
        import bill_similarity
        bill_similarity._sbert_model = None
    except NameError:
        pass
    yield
    try:
        import bill_similarity
        bill_similarity._sbert_model = None
    except NameError:
        pass

@pytest.fixture
def dummy_bill_content():
    return "This is a dummy bill. It has several sentences for testing purposes."

@pytest.fixture
def temp_file(tmp_path, dummy_bill_content):
    p = tmp_path / "dummy_bill.txt"
    p.write_text(dummy_bill_content)
    return str(p)

@pytest.fixture
def sample_segments_data():
    return ["This is segment one.", "Segment two is here.", "And the third segment."]

@pytest.fixture
def sample_embeddings_set1_np(): # Keep as numpy for direct use in cosine_similarity
    return np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.707, 0.707, 0.0]])

@pytest.fixture
def sample_embeddings_set1_list(sample_embeddings_set1_np): # For function inputs
    return sample_embeddings_set1_np.tolist()


@pytest.fixture
def sample_embeddings_set2_np():
    return np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.5, 0.5, 0.5]])

@pytest.fixture
def sample_embeddings_set2_list(sample_embeddings_set2_np):
    return sample_embeddings_set2_np.tolist()


# --- Test Functions ---

def test_load_bills_from_file(temp_file, dummy_bill_content):
    """Test loading bill content from a file."""
    loaded_content = load_bills([temp_file])
    assert len(loaded_content) == 1
    assert loaded_content[0] == dummy_bill_content

def test_load_bills_direct_text(dummy_bill_content):
    """Test loading bill content directly as text."""
    direct_text = "This is a direct bill text."
    loaded_content = load_bills([direct_text])
    assert len(loaded_content) == 1
    assert loaded_content[0] == direct_text

def test_load_bills_file_not_found():
    """Test FileNotFoundError handling in load_bills."""
    # No pytest.raises here, function prints warning and skips
    # We can capture stdout to check for the warning if necessary
    non_existent_file = "non_existent_file.txt"
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        loaded_content = load_bills([non_existent_file])
        output = buf.getvalue()
    assert len(loaded_content) == 0
    assert f"Warning: File not found at {non_existent_file}" in output

def test_load_bills_mixed_sources(temp_file, dummy_bill_content):
    """Test loading from a mix of file and direct text."""
    direct_text = "Another bill as direct text."
    sources = [temp_file, direct_text]
    loaded_content = load_bills(sources)
    assert len(loaded_content) == 2
    assert loaded_content[0] == dummy_bill_content
    assert loaded_content[1] == direct_text


def test_preprocess_text():
    """Test text preprocessing for whitespace."""
    text_with_issues = "   This  is   a test.  "
    expected_text = "This is a test."
    assert preprocess_text(text_with_issues) == expected_text
    assert preprocess_text("Clean text.") == "Clean text."
    assert preprocess_text("") == ""


def test_segment_bill_basic():
    """Test basic bill segmentation."""
    text = "one two three four five six seven eight nine ten"
    segments = segment_bill(text, segment_size=5, overlap=2)
    assert len(segments) == 3
    assert segments[0] == "one two three four five"
    assert segments[1] == "four five six seven eight" # overlap of 'four five' (2 words)
    assert segments[2] == "seven eight nine ten" # remaining words

def test_segment_bill_shorter_than_segment_size():
    """Test segmentation when text is shorter than segment size."""
    text = "one two three"
    segments = segment_bill(text, segment_size=5, overlap=1)
    assert len(segments) == 1
    assert segments[0] == "one two three"

def test_segment_bill_no_overlap():
    """Test segmentation with no overlap."""
    text = "one two three four five six"
    segments = segment_bill(text, segment_size=3, overlap=0)
    assert len(segments) == 2
    assert segments[0] == "one two three"
    assert segments[1] == "four five six"

def test_segment_bill_empty_text():
    """Test segmentation with empty text."""
    text = ""
    segments = segment_bill(text, segment_size=5, overlap=1)
    assert len(segments) == 0

def test_segment_bill_exact_multiple():
    """Test segmentation when text length is an exact multiple of segment_size - overlap."""
    text = "word1 word2 word3 word4 word5 word6 word7 word8 word9" # 9 words
    # (size - overlap) = 3. 9/3 = 3 segments.
    segments = segment_bill(text, segment_size=5, overlap=2) 
    assert len(segments) == 3
    assert segments[0] == "word1 word2 word3 word4 word5"
    assert segments[1] == "word4 word5 word6 word7 word8"
    assert segments[2] == "word7 word8 word9"


@patch('scripts.bill_similarity.SentenceTransformer')
def test_get_sbert_model_loads_and_caches(MockSentenceTransformer):
    """Test SBERT model loading and caching."""
    mock_model_instance = MagicMock()
    MockSentenceTransformer.return_value = mock_model_instance

    # First call: should load the model
    model1 = get_sbert_model()
    MockSentenceTransformer.assert_called_once_with(SBERT_MODEL_NAME)
    assert model1 == mock_model_instance

    # Second call: should return cached model, not call constructor again
    model2 = get_sbert_model()
    MockSentenceTransformer.assert_called_once_with(SBERT_MODEL_NAME) # Still called only once
    assert model2 == mock_model_instance
    assert model2 == model1 # Ensure it's the same instance

@patch('scripts.bill_similarity.SentenceTransformer')
def test_get_sbert_model_load_failure(MockSentenceTransformer):
    """Test SBERT model loading failure."""
    MockSentenceTransformer.side_effect = Exception("Failed to load")
    with pytest.raises(RuntimeError, match="Failed to load SBERT model: Failed to load"):
        get_sbert_model()


@patch('scripts.bill_similarity.get_sbert_model') # Mock get_sbert_model to control the model instance
def test_generate_embeddings(mock_get_sbert_model, sample_segments_data):
    """Test embedding generation."""
    mock_model_instance = MagicMock()
    mock_get_sbert_model.return_value = mock_model_instance
    
    dummy_embeddings_np = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
    dummy_embeddings_list = dummy_embeddings_np.tolist()
    mock_model_instance.encode.return_value = dummy_embeddings_np

    embeddings = generate_embeddings(sample_segments_data)

    mock_get_sbert_model.assert_called_once() # Ensure model loader was called
    mock_model_instance.encode.assert_called_once_with(sample_segments_data, show_progress_bar=True)
    assert embeddings == dummy_embeddings_list

def test_generate_embeddings_empty_input():
    """Test generate_embeddings with empty input list."""
    assert generate_embeddings([]) == []

@patch('scripts.bill_similarity.get_sbert_model')
def test_generate_embeddings_model_load_failure(mock_get_sbert_model):
    """Test generate_embeddings when SBERT model fails to load."""
    mock_get_sbert_model.side_effect = RuntimeError("Model loading failed")
    # Capture stdout to check for the error message from generate_embeddings
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        result = generate_embeddings(["test segment"])
        output = buf.getvalue()
    
    assert result == [] # Should return empty list on failure
    assert "Error obtaining SBERT model for embedding generation: Model loading failed" in output


def test_calculate_similarity_scores_intra_list(sample_embeddings_set1_list, sample_embeddings_set1_np):
    """Test intra-list similarity calculation."""
    # Expected: (0,1), (0,2), (1,2)
    # cos(e0,e1) = 0, cos(e0,e2) = 0.707, cos(e1,e2) = 0.707
    scores = calculate_similarity_scores(sample_embeddings_set1_list)
    
    # Convert to dict for easier lookup, ignoring order of pairs
    scores_dict = {(min(s[0], s[1]), max(s[0], s[1])): s[2] for s in scores}

    assert len(scores) == 3 # 3 unique pairs for 3 items
    np.testing.assert_almost_equal(scores_dict[(0,1)], np.dot(sample_embeddings_set1_np[0], sample_embeddings_set1_np[1]))
    np.testing.assert_almost_equal(scores_dict[(0,2)], np.dot(sample_embeddings_set1_np[0], sample_embeddings_set1_np[2]))
    np.testing.assert_almost_equal(scores_dict[(1,2)], np.dot(sample_embeddings_set1_np[1], sample_embeddings_set1_np[2]))


def test_calculate_similarity_scores_inter_list(sample_embeddings_set1_list, sample_embeddings_set2_list, sample_embeddings_set1_np, sample_embeddings_set2_np):
    """Test inter-list similarity calculation."""
    scores = calculate_similarity_scores(sample_embeddings_set1_list, sample_embeddings_set2_list)
    assert len(scores) == 9 # 3x3 pairs

    # Check a few specific scores
    # (e1_0, e2_0) should be 1.0
    # (e1_1, e2_1) should be 0.0
    score_map = {(s[0], s[1]): s[2] for s in scores}
    np.testing.assert_almost_equal(score_map[(0,0)], np.dot(sample_embeddings_set1_np[0], sample_embeddings_set2_np[0])) # (1,0,0) . (1,0,0) = 1
    np.testing.assert_almost_equal(score_map[(1,1)], np.dot(sample_embeddings_set1_np[1], sample_embeddings_set2_np[1])) # (0,1,0) . (0,0,1) = 0
    np.testing.assert_almost_equal(score_map[(2,2)], np.dot(sample_embeddings_set1_np[2], sample_embeddings_set2_np[2])) # (0.707,0.707,0) . (0.5,0.5,0.5) = 0.707


def test_calculate_similarity_scores_empty():
    assert calculate_similarity_scores([]) == []
    assert calculate_similarity_scores([[]]) == [] #Technically valid if inner list is an embedding
    assert calculate_similarity_scores([], [[]]) == []
    assert calculate_similarity_scores([[]], []) == []


def test_find_similar_segments_intra_bill(sample_segments_data, sample_embeddings_set1_list):
    """Test finding similar segments within a single bill."""
    # e0 vs e2 score is 0.707, e1 vs e2 score is 0.707
    # e0 vs e1 is 0.0
    similar_pairs = find_similar_segments(
        bill_id1="bill1",
        segments1=sample_segments_data,
        embeddings1=sample_embeddings_set1_list,
        similarity_threshold=0.7
    )
    assert len(similar_pairs) == 2
    # Check one pair (order might vary, so check for presence or sort)
    found_0_2 = any(p['segment1_index'] == 0 and p['segment2_index'] == 2 for p in similar_pairs) or \
                any(p['segment1_index'] == 2 and p['segment2_index'] == 0 for p in similar_pairs)
    found_1_2 = any(p['segment1_index'] == 1 and p['segment2_index'] == 2 for p in similar_pairs) or \
                any(p['segment1_index'] == 2 and p['segment2_index'] == 1 for p in similar_pairs)
    assert found_0_2
    assert found_1_2
    for pair in similar_pairs:
        assert pair['similarity_score'] >= 0.7
        assert pair['bill1_id'] == "bill1"
        assert pair['bill2_id'] == "bill1" # Intra-bill comparison

def test_find_similar_segments_inter_bill(sample_segments_data, sample_embeddings_set1_list, sample_embeddings_set2_list):
    """Test finding similar segments between two bills."""
    # e1_0 vs e2_0 score is 1.0
    # e1_2 vs e2_2 score is 0.707
    similar_pairs = find_similar_segments(
        bill_id1="billA",
        segments1=sample_segments_data,
        embeddings1=sample_embeddings_set1_list,
        bill_id2="billB",
        segments2=sample_segments_data, # Using same segments for simplicity, different embeddings matter
        embeddings2=sample_embeddings_set2_list,
        similarity_threshold=0.7
    )
    assert len(similar_pairs) == 2
    
    pair_scores = sorted([p['similarity_score'] for p in similar_pairs], reverse=True)
    np.testing.assert_almost_equal(pair_scores[0], 1.0) # (e1_0, e2_0)
    np.testing.assert_almost_equal(pair_scores[1], 0.707, decimal=3) # (e1_2, e2_2)

    for pair in similar_pairs:
        assert pair['bill1_id'] == "billA"
        assert pair['bill2_id'] == "billB"

def test_find_similar_segments_no_similarity(sample_segments_data, sample_embeddings_set1_list):
    """Test find_similar_segments when no segments meet the threshold."""
    similar_pairs = find_similar_segments(
        bill_id1="bill1",
        segments1=sample_segments_data,
        embeddings1=sample_embeddings_set1_list,
        similarity_threshold=0.99 # High threshold
    )
    assert len(similar_pairs) == 0


def test_report_similarities_console_output(capsys):
    """Test reporting similarities to console."""
    similarities_data = [{
        'bill1_id': 'A', 'segment1_index': 0, 'segment1_text': 'Text A1',
        'bill2_id': 'B', 'segment2_index': 1, 'segment2_text': 'Text B2',
        'similarity_score': 0.85678
    }]
    report_similarities(similarities_data)
    captured = capsys.readouterr()
    assert "Found potential similarity:" in captured.out
    assert "Bill 1 ID: A, Segment Index: 0" in captured.out
    assert "Segment 1 Text: Text A1" in captured.out
    assert "Bill 2 ID: B, Segment Index: 1" in captured.out
    assert "Segment 2 Text: Text B2" in captured.out
    assert "Similarity Score: 0.8568" in captured.out # Check formatting

def test_report_similarities_console_output_no_similarities(capsys):
    """Test console output when no similarities are found."""
    report_similarities([])
    captured = capsys.readouterr()
    assert "No similarities to report." in captured.out

def test_report_similarities_file_output(tmp_path):
    """Test reporting similarities to a JSON file."""
    similarities_data = [{
        'bill1_id': 'C', 'segment1_index': 2, 'segment1_text': 'Text C3',
        'bill2_id': 'D', 'segment2_index': 3, 'segment2_text': 'Text D4',
        'similarity_score': 0.92345
    }]
    output_file_path = tmp_path / "report.json"
    
    # Capture stdout to check the confirmation message
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        report_similarities(similarities_data, output_file=str(output_file_path))
        output_confirmation = buf.getvalue()

    assert f"Similarity report saved to {output_file_path}" in output_confirmation
    assert output_file_path.exists()
    
    with open(output_file_path, 'r') as f:
        loaded_data = json.load(f)
    assert loaded_data == similarities_data

def test_report_similarities_file_output_no_similarities(tmp_path, capsys):
    """Test file output when no similarities are found (should not create file)."""
    output_file_path = tmp_path / "empty_report.json"
    report_similarities([], output_file=str(output_file_path))
    
    # The function prints "No similarities to report." to console.
    captured = capsys.readouterr()
    assert "No similarities to report." in captured.out
    assert not output_file_path.exists() # File should not be created for empty list.

@patch('builtins.open', side_effect=IOError("Disk full"))
def test_report_similarities_file_io_error(mock_open, capsys):
    """Test IOError handling when writing to file."""
    similarities_data = [{"test": "data"}]
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        report_similarities(similarities_data, output_file="dummy_path.json")
        output = buf.getvalue()

    assert "Error saving report to dummy_path.json: Disk full" in output

# --- Main execution for running tests (optional, pytest handles this) ---
if __name__ == "__main__":
    # This allows running the tests with `python test_bill_similarity.py`
    # but it's better to use `pytest` command in the terminal.
    pytest.main()
