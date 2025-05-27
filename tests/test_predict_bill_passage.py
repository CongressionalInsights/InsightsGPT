import pytest
import os
import pandas as pd
import numpy as np
import joblib
from argparse import Namespace # For mocking parsed CLI arguments
from sklearn.preprocessing import StandardScaler # For dummy preprocessor
from sklearn.compose import ColumnTransformer # For dummy preprocessor

# Add project root to sys.path for module import
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts import predict_bill_passage

# --- Dummy Model and Preprocessor Components ---

class DummyModel:
    def __init__(self, model_type="logistic"):
        self.model_type = model_type
        if model_type == "logistic":
            self.coef_ = np.array([[0.1, -0.2, 0.3, 0.4]]) # Example: 4 features after OHE
            self.classes_ = np.array([0,1])
        else: # tree
            self.feature_importances_ = np.array([0.4, 0.3, 0.2, 0.1])
        self.feature_names_in_ = ['feat_0', 'feat_1', 'feat_2', 'feat_3'] # Example processed feature names

    def predict_proba(self, X):
        # Return fixed probabilities for predictability in tests
        # Shape: (n_samples, n_classes) - for binary, 2 classes
        return np.array([[0.8, 0.2], [0.3, 0.7], [0.5,0.5]])[:len(X), :]

class DummyPreprocessor:
    def __init__(self):
        # These are the *original* features the preprocessor was fitted on
        self.feature_names_in_ = ['num_cosponsors', 'bill_type', 'policy_area'] 
        # These would be the features *after* transformation (e.g., one-hot encoding)
        self._feature_names_out = ['num_cosponsors_scaled', 'bill_type_hr', 'bill_type_s', 'policy_area_Health']


    def transform(self, X_df):
        # Simulate transformation: just return a fixed array of the correct shape
        # The shape should match what DummyModel expects (e.g., 4 features)
        # For this dummy, let's assume it always outputs 4 features.
        if not isinstance(X_df, pd.DataFrame): X_df = pd.DataFrame(X_df) # Ensure it's a DataFrame
        
        # Simple transformation: select 'num_cosponsors', scale it, and create 3 dummy OHE features.
        # This is more involved than needed if just testing predict_bill_passage structure,
        # but makes it slightly more realistic.
        transformed_data = np.zeros((len(X_df), len(self._feature_names_out)))
        if 'num_cosponsors' in X_df.columns:
            transformed_data[:,0] = X_df['num_cosponsors'].fillna(0) * 0.1 # Dummy scaling
        if 'bill_type' in X_df.columns: # Dummy OHE
            transformed_data[:,1] = (X_df['bill_type'] == 'hr').astype(int)
            transformed_data[:,2] = (X_df['bill_type'] == 's').astype(int)
        if 'policy_area' in X_df.columns: # Dummy OHE
            transformed_data[:,3] = (X_df['policy_area'] == 'Health').astype(int)
        return transformed_data

    def get_feature_names_out(self, input_features=None):
        return self._feature_names_out


# --- Fixtures ---

@pytest.fixture
def temp_model_files(tmp_path):
    """Creates dummy model and preprocessor files in a temporary directory."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    # Create and save dummy logistic model
    dummy_logistic = DummyModel(model_type="logistic")
    joblib.dump(dummy_logistic, models_dir / predict_bill_passage.LOGISTIC_MODEL_FILENAME)

    # Create and save dummy tree model
    dummy_tree = DummyModel(model_type="tree")
    joblib.dump(dummy_tree, models_dir / predict_bill_passage.DECISION_TREE_MODEL_FILENAME)
    
    # Create and save dummy preprocessor
    dummy_preprocessor = DummyPreprocessor()
    joblib.dump(dummy_preprocessor, models_dir / predict_bill_passage.PREPROCESSOR_FILENAME)
    
    # Patch the MODELS_DIR in the script to use this temp directory
    original_models_dir = predict_bill_passage.MODELS_DIR
    predict_bill_passage.MODELS_DIR = str(models_dir)
    yield models_dir # Provide the path to the test
    predict_bill_passage.MODELS_DIR = original_models_dir # Restore

@pytest.fixture
def sample_input_csv_file(tmp_path):
    """Creates a sample CSV input file."""
    input_dir = tmp_path / "input_data"
    input_dir.mkdir()
    csv_path = input_dir / "sample_bills.csv"
    # Match columns expected by DummyPreprocessor.feature_names_in_
    csv_content = "num_cosponsors,bill_type,policy_area\n10,hr,Health\n5,s,Economy\n,hr,Other" # Includes a missing value
    with open(csv_path, 'w') as f:
        f.write(csv_content)
    return csv_path

# --- Tests for Core Functions ---

def test_load_model_and_preprocessor_logistic(temp_model_files):
    """Test loading logistic model and preprocessor."""
    model, preprocessor, feat_names = predict_bill_passage.load_model_and_preprocessor("logistic")
    assert model is not None
    assert preprocessor is not None
    assert hasattr(model, "coef_")
    assert feat_names == ['num_cosponsors_scaled', 'bill_type_hr', 'bill_type_s', 'policy_area_Health']


def test_load_model_and_preprocessor_tree(temp_model_files):
    """Test loading tree model and preprocessor."""
    model, preprocessor, _ = predict_bill_passage.load_model_and_preprocessor("tree")
    assert model is not None
    assert preprocessor is not None
    assert hasattr(model, "feature_importances_")

def test_load_model_files_not_found(tmp_path): # Use fresh tmp_path, not temp_model_files
    predict_bill_passage.MODELS_DIR = str(tmp_path) # Point to an empty dir
    model, preprocessor, _ = predict_bill_passage.load_model_and_preprocessor("logistic")
    assert model is None
    assert preprocessor is None


def test_prepare_input_data_from_file(sample_input_csv_file):
    """Test preparing input data from a CSV file."""
    args = Namespace(input_file=str(sample_input_csv_file))
    # Expected features for DummyPreprocessor
    expected_raw_features = DummyPreprocessor().feature_names_in_
    df = predict_bill_passage.prepare_input_data(args, expected_raw_features)
    
    assert df is not None
    assert len(df) == 3
    assert list(df.columns) == expected_raw_features # Columns should match expected raw features
    assert df['num_cosponsors'].iloc[2] is np.nan # Check NaN handling for missing CSV value

def test_prepare_input_data_from_cli_args():
    """Test preparing input data from CLI arguments."""
    args = Namespace(
        input_file=None,
        num_cosponsors=10.0, # argparse converts to float if type=float
        bill_type="hr",
        policy_area="Health",
        # Other core features would be None if not provided
        num_actions=None, num_committees=None, days_pending_latest_action=None, primary_sponsor_party=None
    )
    # Simulate that ALL_CORE_FEATURES were expected by preprocessor (some will be NaN)
    df = predict_bill_passage.prepare_input_data(args, predict_bill_passage.ALL_CORE_FEATURES)
    
    assert df is not None
    assert len(df) == 1
    assert df["num_cosponsors"].iloc[0] == 10.0
    assert df["bill_type"].iloc[0] == "hr"
    assert df["policy_area"].iloc[0] == "Health"
    assert pd.isna(df["primary_sponsor_party"].iloc[0]) # This was not provided, so should be NaN


def test_preprocess_input_data(temp_model_files): # Needs preprocessor file
    """Test preprocessing of input data."""
    _, preprocessor, _ = predict_bill_passage.load_model_and_preprocessor("logistic") # Load dummy preprocessor
    
    # Create sample DataFrame matching DummyPreprocessor.feature_names_in_
    input_df = pd.DataFrame({
        'num_cosponsors': [10, 20], 
        'bill_type': ['hr', 's'], 
        'policy_area': ['Health', 'Economy']
    })
    
    processed_data = predict_bill_passage.preprocess_input_data(input_df, preprocessor)
    assert processed_data is not None
    assert processed_data.shape == (2, 4) # DummyPreprocessor outputs 4 features

def test_make_predictions(temp_model_files): # Needs model file
    """Test making predictions."""
    model, _, _ = predict_bill_passage.load_model_and_preprocessor("logistic") # Load dummy model
    # Dummy processed data (2 samples, 4 features as expected by DummyModel)
    dummy_processed_data = np.array([[0.1, 1, 0, 1], [0.5, 0, 1, 0]]) 
    
    probabilities = predict_bill_passage.make_predictions(model, dummy_processed_data)
    assert probabilities is not None
    assert len(probabilities) == 2
    assert np.all((probabilities >= 0) & (probabilities <= 1))
    # Check fixed probabilities from DummyModel: 0.2, 0.7
    assert probabilities[0] == pytest.approx(0.2)
    assert probabilities[1] == pytest.approx(0.7)


def test_display_results_logistic(temp_model_files, capsys):
    """Test display of results for logistic regression."""
    model, _, feature_names = predict_bill_passage.load_model_and_preprocessor("logistic")
    probabilities = np.array([0.756, 0.321])
    input_df = pd.DataFrame({'bill_id': ['HR1', 'S2']}) # Dummy df for indexing

    predict_bill_passage.display_results(probabilities, input_df, "logistic", model, feature_names)
    
    captured = capsys.readouterr()
    assert "Passage Likelihood Score: 75.60%" in captured.out
    assert "Passage Likelihood Score: 32.10%" in captured.out
    assert "Model Type: Logistic Regression" in captured.out
    assert "Feature Influence (Coefficients):" in captured.out
    # Check if top features are mentioned (based on DummyModel coefs and DummyPreprocessor feature_names_out)
    # DummyModel coefs: [[0.1, -0.2, 0.3, 0.4]]
    # DummyPreprocessor feature_names_out: ['num_cosponsors_scaled', 'bill_type_hr', 'bill_type_s', 'policy_area_Health']
    # Expected order by abs_coeff: policy_area_Health (0.4), bill_type_s (0.3), bill_type_hr (-0.2), num_cosponsors_scaled (0.1)
    assert "policy_area_Health: 0.4000" in captured.out # Top one
    assert "bill_type_s: 0.3000" in captured.out


def test_display_results_tree(temp_model_files, capsys):
    """Test display of results for decision tree."""
    model, _, feature_names = predict_bill_passage.load_model_and_preprocessor("tree")
    probabilities = np.array([0.60])
    input_df = pd.DataFrame({'bill_id': ['HR3']})

    predict_bill_passage.display_results(probabilities, input_df, "tree", model, feature_names)
    
    captured = capsys.readouterr()
    assert "Passage Likelihood Score: 60.00%" in captured.out
    assert "Model Type: Decision Tree" in captured.out
    assert "Feature Importance:" in captured.out
    # DummyModel tree importances: [0.4, 0.3, 0.2, 0.1]
    # DummyPreprocessor feature_names_out: ['num_cosponsors_scaled', 'bill_type_hr', 'bill_type_s', 'policy_area_Health']
    # Expected order: num_cosponsors_scaled (0.4), bill_type_hr (0.3), bill_type_s (0.2), policy_area_Health (0.1)
    assert "num_cosponsors_scaled: 0.4000" in captured.out # Top one
    assert "bill_type_hr: 0.3000" in captured.out


# --- Test Main Orchestration (CLI argument parsing and flow) ---

def test_main_with_file_input(temp_model_files, sample_input_csv_file, mocker, capsys):
    """Test main function flow with file input."""
    # Mock argparse to simulate command line arguments
    mock_args = Namespace(
        model_type="logistic", 
        input_file=str(sample_input_csv_file),
        # CLI feature args would be None
        num_cosponsors=None, bill_type=None, policy_area=None, num_actions=None, 
        num_committees=None, days_pending_latest_action=None, primary_sponsor_party=None
    )
    mocker.patch("argparse.ArgumentParser.parse_args", return_value=mock_args)
    
    predict_bill_passage.main()
    
    captured = capsys.readouterr()
    assert "--- Bill Passage Prediction Utility (Model: Logistic) ---" in captured.out
    assert "Loaded input data from file:" in captured.out
    assert "Predictions made successfully." in captured.out
    # Based on DummyModel and DummyPreprocessor, for 3 input rows from sample_input_csv_file:
    # predict_proba returns [[0.8, 0.2], [0.3, 0.7], [0.5,0.5]]
    # So likelihoods are 0.2, 0.7, 0.5
    assert "Passage Likelihood Score: 20.00%" in captured.out # First bill
    assert "Passage Likelihood Score: 70.00%" in captured.out # Second bill
    assert "Passage Likelihood Score: 50.00%" in captured.out # Third bill


def test_main_with_cli_input(temp_model_files, mocker, capsys):
    """Test main function flow with CLI input for a single bill."""
    mock_args = Namespace(
        model_type="tree", 
        input_file=None,
        num_cosponsors=20.0, 
        bill_type="s", 
        policy_area="Economy", # Matches one of the dummy preprocessor's OHE features
        num_actions=5.0, 
        num_committees=1.0, 
        days_pending_latest_action=100.0, 
        primary_sponsor_party="R"
    )
    mocker.patch("argparse.ArgumentParser.parse_args", return_value=mock_args)
    
    predict_bill_passage.main()
    
    captured = capsys.readouterr()
    assert "--- Bill Passage Prediction Utility (Model: Tree) ---" in captured.out
    assert "Prepared input data from command-line arguments" in captured.out
    assert "Passage Likelihood Score: 20.00%" in captured.out # Only one bill, first proba from dummy model is 0.2
    assert "Feature Importance:" in captured.out

def test_main_no_input_error(mocker, capsys):
    """Test main function error when no input is provided."""
    # Mock argparse to simulate no input arguments (all features also None)
    mock_args = Namespace(
        model_type="logistic", input_file=None,
        num_cosponsors=None, bill_type=None, policy_area=None, num_actions=None, 
        num_committees=None, days_pending_latest_action=None, primary_sponsor_party=None
    )
    # Need to mock the ArgumentParser instance itself to control `error` method
    mock_parser_instance = mocker.MagicMock()
    mock_parser_instance.parse_args.return_value = mock_args
    # Simulate parser.error being called
    mock_parser_instance.error = mocker.MagicMock(side_effect=SystemExit) # parser.error usually exits

    mocker.patch("argparse.ArgumentParser", return_value=mock_parser_instance)

    with pytest.raises(SystemExit): # Expect SystemExit because parser.error is called
        predict_bill_passage.main()
    
    mock_parser_instance.error.assert_called_once_with(
        "No input provided. Please specify an input file with -i or provide feature values for a single bill via command-line options."
    )
