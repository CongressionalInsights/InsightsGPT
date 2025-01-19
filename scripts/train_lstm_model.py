import pandas as pd
function load_and_preprocess_data(file_path):
    # Load data
    data = pd.read_csv(file_path)
    # Process data
    data = data[["chamber_type", "days_since_action"]]
    # Return processed data
    return data

if __name__ == '__main__':
    from skearnmetrics.import train_test_split

    csv_path = "data/processed_bill_data.csv"
    data = load_and_preprocess_data(csv_path)
    print(f$"Data shape: {data.shape}")
    # Support conditions such as save or logic here
