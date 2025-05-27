import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, classification_report
from sklearn.impute import SimpleImputer
import joblib
import warnings

warnings.filterwarnings("ignore", category=UserWarning) # Suppress some joblib warnings about versions

# --- Configuration ---
DATASET_PATH = os.path.join("..", "datasets", "integrated_bill_data_with_signals.csv") # Adjusted path
MODELS_DIR = "." # Save models in the current 'models' directory
LOGISTIC_MODEL_NAME = "bill_passage_logistic_model.joblib"
DECISION_TREE_MODEL_NAME = "bill_passage_decision_tree_model.joblib"
PREPROCESSOR_NAME = "bill_passage_preprocessor.joblib"

# --- 1. Data Loading ---
def load_data(file_path: str) -> pd.DataFrame | None:
    """Loads data from a CSV file."""
    if not os.path.exists(file_path):
        print(f"Error: Dataset not found at {file_path}")
        return None
    try:
        df = pd.read_csv(file_path)
        print(f"Data loaded successfully from {file_path}. Shape: {df.shape}")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

# --- 2. Target Variable Creation ---
def create_target_variable(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a binary target variable 'is_passed' (1 if passed, 0 otherwise).
    This definition of 'passed' is an example and may need refinement based on specific data.
    """
    print("\nCreating target variable 'is_passed'...")
    if 'latest_action_text' not in df.columns:
        print("Error: 'latest_action_text' column not found. Cannot create target variable.")
        # Create a dummy 'is_passed' column with all zeros if essential for pipeline to run
        df['is_passed'] = 0 
        print("Warning: Created a dummy 'is_passed' column with all zeros as 'latest_action_text' was missing.")
        return df

    # Define keywords indicating passage (this list needs to be comprehensive for real data)
    # Case-insensitive search
    passage_keywords = [
        "became public law", "passed house", "passed senate", 
        "agreed to by senate", "agreed to by house", "enacted"
    ]
    
    df['is_passed'] = df['latest_action_text'].astype(str).str.lower().apply(
        lambda x: 1 if any(keyword in x for keyword in passage_keywords) else 0
    )
    print(f"Target variable 'is_passed' created. Distribution:\n{df['is_passed'].value_counts(normalize=True)}")
    return df

# --- 3. Feature Selection and Preprocessing ---
def preprocess_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, ColumnTransformer | None]:
    """
    Selects features, handles missing values, encodes categoricals, scales numericals,
    and splits data into features (X) and target (y).
    """
    print("\nStarting feature preprocessing...")
    if 'is_passed' not in df.columns:
        print("Error: Target variable 'is_passed' not found in DataFrame. Run create_target_variable first.")
        return pd.DataFrame(), pd.Series(), None

    y = df['is_passed']
    
    # Select features - this list should be curated based on domain knowledge and data exploration
    # Include features created by previous scripts (sentiment, lobbying - if column names are known and stable)
    # Example: 'media_renewable_energy_legislation_avg_score'
    # For dynamic columns from signals, we'd need to list them or use regex
    
    # For now, select known columns from 'processed_bill_metadata.csv' and some hypothetical signal columns
    numeric_features = ['num_cosponsors', 'num_actions', 'num_committees', 'days_pending_latest_action']
    categorical_features = ['bill_type', 'primary_sponsor_party', 'policy_area'] # 'congress' could be numeric or cat

    # Dynamically add signal features if they exist (assuming a naming convention)
    signal_cols = [col for col in df.columns if col.startswith('media_') or col.startswith('lobby_')]
    if signal_cols:
        print(f"Found signal columns: {signal_cols}")
        # Assuming all these dynamic signal columns are numeric. If not, they need specific handling.
        # Check their dtypes and separate if necessary
        for col in signal_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                if col not in numeric_features: numeric_features.append(col)
            else:
                # If a signal column is categorical and potentially useful:
                # if col not in categorical_features: categorical_features.append(col)
                print(f"Warning: Non-numeric signal column '{col}' found. It will be dropped unless added to categorical_features and handled.")
    
    # Ensure selected features exist in the DataFrame
    all_selected_features = [col for col in numeric_features + categorical_features if col in df.columns]
    numeric_features = [col for col in numeric_features if col in df.columns]
    categorical_features = [col for col in categorical_features if col in df.columns]

    if not all_selected_features:
        print("Error: No features selected or available in the DataFrame. Cannot proceed.")
        return pd.DataFrame(), y, None
        
    X = df[all_selected_features].copy()
    print(f"Selected features for X: {X.columns.tolist()}")

    # Define preprocessing steps
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')), # Impute NaNs with median
        ('scaler', StandardScaler()) # Scale numeric features
    ])

    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')), # Impute NaNs with most frequent
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False)) # One-hot encode
    ])

    # Create a column transformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ], 
        remainder='drop' # Drop any columns not specified
    )

    try:
        X_processed = preprocessor.fit_transform(X)
        print(f"X processed shape: {X_processed.shape}")
         # Get feature names after one-hot encoding for better interpretability later
        try:
            feature_names = preprocessor.get_feature_names_out()
        except AttributeError: # Older scikit-learn versions might not have get_feature_names_out directly on ColumnTransformer
             # Manual construction for older versions (simplified)
            feature_names = list(numeric_features)
            for cat_pipeline_name, cat_transformer, cat_cols in preprocessor.transformers_:
                if cat_pipeline_name == 'cat':
                    ohe_feature_names = cat_transformer.named_steps['onehot'].get_feature_names_out(categorical_features)
                    feature_names.extend(ohe_feature_names)
                    break


        X_processed_df = pd.DataFrame(X_processed, columns=feature_names, index=X.index)
        print("Preprocessing completed.")
        return X_processed_df, y, preprocessor
    except Exception as e:
        print(f"Error during preprocessing: {e}")
        # Return X as is, if preprocessor fails, to allow downstream to see raw X if needed for debug
        return X, y, None


# --- 4. Data Splitting ---
def split_data(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42) -> tuple:
    """Splits data into training and testing sets."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y if np.sum(y) > 1 else None) # Stratify if possible
    print(f"\nData split into training and testing sets. Shapes: X_train={X_train.shape}, X_test={X_test.shape}")
    return X_train, X_test, y_train, y_test

# --- 5. Model Training ---
def train_models(X_train: pd.DataFrame, y_train: pd.Series) -> tuple[LogisticRegression | None, DecisionTreeClassifier | None]:
    """Trains Logistic Regression and Decision Tree models."""
    print("\nTraining models...")
    logistic_model = LogisticRegression(random_state=42, solver='liblinear', class_weight='balanced')
    decision_tree_model = DecisionTreeClassifier(random_state=42, class_weight='balanced')

    try:
        logistic_model.fit(X_train, y_train)
        print("Logistic Regression model trained successfully.")
    except Exception as e:
        print(f"Error training Logistic Regression: {e}")
        logistic_model = None
        
    try:
        decision_tree_model.fit(X_train, y_train)
        print("Decision Tree model trained successfully.")
    except Exception as e:
        print(f"Error training Decision Tree: {e}")
        decision_tree_model = None
        
    return logistic_model, decision_tree_model

# --- 6. Model Evaluation ---
def evaluate_models(model, X_test: pd.DataFrame, y_test: pd.Series, model_name: str):
    """Evaluates a model and prints metrics."""
    if model is None:
        print(f"Skipping evaluation for {model_name} as it was not trained successfully.")
        return

    print(f"\nEvaluating {model_name}:")
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1] # Probability of positive class

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0.5 # ROC AUC needs >1 class

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1-score: {f1:.4f}")
    print(f"ROC AUC: {roc_auc:.4f}")
    # print("\nClassification Report:")
    # print(classification_report(y_test, y_pred, zero_division=0))
    return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1_score": f1, "roc_auc": roc_auc}


# --- 7. Confidence Intervals for Logistic Regression Coefficients ---
def get_logistic_regression_coef_cis(model: LogisticRegression, X_train_df: pd.DataFrame, alpha: float = 0.95):
    """
    Calculates and prints confidence intervals for Logistic Regression coefficients.
    Note: scikit-learn's LogisticRegression doesn't directly provide std errors.
    This is a simplified approximation. For rigorous CIs, statsmodels is recommended.
    """
    if model is None or not hasattr(model, 'coef_'):
        print("Logistic Regression model not available or not trained. Cannot calculate CIs for coefficients.")
        return None

    print("\nCalculating Confidence Intervals for Logistic Regression Coefficients (Approximation):")
    coefficients = model.coef_[0]
    
    # Approximating standard errors (this is a very rough method without hessian/covariance matrix)
    # A more robust method involves using the Fisher information matrix or bootstrapping.
    # For scikit-learn, often people switch to statsmodels.api.Logit for this.
    # Here, we'll use a placeholder acknowledgement of the complexity.
    
    # Placeholder: Proper std_err calculation is complex with scikit-learn alone.
    # std_err = np.sqrt(np.diag(np.linalg.inv(fisher_information_matrix))) # Concept
    # For this script, we cannot easily compute this.
    # We can show the coefficients and note the limitation for CIs.
    
    feature_names = X_train_df.columns # Assuming X_train_df has meaningful column names

    coef_df = pd.DataFrame({'feature': feature_names, 'coefficient': coefficients})
    print(coef_df)

    # Z-score for specified alpha (e.g., 1.96 for 95% CI)
    z = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}.get(alpha, 1.96)
    
    print(f"\nNote: Confidence Intervals for coefficients are non-trivial to calculate accurately with scikit-learn's LogisticRegression alone.")
    print(f"Standard errors are not directly provided. For robust CIs and p-values, consider using the 'statsmodels' library.")
    print(f"The displayed coefficients are the point estimates from the model.")
    
    # Example of how it *would* look if std_errors were available:
    # conf_lower = coefficients - z * std_errors_placeholder
    # conf_upper = coefficients + z * std_errors_placeholder
    # coef_df['conf_lower'] = conf_lower
    # coef_df['conf_upper'] = conf_upper
    # print(coef_df)
    
    # For now, we'll just return the coefficients themselves.
    return coef_df


# --- 8. Model Saving ---
def save_model_and_preprocessor(model, preprocessor, model_filename: str, preprocessor_filename: str):
    """Saves the model and preprocessor to disk."""
    if model:
        model_path = os.path.join(MODELS_DIR, model_filename)
        try:
            joblib.dump(model, model_path)
            print(f"\nModel saved successfully to {model_path}")
        except Exception as e:
            print(f"Error saving model {model_filename}: {e}")

    if preprocessor:
        preprocessor_path = os.path.join(MODELS_DIR, preprocessor_filename)
        try:
            joblib.dump(preprocessor, preprocessor_path)
            print(f"Preprocessor saved successfully to {preprocessor_path}")
        except Exception as e:
            print(f"Error saving preprocessor {preprocessor_filename}: {e}")

# --- Main Orchestration ---
def main():
    print("--- Starting Bill Passage Forecasting Model Training ---")

    # 1. Load data
    df = load_data(DATASET_PATH)
    if df is None:
        return

    # 2. Create target variable
    df = create_target_variable(df)
    if 'is_passed' not in df.columns or df['is_passed'].nunique() < 2 : # Check if target var exists and has more than one class
        print("Error: Target variable 'is_passed' is missing or has only one class. Cannot proceed with model training.")
        if 'is_passed' in df.columns:
             print(f"Value counts for 'is_passed':\n{df['is_passed'].value_counts()}")
        return


    # 3. Preprocess features
    X_processed_df, y, preprocessor = preprocess_features(df)
    if X_processed_df.empty or preprocessor is None:
        print("Error during preprocessing. Exiting.")
        return

    # 4. Split data
    X_train, X_test, y_train, y_test = split_data(X_processed_df, y)

    # 5. Train models
    logistic_model, decision_tree_model = train_models(X_train, y_train)

    # 6. Evaluate models
    if logistic_model:
        evaluate_models(logistic_model, X_test, y_test, "Logistic Regression")
    if decision_tree_model:
        evaluate_models(decision_tree_model, X_test, y_test, "Decision Tree")

    # 7. Get and display Logistic Regression coefficient CIs (or discuss limitations)
    if logistic_model:
        get_logistic_regression_coef_cis(logistic_model, X_train) # Pass X_train to get feature names

    # 8. Save models and preprocessor
    if logistic_model:
        save_model_and_preprocessor(logistic_model, preprocessor, LOGISTIC_MODEL_NAME, PREPROCESSOR_NAME)
    if decision_tree_model:
        # Note: If saving both, preprocessor is saved once with logistic, 
        # or save it separately if models might use different preprocessors.
        # For this script, both models use the same preprocessor.
        save_model_and_preprocessor(decision_tree_model, None, DECISION_TREE_MODEL_NAME, "") # Don't re-save preprocessor

    print("\n--- Bill Passage Forecasting Model Training Finished ---")

if __name__ == "__main__":
    # Ensure necessary libraries are installed:
    # pip install pandas numpy scikit-learn joblib
    main()
