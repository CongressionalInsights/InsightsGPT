import pytest
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

# Add project root to sys.path for module import
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models import train_bill_forecasting_model # Assuming the script is in models/

# --- Sample Data ---
SAMPLE_INTEGRATED_DATA_CSV_CONTENT = """bill_id,title,latest_action_text,num_cosponsors,num_actions,num_committees,days_pending_latest_action,bill_type,primary_sponsor_party,policy_area,media_topic_score,lobby_topic_filings
117-HR-1,Bill A,Passed House and Senate,10,5,2,30,hr,D,Economy,0.5,10
117-S-2,Bill B,Introduced,5,2,1,10,s,R,Health,-0.2,5
117-HR-3,Bill C,Became Public Law,20,10,3,60,hr,D,Science,0.8,15
116-S-10,Bill D,Referred to committee,2,1,1,5,s,I,Technology,0.1,2
116-HR-20,Bill E,Passed House,8,4,2,25,hr,R,Education,NaN,NaN 
"""
# Added NaN for signal columns to test imputation for those too.

# --- Fixtures ---

@pytest.fixture
def temp_datasets_dir(tmp_path):
    """Creates a temporary datasets directory with sample integrated data."""
    ds_dir = tmp_path / "datasets"
    ds_dir.mkdir()
    with open(ds_dir / "integrated_bill_data_with_signals.csv", 'w') as f:
        f.write(SAMPLE_INTEGRATED_DATA_CSV_CONTENT)
    return ds_dir

@pytest.fixture
def temp_models_dir(tmp_path):
    """Creates a temporary models directory."""
    m_dir = tmp_path / "models"
    m_dir.mkdir()
    return m_dir

# --- Tests for Core Functions ---

def test_load_data(temp_datasets_dir):
    """Test loading data from CSV."""
    filepath = temp_datasets_dir / "integrated_bill_data_with_signals.csv"
    # Patch the DATASET_PATH in the module to use our temp file
    train_bill_forecasting_model.DATASET_PATH = str(filepath)
    
    df = train_bill_forecasting_model.load_data(str(filepath))
    assert df is not None
    assert len(df) == 5
    assert "num_cosponsors" in df.columns

def test_load_data_file_not_found(capsys):
    train_bill_forecasting_model.DATASET_PATH = "non_existent_file.csv"
    df = train_bill_forecasting_model.load_data("non_existent_file.csv")
    assert df is None
    captured = capsys.readouterr()
    assert "Error: Dataset not found" in captured.out

def test_create_target_variable():
    """Test creation of the 'is_passed' target variable."""
    data = {
        "latest_action_text": [
            "Introduced in House", "Passed House", "Became Public Law", 
            "Signed by President; Became Public Law", "Failed to pass Senate"
        ]
    }
    df = pd.DataFrame(data)
    df = train_bill_forecasting_model.create_target_variable(df)
    
    assert "is_passed" in df.columns
    expected_is_passed = [0, 1, 1, 1, 0]
    assert df["is_passed"].tolist() == expected_is_passed
    # Test with missing latest_action_text (should create dummy and warn)
    df_missing = pd.DataFrame({"some_other_col": [1,2]})
    df_missing = train_bill_forecasting_model.create_target_variable(df_missing.copy()) # Use .copy() to avoid modifying original for other tests
    assert df_missing["is_passed"].tolist() == [0,0]


def test_preprocess_features(temp_datasets_dir):
    """Test feature preprocessing pipeline."""
    filepath = temp_datasets_dir / "integrated_bill_data_with_signals.csv"
    df = pd.read_csv(filepath)
    df = train_bill_forecasting_model.create_target_variable(df) # Need 'is_passed'

    # Manually define which signal columns from sample data are numeric for the test
    # In the actual script, this is done by checking dtype.
    # Our sample data has 'media_topic_score', 'lobby_topic_filings' as numeric.
    
    # We need to ensure the `preprocess_features` function inside the module
    # correctly identifies these. The test will rely on the script's internal logic for this.

    X_processed_df, y, preprocessor = train_bill_forecasting_model.preprocess_features(df.copy()) # Pass a copy
    
    assert not X_processed_df.empty
    assert y is not None
    assert preprocessor is not None
    assert len(X_processed_df) == len(y)
    
    # Check if known features were processed
    # Original numeric: num_cosponsors, num_actions, num_committees, days_pending_latest_action, media_topic_score, lobby_topic_filings
    # Original categorical: bill_type (hr, s), primary_sponsor_party (D, R, I), policy_area (Economy, Health, Science, Technology, Education)
    # Expected columns after one-hot encoding:
    # num_cosponsors, num_actions, num_committees, days_pending_latest_action, media_topic_score, lobby_topic_filings (6 numeric)
    # bill_type_hr, bill_type_s (2 from bill_type)
    # primary_sponsor_party_D, primary_sponsor_party_I, primary_sponsor_party_R (3 from party)
    # policy_area_Economy, policy_area_Education, policy_area_Health, policy_area_Science, policy_area_Technology (5 from policy_area)
    # Total = 6 + 2 + 3 + 5 = 16 columns
    
    # Let's verify the column names based on get_feature_names_out
    feature_names = X_processed_df.columns.tolist()
    assert len(feature_names) == 16 # Based on sample data
    
    # Check for one of each type of original column in the transformed names
    assert any("num_cosponsors" in col for col in feature_names)
    assert any("bill_type_hr" in col for col in feature_names)
    assert any("primary_sponsor_party_D" in col for col in feature_names)
    assert any("policy_area_Economy" in col for col in feature_names)
    assert any("media_topic_score" in col for col in feature_names) # check signal column

    # Check that scaling and one-hot encoding happened (e.g. mean of scaled numeric should be ~0)
    # And one-hot encoded columns should be binary.
    numeric_cols_processed = [col for col in feature_names if not any(cat_prefix in col for cat_prefix in ["bill_type_", "primary_sponsor_party_", "policy_area_"])]
    if numeric_cols_processed: # Check only if numeric columns are present
         assert np.allclose(X_processed_df[numeric_cols_processed].mean(axis=0), 0, atol=1e-5) # atol for float precision

    ohe_cols_processed = [col for col in feature_names if any(cat_prefix in col for cat_prefix in ["bill_type_", "primary_sponsor_party_", "policy_area_"])]
    if ohe_cols_processed: # Check only if OHE columns are present
        assert X_processed_df[ohe_cols_processed].isin([0, 1]).all().all()


def test_split_data(temp_datasets_dir):
    """Test data splitting into train and test sets."""
    # Create a dummy X and y for testing split
    X = pd.DataFrame(np.random.rand(100, 5), columns=[f"feat_{i}" for i in range(5)])
    y = pd.Series(np.random.randint(0, 2, 100))
    
    X_train, X_test, y_train, y_test = train_bill_forecasting_model.split_data(X, y, test_size=0.25)
    
    assert len(X_train) == 75
    assert len(X_test) == 25
    assert len(y_train) == 75
    assert len(y_test) == 25

def test_train_models(temp_datasets_dir):
    """Test model training process (models are created)."""
    # Create dummy processed X_train and y_train
    X_train = pd.DataFrame(np.random.rand(80, 16)) # 16 features as per previous test
    y_train = pd.Series(np.random.randint(0, 2, 80))
    
    logistic_model, decision_tree_model = train_bill_forecasting_model.train_models(X_train, y_train)
    
    assert logistic_model is not None
    assert isinstance(logistic_model, LogisticRegression)
    assert hasattr(logistic_model, "coef_") # Check if fitted
    
    assert decision_tree_model is not None
    assert isinstance(decision_tree_model, DecisionTreeClassifier)
    assert hasattr(decision_tree_model, "feature_importances_") # Check if fitted

def test_evaluate_models(capsys):
    """Test model evaluation metrics display (not the values themselves deeply)."""
    # Create a dummy model and test data
    class DummyModel:
        def predict(self, X): return np.array([0, 1, 0, 1])
        def predict_proba(self, X): return np.array([[0.9, 0.1], [0.2, 0.8], [0.7, 0.3], [0.4, 0.6]])

    model = DummyModel()
    X_test = pd.DataFrame(np.random.rand(4, 2))
    y_test = pd.Series([0, 1, 1, 0]) # Some mismatch for non-perfect scores
    
    metrics = train_bill_forecasting_model.evaluate_models(model, X_test, y_test, "Dummy Model")
    
    captured = capsys.readouterr()
    assert "Evaluating Dummy Model:" in captured.out
    assert "Accuracy:" in captured.out
    assert "ROC AUC:" in captured.out
    assert metrics["accuracy"] == 0.5 # (0,0) (1,1) correct, (0,1) (1,0) incorrect

def test_get_logistic_regression_coef_cis(mocker):
    """Test display of logistic regression coefficients (and CI limitations message)."""
    # Mock a logistic regression model
    mock_lr_model = MagicMock(spec=LogisticRegression)
    mock_lr_model.coef_ = np.array([[0.1, -0.2, 0.3]])
    
    # Create dummy X_train_df with feature names
    X_train_df = pd.DataFrame(columns=["feature_A", "feature_B", "feature_C"])
    
    # Capture print output
    mock_print = mocker.patch("builtins.print")
    
    train_bill_forecasting_model.get_logistic_regression_coef_cis(mock_lr_model, X_train_df)
    
    # Check that coefficients are printed and the note about statsmodels is there
    # This is a bit fragile if print statements change, better to check specific parts of output.
    # For example, check if "Note: Confidence Intervals" was printed.
    
    # Check if specific print calls were made (example)
    # Find a call that contains the note about statsmodels
    statsmodels_note_printed = any("statsmodels" in call_args[0] for call_args, _ in mock_print.call_args_list if call_args)
    assert statsmodels_note_printed
    
    # Check if coefficients were part of the print
    coef_printed = any("feature_A" in str(call_args[0]) and "0.1" in str(call_args[0]) for call_args, _ in mock_print.call_args_list if call_args)
    assert coef_printed


def test_save_and_load_model_and_preprocessor(temp_models_dir):
    """Test saving and then loading a model and preprocessor."""
    # Create dummy model and preprocessor
    dummy_model = LogisticRegression().fit(np.array([[0,1],[1,0]]), np.array([0,1]))
    dummy_preprocessor = ColumnTransformer(transformers=[('num', StandardScaler(), [0])]).fit(np.array([[0],[1]]))
    
    # Patch MODELS_DIR in the module
    train_bill_forecasting_model.MODELS_DIR = str(temp_models_dir)
    model_filename = "test_model.joblib"
    preprocessor_filename = "test_preprocessor.joblib"

    train_bill_forecasting_model.save_model_and_preprocessor(dummy_model, dummy_preprocessor, model_filename, preprocessor_filename)
    
    model_path = temp_models_dir / model_filename
    preprocessor_path = temp_models_dir / preprocessor_filename
    
    assert model_path.exists()
    assert preprocessor_path.exists()
    
    # Try loading them back
    loaded_model = joblib.load(model_path)
    loaded_preprocessor = joblib.load(preprocessor_path)
    
    assert loaded_model is not None
    assert loaded_preprocessor is not None
    assert hasattr(loaded_model, "predict_proba")
    assert hasattr(loaded_preprocessor, "transform")

# --- Test Main Orchestration ---
def test_main_function_full_run(temp_datasets_dir, temp_models_dir, mocker):
    """Test the main function for a full execution run (no errors)."""
    
    # Patch paths and external calls that are not core to this test's logic
    mocker.patch("models.train_bill_forecasting_model.DATASET_PATH", str(temp_datasets_dir / "integrated_bill_data_with_signals.csv"))
    mocker.patch("models.train_bill_forecasting_model.MODELS_DIR", str(temp_models_dir))
    
    # Mock the coefficient CI display function as its output is verbose and tested separately
    mocker.patch("models.train_bill_forecasting_model.get_logistic_regression_coef_cis")

    train_bill_forecasting_model.main() # Execute the main script logic
    
    # Check if output files (models, preprocessor) were created
    assert (temp_models_dir / train_bill_forecasting_model.LOGISTIC_MODEL_NAME).exists()
    assert (temp_models_dir / train_bill_forecasting_model.DECISION_TREE_MODEL_NAME).exists()
    assert (temp_models_dir / train_bill_forecasting_model.PREPROCESSOR_NAME).exists()


def test_main_function_target_var_one_class(temp_datasets_dir, mocker, capsys):
    """Test main when target variable has only one class."""
    # Create data where all 'latest_action_text' result in the same class for 'is_passed'
    single_class_csv_content = """bill_id,title,latest_action_text,num_cosponsors,num_actions,num_committees,days_pending_latest_action,bill_type,primary_sponsor_party,policy_area
117-HR-1,Bill A,Introduced,10,5,2,30,hr,D,Economy
117-S-2,Bill B,Referred,5,2,1,10,s,R,Health
    """
    single_class_csv_path = temp_datasets_dir / "single_class_data.csv"
    with open(single_class_csv_path, 'w') as f:
        f.write(single_class_csv_content)

    mocker.patch("models.train_bill_forecasting_model.DATASET_PATH", str(single_class_csv_path))
    mocker.patch("models.train_bill_forecasting_model.MODELS_DIR", str(temp_datasets_dir)) # Use any temp dir for models

    train_bill_forecasting_model.main()

    captured = capsys.readouterr()
    assert "Target variable 'is_passed' is missing or has only one class. Cannot proceed" in captured.out
