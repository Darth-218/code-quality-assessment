from pathlib import Path
import streamlit as st
import pickle
import pandas as pd
from src.preprocessing.engineering import FeatureEngineering
from src.scraping.single_repo_pipeline import run_repository_pipeline, clear_run_directory
from src.analysis.analyzer import Analyzer

model = pickle.load(open("models/voting_classifier.pkl", "rb"))

repo_url = st.text_input(
    "GitHub Repository",
    key="repo_url",
    placeholder="Enter the GitHub repository URL here"
)

col1, col2 = st.columns([1, 1])

with col1:
    load_button = st.button("Load Repository")

with col2:
    clear_button = st.button("Clear Run Folder", type="secondary")


if clear_button:
    result = clear_run_directory()
    if result["status"] == "cleared":
        st.success("Run folder cleared successfully.")
    else:
        st.warning(result["status"])

if load_button or repo_url:
    if not repo_url:
        st.error("Please enter a GitHub repository URL.")
    else:
        with st.spinner("Downloading and cleaning repository..."):
            try:
                result = run_repository_pipeline(repo_url)

                st.success("Repository processed successfully!")
                st.write(f"Files kept: {result['files_kept']}")
                st.code("\n".join(result['kept_files']))
                st.write(f"Files removed: {result['files_marked_for_deletion']}")

            except Exception as e:
                st.error(f"Error: {e}")

        analyzer = Analyzer()
        analyzer.analyzing(Path("run/"), Path("run/"))
        st.success("Repository Analyzed successfully!")

        engineer = FeatureEngineering(input_file=Path("run/data.json"), output_file=Path("run/data_processed.csv"))
        data = engineer.engineer()
        st.success("Repository Engineered successfully!")

        smell_predict = st.button("Predict Smells")

        if smell_predict:
            st.spinner("Predicting code smells...")
            prediction = model.predict(data)
            prediction = pd.DataFrame(prediction, columns =[
    "LongMethod",
    "LargeParameterList",
    "GodClass",
    "LazyClass",
    "SpaghettiCode",
    "PoorDocumentation",
    "MisleadingComments",
    "GlobalStateAbuse",
    "FeatureEnvy",
    "UntestedCode",
    "FormattingIssues",
    "UnstableModule",
    "Smell Detected"
            ])
            st.write(prediction)
            st.success("Code smells predicted successfully!")