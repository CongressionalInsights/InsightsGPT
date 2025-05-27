import os
import argparse
import pandas as pd
import numpy as np
import joblib

# --- Configuration ---
MODELS_DIR = os.path.join("..", "models") # Adjusted path to be relative to 'scripts/'
LOGISTIC_MODEL_FILENAME = "bill_passage_logistic_model.joblib"
DECISION_TREE_MODEL_FILENAME = "bill_passage_decision_tree_model.joblib"
PREPROCESSOR_FILENAME = "bill_passage_preprocessor.joblib"

# Define the core features expected by the preprocessor (must match training script)
# These are the features a user might input via CLI for a single prediction.
# Signal features (media_*, lobby_*) are typically too numerous for CLI and expected from file input.
CORE_NUMERIC_FEATURES = ['num_cosponsors', 'num_actions', 'num_committees', 'days_pending_latest_action']
CORE_CATEGORICAL_FEATURES = ['bill_type', 'primary_sponsor_party', 'policy_area']
ALL_CORE_FEATURES = CORE_NUMERIC_FEATURES + CORE_CATEGORICAL_FEATURES

# --- Load Model and Preprocessor ---
def load_model_and_preprocessor(model_type: str) -> tuple[any, any, list | None]:
    """Loads the specified model and the shared preprocessor."""
    model_filename = LOGISTIC_MODEL_FILENAME if model_type.lower() == "logistic" else DECISION_TREE_MODEL_FILENAME
    model_path = os.path.join(MODELS_DIR, model_filename)
    preprocessor_path = os.path.join(MODELS_DIR, PREPROCESSOR_FILENAME)

    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        return None, None, None
    if not os.path.exists(preprocessor_path):
        print(f"Error: Preprocessor file not found at {preprocessor_path}")
        return None, None, None

    try:
        model = joblib.load(model_path)
        print(f"Loaded model from {model_path}")
        preprocessor = joblib.load(preprocessor_path)
        print(f"Loaded preprocessor from {preprocessor_path}")
        
        # Try to get feature names from the preprocessor
        feature_names_out = None
        if hasattr(preprocessor, 'get_feature_names_out'):
            try:
                feature_names_out = preprocessor.get_feature_names_out()
            except Exception as e:
                print(f"Could not get feature names from preprocessor: {e}. Will try to use model's feature names if available.")
        
        if feature_names_out is None and hasattr(model, 'feature_names_in_'): # Fallback for some models
             feature_names_out = model.feature_names_in_


        return model, preprocessor, feature_names_out
    except Exception as e:
        print(f"Error loading model or preprocessor: {e}")
        return None, None, None

# --- Prepare Input Data ---
def prepare_input_data(args, all_expected_features: list) -> pd.DataFrame | None:
    """Prepares input data from file or CLI arguments into a DataFrame."""
    if args.input_file:
        try:
            if args.input_file.endswith(".csv"):
                input_df = pd.read_csv(args.input_file)
            elif args.input_file.endswith(".json"):
                input_df = pd.read_json(args.input_file, orient='records') # Assumes records orientation
            else:
                print("Error: Unsupported file type. Please use CSV or JSON.")
                return None
            print(f"Loaded input data from file: {args.input_file}. Shape: {input_df.shape}")
        except Exception as e:
            print(f"Error loading input file {args.input_file}: {e}")
            return None
    else:
        # Create DataFrame from CLI args for a single bill
        cli_data = {}
        for feature in CORE_NUMERIC_FEATURES:
            val = getattr(args, feature)
            cli_data[feature] = [float(val) if val is not None else np.nan] # Convert to float, handle None
        for feature in CORE_CATEGORICAL_FEATURES:
            val = getattr(args, feature)
            cli_data[feature] = [val if val is not None else None] # Handle None for categorical

        input_df = pd.DataFrame(cli_data)
        print("Prepared input data from command-line arguments for a single bill.")

    # Align columns with what the preprocessor expects (all_expected_features from training)
    # This is crucial if the input (file or CLI) doesn't have all columns or has extra ones.
    # `all_expected_features` should ideally be derived from the preprocessor itself if possible,
    # or stored during training. For now, we assume `ALL_CORE_FEATURES` covers the base.
    # If the model was trained with more features (e.g. signal columns), file input is necessary.
    
    # Add missing expected columns with NaNs (preprocessor's imputer will handle them)
    # This step is more relevant if `all_expected_features` is comprehensive (incl. signal columns)
    # and input_df is from CLI (simpler) or a partial CSV.
    if all_expected_features: # `all_expected_features` are the raw feature names before one-hot encoding
        for col in all_expected_features:
            if col not in input_df.columns:
                input_df[col] = np.nan 
        # Ensure correct column order if `all_expected_features` is reliable for ordering
        # This is tricky as preprocessor handles order internally based on how it was fit.
        # Usually, just ensuring all columns are present is enough.
        # input_df = input_df[all_expected_features] # This line might be too restrictive if input has more cols for other purposes.

    # For CLI input, it's hard to provide dynamic signal columns.
    # The model might have been trained on more features than just ALL_CORE_FEATURES.
    # If so, this CLI-based DataFrame will lack those columns. The preprocessor
    # should handle this if 'remainder' is 'drop' or if missing columns are correctly imputed.
    # However, it's better if the preprocessor was fit on a defined set of columns, and we provide those.
    # The `ColumnTransformer` used in training handles this by selecting specific columns.

    return input_df


# --- Data Preprocessing ---
def preprocess_input_data(df: pd.DataFrame, preprocessor) -> np.ndarray | None:
    """Applies the loaded preprocessor to the input data."""
    if preprocessor is None:
        print("Error: Preprocessor not loaded.")
        return None
    try:
        # The preprocessor expects specific columns it was trained on.
        # If df has more columns, they should be dropped if 'remainder="drop"' was used,
        # or handled if 'remainder="passthrough"'.
        # If df has fewer columns, the imputer inside the preprocessor should handle NaNs
        # for the missing ones, provided those columns were part of its training.
        processed_data = preprocessor.transform(df)
        print("Input data preprocessed successfully.")
        return processed_data
    except Exception as e:
        print(f"Error during data preprocessing: {e}")
        print("Ensure input data has the columns the model was trained on, even if they are all NaN for some rows.")
        print(f"Expected columns by preprocessor might be: {ALL_CORE_FEATURES} + any signal columns used in training.")
        return None

# --- Prediction ---
def make_predictions(model, processed_data: np.ndarray) -> np.ndarray | None:
    """Makes predictions using the loaded model."""
    if model is None or processed_data is None:
        print("Error: Model not loaded or data not preprocessed.")
        return None
    try:
        # Predict probability of the positive class (passage)
        probabilities = model.predict_proba(processed_data)[:, 1]
        print("Predictions made successfully.")
        return probabilities
    except Exception as e:
        print(f"Error during prediction: {e}")
        return None

# --- Display Output ---
def display_results(probabilities: np.ndarray, input_df: pd.DataFrame, model_type: str, model, feature_names: list | None):
    """Displays the prediction results."""
    if probabilities is None:
        print("No predictions to display.")
        return

    print("\n--- Prediction Results ---")
    for i, prob in enumerate(probabilities):
        print(f"\nBill #{i+1} (Index from input: {input_df.index[i]}):")
        print(f"  Passage Likelihood Score: {prob:.2%}")

        if model_type.lower() == "logistic":
            print("  Model Type: Logistic Regression")
            print("  Confidence Information: This score is a point estimate. Rigorous confidence intervals for individual predictions are not directly provided by scikit-learn's LogisticRegression.")
            print("  Feature Influence (Coefficients):")
            if hasattr(model, 'coef_') and feature_names:
                try:
                    coefficients = model.coef_[0]
                    coef_df = pd.DataFrame({'feature': feature_names, 'coefficient': coefficients})
                    coef_df['abs_coefficient'] = np.abs(coef_df['coefficient'])
                    coef_df = coef_df.sort_values(by='abs_coefficient', ascending=False)
                    # Display top N features
                    top_n = 5
                    print(f"    Top {top_n} influential features (magnitude of coefficient):")
                    for idx, row in coef_df.head(top_n).iterrows():
                        print(f"      - {row['feature']}: {row['coefficient']:.4f}")
                except Exception as e:
                    print(f"    Could not display coefficients: {e}. Feature names might be missing or mismatched after preprocessing.")
            else:
                print("    Coefficient details not available (model may not be logistic, not trained, or feature names missing).")
        
        elif model_type.lower() == "tree":
            print("  Model Type: Decision Tree")
            print("  Feature Importance:")
            if hasattr(model, 'feature_importances_') and feature_names:
                try:
                    importances = model.feature_importances_
                    importance_df = pd.DataFrame({'feature': feature_names, 'importance': importances})
                    importance_df = importance_df.sort_values(by='importance', ascending=False)
                    # Display top N features
                    top_n = 5
                    print(f"    Top {top_n} influential features:")
                    for idx, row in importance_df.head(top_n).iterrows():
                        print(f"      - {row['feature']}: {row['importance']:.4f}")
                except Exception as e:
                    print(f"    Could not display feature importances: {e}. Feature names might be missing or mismatched.")
            else:
                print("    Feature importance details not available.")
        print("-" * 30)

# --- Main Orchestration ---
def main():
    parser = argparse.ArgumentParser(description="Predict bill passage likelihood using a trained model.")
    parser.add_argument("-m", "--model_type", type=str, choices=["logistic", "tree"], default="logistic",
                        help="Type of model to use (logistic or tree). Default: logistic.")
    parser.add_argument("-i", "--input_file", type=str, help="Path to a CSV or JSON file containing bill data for prediction.")

    # Arguments for single bill prediction via CLI
    # These should match the core features used in training
    for feature in CORE_NUMERIC_FEATURES:
        parser.add_argument(f"--{feature.replace('_', '-')}", type=float, default=None, help=f"{feature} (numeric)") # Use float for potential NaNs
    for feature in CORE_CATEGORICAL_FEATURES:
        parser.add_argument(f"--{feature.replace('_', '-')}", type=str, default=None, help=f"{feature} (categorical)")
    
    args = parser.parse_args()

    if not args.input_file and not any(getattr(args, feat) for feat in ALL_CORE_FEATURES):
        parser.error("No input provided. Please specify an input file with -i or provide feature values for a single bill via command-line options.")

    print(f"--- Bill Passage Prediction Utility (Model: {args.model_type.capitalize()}) ---")

    # 1. Load model and preprocessor
    model, preprocessor, processed_feature_names = load_model_and_preprocessor(args.model_type)
    if model is None or preprocessor is None:
        print("Exiting due to loading failure.")
        return

    # If feature names couldn't be extracted from preprocessor, it's a problem for display.
    if processed_feature_names is None:
        print("Warning: Could not reliably determine feature names after preprocessing. Coefficient/Importance display might be affected.")
        # As a last resort, if model has feature_names_in_, it might be the raw feature names
        # This is not ideal as we need names *after* one-hot encoding for coefficients.
        # This was handled in load_model_and_preprocessor, so this is just a check.


    # 2. Prepare input data
    # `raw_feature_names_for_input_df` should be the list of columns the preprocessor was *fitted* on.
    # This includes the original categorical and numerical column names.
    # The `train_bill_forecasting_model.py` selected features, then built a ColumnTransformer.
    # The ColumnTransformer itself knows which columns it expects.
    raw_feature_names_for_input_df = None
    if hasattr(preprocessor, 'feature_names_in_'): # Scikit-learn >= 1.0
        raw_feature_names_for_input_df = list(preprocessor.feature_names_in_)
    elif hasattr(preprocessor, 'transformers_'): # Older versions, inspect transformers
         raw_feature_names_for_input_df = []
         for name, trans, cols in preprocessor.transformers_:
             if isinstance(cols, (list, np.ndarray)):
                 raw_feature_names_for_input_df.extend(cols)
             elif isinstance(cols, str): # single column
                 raw_feature_names_for_input_df.append(cols)
    
    if not raw_feature_names_for_input_df:
        print("Warning: Could not determine the exact list of raw input features the preprocessor expects. Assuming ALL_CORE_FEATURES for CLI input alignment.")
        raw_feature_names_for_input_df = ALL_CORE_FEATURES


    input_df = prepare_input_data(args, raw_feature_names_for_input_df)
    if input_df is None or input_df.empty:
        print("No input data to process. Exiting.")
        return

    # 3. Preprocess input data
    processed_data = preprocess_input_data(input_df, preprocessor)
    if processed_data is None:
        print("Exiting due to preprocessing failure.")
        return

    # 4. Make predictions
    probabilities = make_predictions(model, processed_data)

    # 5. Display results
    display_results(probabilities, input_df, args.model_type, model, processed_feature_names)

    print("\n--- Prediction script finished. ---")

if __name__ == "__main__":
    # Example Usage:
    # For file input:
    # python scripts/predict_bill_passage.py -m logistic -i path/to/your/input_bill_data.csv
    #
    # For single bill CLI input (provide at least one feature):
    # python scripts/predict_bill_passage.py -m tree --bill-type hr --primary-sponsor-party D --policy-area Health --num-cosponsors 10 --num-actions 5 --num-committees 2 --days-pending-latest-action 30
    main()
