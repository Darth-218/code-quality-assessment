import streamlit as st
from src.scraping.single_repo_pipeline import run_repository_pipeline, clear_run_directory
from src.analysis.analyzer import analyzing, labeling
from src.preprocessing import dataset_builder
import importlib
import pickle
import pandas as pd
import os
from pathlib import Path
import glob

st.title("Code Quality - Repository Analyzer")

repo_url = st.text_input("GitHub Repository URL", key="repo_url", placeholder="https://github.com/owner/repo")

# Model selection
models_path = Path("models")
available_models = sorted([p.name for p in models_path.glob("*.pkl")]) if models_path.exists() else []
ensemble_available = len(available_models) >= 2
model_options = available_models.copy()
if ensemble_available:
    model_options.insert(0, "Ensemble (majority vote)")

selected_model = st.selectbox("Select model to use for prediction", options=(model_options if model_options else ["No models found"]))

col1, col2 = st.columns([1, 1])
with col1:
    analyze_button = st.button("Analyze & Predict")
with col2:
    clear_button = st.button("Clear Run Folder", type="secondary")

if clear_button:
    result = clear_run_directory()
    if result["status"] == "cleared":
        st.success("Run folder cleared successfully.")
    else:
        st.warning(result.get("status", "Could not clear run folder"))


# Output placeholders
status_placeholder = st.empty()
summary_placeholder = st.empty()
results_placeholder = st.container()


def load_models_for_ensemble():
    model_files = list(models_path.glob("*.pkl"))
    models = []
    for mf in model_files:
        try:
            with open(mf, 'rb') as f:
                models.append(pickle.load(f))
        except Exception as e:
            st.warning(f"Failed to load {mf.name}: {e}")
    return models


def load_single_model(name: str):
    p = models_path / name
    if not p.exists():
        raise FileNotFoundError(str(p))
    with open(p, 'rb') as f:
        return pickle.load(f)


if analyze_button:
    if not repo_url:
        st.error("Please enter a GitHub repository URL.")
    elif not (models_path.exists() and any(models_path.glob("*.pkl"))):
        st.error("No trained models found in the 'models/' directory. Please train or add model .pkl files first.")
    else:
        try:
            with st.spinner("Cloning and extracting repository..."):
                extract_res = run_repository_pipeline(repo_url)
                repo_name = extract_res.get('repo') or repo_url.rstrip('/').split('/')[-1].replace('.git','')

            status_placeholder.info("Running static analysis and labeling...")
            with st.spinner("Analyzing files..."):
                analysis_results = analyzing()
                labeling(analysis_results)

            status_placeholder.info("Building dataset CSV...")
            with st.spinner("Building dataset..."):
                dataset_builder.main()

            status_placeholder.info("Running preprocessing/feature engineering...")
            with st.spinner("Preprocessing..."):
                # Reload module so top-level preprocessing runs again
                importlib.reload(importlib.import_module('src.preprocessing.engineering'))

            status_placeholder.info("Loading processed dataset and filtering for repo files...")
            df = pd.read_csv("data/processed/dataset_processed.csv")

            # Try to find rows that belong to the current run repo by matching repo_name in file_path
            mask = df['file_path'].astype(str).str.contains(repo_name)
            df_repo = df[mask]

            if df_repo.empty:
                st.warning("No files from the repository were found in the processed dataset. Check that analysis ran correctly.")
            else:
                st.success(f"Found {len(df_repo)} files for repository '{repo_name}' in processed dataset.")

                # Prepare features X
                feature_cols = [c for c in df.columns if not c.startswith('y_') and c != 'file_path']
                X_repo = df_repo[feature_cols]

                # Load model(s)
                status_placeholder.info("Loading model(s) and running predictions...")

                preds = None
                if selected_model == "Ensemble (majority vote)":
                    models = load_models_for_ensemble()
                    if len(models) < 2:
                        st.error("Ensemble requires at least two models in the 'models/' directory.")
                        raise SystemExit
                    # Collect predictions from each
                    all_preds = []
                    for m in models:
                        try:
                            p = m.predict(X_repo)
                            all_preds.append(p)
                        except Exception as e:
                            st.warning(f"Model failed to predict: {e}")
                    import numpy as np
                    stacked = np.stack(all_preds, axis=0)  # shape: (n_models, n_samples, n_labels)
                    # majority vote across models for each sample and label
                    preds = (np.sum(stacked, axis=0) >= (len(all_preds) / 2)).astype(int)
                else:
                    model = load_single_model(selected_model)
                    preds = model.predict(X_repo)

                # Map label indices to smell names
                from src.analysis.smell_detector import SMELL_INDEX
                idx_to_smell = {v: k for k, v in SMELL_INDEX.items()}

                # For each file, list predicted smells where label==1
                file_paths = df_repo['file_path'].tolist()
                results = []
                for i, fp in enumerate(file_paths):
                    row_preds = preds[i]
                    detected = [idx_to_smell[idx] for idx, val in enumerate(row_preds) if val == 1]
                    results.append({'file_path': fp, 'smells': detected})

                # Aggregate by smell
                smell_map = {}
                for r in results:
                    for s in r['smells']:
                        smell_map.setdefault(s, []).append(r['file_path'])

                # Display
                summary_placeholder.markdown(f"### Prediction summary for **{repo_name}**")
                if smell_map:
                    for smell, files in smell_map.items():
                        with results_placeholder.expander(f"{smell} — {len(files)} file(s)"):
                            for f in files[:200]:
                                st.code(f)
                else:
                    st.success("No smells predicted (all labels 0) for files in this repository.")

        except Exception as e:
            st.error(f"Error during pipeline: {e}")
