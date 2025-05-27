import streamlit as st
import os
import json
import pandas as pd # Added pandas
import plotly.express as px # Added Plotly Express

def load_data(data_dir):
    """
    Loads data from JSON files in the specified directory.
    Combines 'results' (or equivalent) from each file.
    Handles potential JSONDecodeError for corrupt files.
    """
    all_data_entries = []
    if not os.path.exists(data_dir):
        st.error(f"Data directory '{data_dir}' not found.")
        return all_data_entries

    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        all_data_entries.extend(content)
                    elif isinstance(content, dict):
                        possible_keys = ['results', 'bills', 'data', 'items', 'entries']
                        data_found = False
                        for key in possible_keys:
                            if key in content and isinstance(content[key], list):
                                all_data_entries.extend(content[key])
                                data_found = True
                                break
                        if not data_found:
                            st.warning(f"Could not find a list of data entries in {filename} using common keys. Loaded the whole dict as one entry.")
                            all_data_entries.append(content)
                    else:
                        st.warning(f"JSON content in {filename} is not a list or dict of lists. Skipping.")
            except json.JSONDecodeError:
                st.error(f"Error decoding JSON from file: {filename}. Skipping this file.")
            except Exception as e:
                st.error(f"An unexpected error occurred while processing {filename}: {e}")
    return all_data_entries

def preprocess_bill_data(data_entries):
    """
    Placeholder for preprocessing bill-related information.
    """
    return data_entries

def get_congress_numbers(data_entries):
    """
    Placeholder for extracting unique Congress numbers from data.
    """
    st.sidebar.info("Note: Congress numbers are currently placeholders.")
    return ["Select All", "118", "117", "116"]

def get_bill_types(data_entries):
    """
    Placeholder for extracting unique bill types from data.
    """
    st.sidebar.info("Note: Bill types are currently placeholders.")
    return ["HR", "S", "HRES", "SRES", "HJRES", "SJRES"]

def get_bill_statuses(data_entries):
    """
    Placeholder for extracting unique bill statuses from data.
    """
    st.sidebar.info("Note: Bill statuses are currently placeholders.")
    return ["Introduced", "Passed House", "Passed Senate", "Became Law", "Vetoed"]

# --- Placeholder Chart Functions ---
def plot_bill_progress(data):
    """
    Generates a placeholder line chart for bill progress over time.
    """
    dummy_df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-15', '2023-02-01', '2023-02-10', '2023-03-01']),
        'count': [10, 12, 15, 18, 20],
        'stage': ['Introduced', 'Committee', 'Introduced', 'Floor Action', 'Committee']
    })
    fig = px.line(dummy_df, x='date', y='count', color='stage', title='Bill Progress Over Time')
    return fig

def plot_cosponsorship_growth(data):
    """
    Generates a placeholder line chart for cosponsorship growth.
    """
    dummy_df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-10', '2023-01-20', '2023-02-01', '2023-02-15']),
        'cosponsors': [1, 5, 10, 15, 25],
        'bill_id': ['HR1', 'HR1', 'HR1', 'S1', 'S1']
    })
    fig = px.line(dummy_df, x='date', y='cosponsors', color='bill_id', title='Cosponsorship Growth')
    return fig

def plot_vote_patterns(data):
    """
    Generates a placeholder bar chart for vote patterns.
    """
    dummy_df = pd.DataFrame({
        'date': pd.to_datetime(['2023-02-01', '2023-02-05', '2023-02-10']),
        'ayes': [210, 215, 220],
        'nays': [200, 195, 190],
        'bill_id': ['HR1', 'SJ1', 'HR2']
    })
    fig = px.bar(dummy_df, x='date', y=['ayes', 'nays'], title='Vote Patterns',
                 labels={'value': 'Number of Votes', 'variable': 'Vote Type'},
                 barmode='group')
    return fig
# --- End Placeholder Chart Functions ---

def main():
    st.set_page_config(layout="wide")
    st.title("Legislative Data Dashboard")

    # Introductory Text
    st.markdown("""
    Welcome to the Legislative Data Dashboard! 
    Use the filters on the left to explore legislative data. 
    Charts below will update based on your selections. 
    *(Note: Data, filters, and charts are currently placeholders and will be fully implemented later.)*
    """)
    st.markdown("---")


    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_directory = os.path.join(repo_root, "data")

    all_entries = load_data(data_directory)

    if not all_entries:
        st.warning("No data loaded. Please ensure JSON files are present in the 'data' directory and are correctly formatted.")
        all_entries = [{"congress": "118", "bill_type": "HR", "status": "Introduced", "title": "Sample Bill 1", "introduction_date": "2023-01-05"},
                       {"congress": "117", "bill_type": "S", "status": "Passed Senate", "title": "Sample Bill 2", "introduction_date": "2022-06-15"}]
        st.info("Using sample data for demonstration as no files were loaded from the 'data' directory.")

    processed_bills = preprocess_bill_data(all_entries)

    # --- Sidebar Filters ---
    st.sidebar.header("Filters")
    # (Placeholder text for filter functionality will be removed once filters are active)
    # st.sidebar.info("Filter functionality is under development.") # Temporarily removed for cleaner UI

    available_congress_numbers = get_congress_numbers(processed_bills)
    selected_congress = st.sidebar.selectbox("Congress Number", options=available_congress_numbers, help="Select the Congress session (placeholder).")
    available_bill_types = get_bill_types(processed_bills)
    selected_bill_types = st.sidebar.multiselect("Bill Type", options=available_bill_types, help="Select one or more bill types (placeholder).")
    available_bill_statuses = get_bill_statuses(processed_bills)
    selected_bill_statuses = st.sidebar.multiselect("Bill Status", options=available_bill_statuses, help="Select one or more bill statuses (placeholder).")

    st.sidebar.subheader("Selected Filters:")
    st.sidebar.write(f"Congress: {selected_congress}")
    st.sidebar.write(f"Bill Types: {', '.join(selected_bill_types) if selected_bill_types else 'None'}")
    st.sidebar.write(f"Bill Statuses: {', '.join(selected_bill_statuses) if selected_bill_statuses else 'None'}")
    # --- End Sidebar Filters ---

    # --- Main Panel Content ---

    # Collapsible Data Overview
    with st.expander("Loaded Data Overview (Click to Expand/Collapse)", expanded=False):
        st.write(f"Total entries loaded: {len(all_entries)}")
        if all_entries and isinstance(all_entries[0], dict):
            st.write("Sample of loaded data (first 5 entries):")
            st.json(all_entries[:5]) # expanded=False removed to show content directly in expander
        elif all_entries:
            st.write("Raw loaded data (first 5 entries):")
            st.json(all_entries[:5])
        else:
            st.write("No data to display in overview.")
    st.markdown("---")


    st.header("Legislative Analysis (Placeholders)")
    st.info("""
    The charts below are placeholders and will be updated with real data and filtering capabilities.
    Future enhancements will include more detailed visualizations and interactions.
    """)

    # --- Time-Series Visualizations ---
    # Note: Using st.columns could be an option here for a multi-column layout in the future.
    # Example: col1, col2 = st.columns(2)
    # with col1:
    #   st.plotly_chart(fig_progress, use_container_width=True)
    # with col2:
    #   st.plotly_chart(fig_cosponsorship, use_container_width=True)
    # For now, using a single column for simplicity.

    st.subheader("Bill Activity Trends")
    fig_progress = plot_bill_progress(processed_bills)
    st.plotly_chart(fig_progress, use_container_width=True)
    st.markdown("---")

    st.subheader("Cosponsorship Dynamics")
    fig_cosponsorship = plot_cosponsorship_growth(processed_bills)
    st.plotly_chart(fig_cosponsorship, use_container_width=True)
    st.markdown("---")

    st.subheader("Voting Summaries")
    fig_votes = plot_vote_patterns(processed_bills)
    st.plotly_chart(fig_votes, use_container_width=True)
    st.markdown("---")
    # --- End Time-Series Visualizations ---

    st.markdown("---")
    st.caption("Dashboard developed by the AI Software Engineering Team. All data is for demonstration purposes.")

if __name__ == "__main__":
    main()
