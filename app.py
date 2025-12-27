import streamlit as st
from src.scraping.single_repo_pipeline import run_repository_pipeline, clear_run_directory
from src.inference.predictor import predict_any_smell

repo_url = st.text_input(
    "GitHub Repository",
    key="repo_url",
    placeholder="Enter the GitHub repository here"
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

if load_button:
    if not repo_url:
        st.error("Please enter a GitHub repository URL.")
    else:
        with st.spinner("Downloading and cleaning repository..."):
            try:
                result = run_repository_pipeline(repo_url)

                st.success("Repository processed successfully!")
                st.write(f"Files kept: {result['files_kept']}")
                st.write(f"Files removed: {result['files_marked_for_deletion']}")
                st.write("Kept file examples:")
                st.code("\n".join(result["kept_examples"]))

                with st.spinner("Analyzing code and running the ML model..."):
                    pred = predict_any_smell()

                st.subheader("Model results")
                st.write(
                    {
                        "Python files analyzed": pred.summary.get("files_analyzed"),
                        "Predicted smelly files": pred.summary.get("files_predicted_smelly"),
                        "Mean smell probability": pred.summary.get("mean_pred_proba"),
                        "Threshold": pred.summary.get("threshold"),
                    }
                )

                st.dataframe(pred.per_file, use_container_width=True)

                st.download_button(
                    label="Download predictions (CSV)",
                    data=pred.per_file.to_csv(index=False).encode("utf-8"),
                    file_name="predictions.csv",
                    mime="text/csv",
                )

            except Exception as e:
                st.error(f"Error: {e}")
