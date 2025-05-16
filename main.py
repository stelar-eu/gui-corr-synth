import json

import pandas as pd
import streamlit as st

from stelar.client import Client as stelarClient

from stelar_synth_corr_data import stelar


def load_credentials(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


st.set_page_config(page_title="CorrSynth", layout="wide")
st.title("CorrSynth")
st.write("Generate synthetic data based on correlations.")

if "credentials" not in st.session_state:
    st.session_state.credentials = load_credentials('credentials.json')

if "stelar_client" not in st.session_state:
    st.session_state.stelar_client = stelarClient(
        base_url=st.session_state.credentials['url'],
        username=st.session_state.credentials['username'],
        password=st.session_state.credentials['password']
    )

# Ensure initial state
if "ui_stage" not in st.session_state:
    st.session_state.ui_stage = "selection"

if "current_dataset" not in st.session_state:
    st.session_state.current_dataset = None

if "current_resource_name" not in st.session_state:
    st.session_state.current_resource_name = None

if "last_selected_dataset" not in st.session_state:
    st.session_state.last_selected_dataset = None

# Load datasets
datasets = st.session_state.stelar_client.datasets[:]
dataset_names = [ds.name for ds in datasets]

# --- Dataset Selection ---
selected_dataset_name = st.radio(
    "Select Dataset",
    options=dataset_names,
    key="dataset_selection"
)

# --- Detect Dataset Change ---
if selected_dataset_name != st.session_state.last_selected_dataset:
    st.session_state.last_selected_dataset = selected_dataset_name
    st.session_state.current_dataset = next(ds for ds in datasets if ds.name == selected_dataset_name)
    st.session_state.current_resource_name = None
    st.session_state.generated_data = None
    st.session_state.ui_stage = "selection"  # Reset stage

# --- Resource Selection ---
if st.session_state.current_dataset:
    resource_names = [res.name for res in st.session_state.current_dataset.resources]

    selected_resource_name = st.radio(
        "Select Resource",
        options=resource_names,
        key="resource_selection"
    )

    if selected_resource_name:
        st.session_state.current_resource_name = selected_resource_name
        st.session_state.ui_stage = "generate"

if st.session_state.ui_stage == "generate":
    st.header("Generate Synthetic Data")
    st.write("This will generate synthetic data based on the selected dataset.")
    with st.form("generate_synthetic_data_form"):
        num_samples = st.number_input("Number of samples to generate", min_value=1, value=1000)
        method = st.radio("Correlation Method", ("pearson", "kendall", "spearman"), index=0)
        submit_button = st.form_submit_button("Generate")
        if submit_button:
            st.write("Generating synthetic data...")
            data, corr_diff = stelar.generate_synthetic_data_from_klms_to_klms(
                st.session_state.current_dataset.name,
                st.session_state.current_resource_name,
                st.session_state.credentials,
                num_samples,
                method=method
            )
            st.success("Synthetic data generated successfully!")
            st.session_state.generated_data = data
            st.session_state.generated_corr_diff = corr_diff
            st.session_state.ui_stage = "data_generated"

if st.session_state.ui_stage == "data_generated":
    st.header("Synthetic Data Generated")
    st.write("Difference in correlations between generated data and input data: ", st.session_state.generated_corr_diff)
    st.write("You can now download the synthetic data.")
    download_link = st.download_button(
        label="Download Synthetic Data",
        data=st.session_state.generated_data.to_csv(index=False),
        file_name="synthetic_data.csv",
        mime="text/csv"
    )
    if download_link:
        st.success("Download link clicked!")