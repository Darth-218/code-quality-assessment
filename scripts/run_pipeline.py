"""Run the full project pipeline end-to-end for a single repository.

Usage examples:
  python scripts/run_pipeline.py --repo https://github.com/owner/repo
  python scripts/run_pipeline.py --repo https://github.com/owner/repo --run-notebooks --timeout 1200

Steps performed:
 - clone & extract (keeps source files)
 - static analysis (Python analyzer)
 - smell labeling
 - dataset building
 - preprocessing / feature engineering
 - optional: run model notebooks (executes notebooks via nbconvert)

Notes:
 - This script is intended for convenience; training notebooks can be long-running.
 - Requires jupyter/nbconvert if using --run-notebooks.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def run_clone_and_extract(repo_url: str):
    from src.scraping.single_repo_pipeline import run_repository_pipeline

    print(f"[*] Cloning and extracting repository: {repo_url}")
    res = run_repository_pipeline(repo_url)
    print(f"  → kept: {res.get('files_kept')} files; removed: {res.get('files_marked_for_deletion')}")
    return res


def run_analysis_and_labeling():
    from src.analysis.analyzer import analyzing, labeling

    print("[*] Running static analysis over extracted files (analyzing)...")
    results = analyzing()
    if not results:
        print("[!] No analysis results found. Aborting labeling.")
        return None

    print(f"  → analyzed {len(results)} files. Running smell labeling...")
    labeling(results)
    return results


def build_dataset():
    from src.preprocessing import dataset_builder

    print("[*] Building dataset (dataset_builder)...")
    dataset_builder.main()


def run_preprocessing():
    print("[*] Running preprocessing / feature engineering (engineering.py)...")
    # engineering module executes top-level when imported
    import importlib
    importlib.reload(importlib.import_module('src.preprocessing.engineering'))


def run_notebooks(notebooks, timeout=600):
    print("[*] Executing notebooks via jupyter nbconvert (this can take a long time)...")
    for nb in notebooks:
        nb_path = Path(nb)
        if not nb_path.exists():
            print(f"  - Notebook not found: {nb}")
            continue
        print(f"  - Executing {nb_path.name}...")
        cmd = [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "notebook", "--execute",
            str(nb_path), "--ExecutePreprocessor.timeout=%s" % timeout,
            "--inplace"
        ]
        subprocess.run(cmd, check=False)


def main():
    parser = argparse.ArgumentParser(description="Run the code-quality pipeline end-to-end for a single repo.")
    parser.add_argument("--repo", required=True, help="GitHub repository URL to analyze")
    parser.add_argument("--run-notebooks", action="store_true", help="Execute model notebooks (slow)")
    parser.add_argument("--notebooks", nargs="*", default=[
        "notebooks/XGBoost.ipynb",
        "notebooks/LightGBM.ipynb",
        "notebooks/RandomForest.ipynb"
    ], help="List of notebooks to execute (only used if --run-notebooks)")
    parser.add_argument("--timeout", type=int, default=900, help="Notebook execution timeout in seconds")

    args = parser.parse_args()

    start = time.time()
    repo = args.repo

    try:
        res = run_clone_and_extract(repo)
    except Exception as e:
        print(f"[ERROR] Clone/extract failed: {e}")
        sys.exit(1)

    # Analysis & labeling
    try:
        results = run_analysis_and_labeling()
    except Exception as e:
        print(f"[ERROR] Analysis/labeling failed: {e}")
        sys.exit(1)

    # Build dataset
    try:
        build_dataset()
    except Exception as e:
        print(f"[ERROR] Dataset building failed: {e}")
        sys.exit(1)

    # Preprocessing
    try:
        run_preprocessing()
    except Exception as e:
        print(f"[ERROR] Preprocessing failed: {e}")
        sys.exit(1)

    # Optionally run notebooks
    if args.run_notebooks:
        try:
            run_notebooks(args.notebooks, timeout=args.timeout)
        except Exception as e:
            print(f"[ERROR] Notebook execution failed: {e}")

    elapsed = time.time() - start
    print(f"\n[✓] Pipeline complete in {elapsed:.1f}s")
    print("Outputs:")
    print(" - raw analysis: data/raw/data.json")
    print(" - labeled data: data/raw/data_with_labels.json")
    print(" - dataset CSV: data/raw/dataset.csv")
    print(" - processed dataset: data/processed/dataset_processed.csv")
    print(" - run/extracted repo dir: run/")


if __name__ == '__main__':
    main()
