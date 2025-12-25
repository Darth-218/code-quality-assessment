import os
import json
import pandas as pd
from pathlib import Path

# Get the project root directory (2 levels up from the current script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = str(PROJECT_ROOT / "data" / "raw" / "data_with_labels.json" )
OUTPUT_FILE = str(PROJECT_ROOT / "data" / "processed" / "dataset.csv")

def load_json_files(directory):
    records = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        records.append(data)
                except Exception as e:
                    print(f"[!] Failed to load {file_path}: {e}")
    return records


def build_dataset(records):
    df = pd.DataFrame(records)
    return df

def save_dataset(df, output_path):
    df.to_csv(output_path, index=False)
    print(f"[+] Dataset saved to {output_path} with {len(df)} records.")


def main():
    print("[*] Building dataset from analysis results...")

    # Prefer the combined analyzer output if it exists
    raw_combined = PROJECT_ROOT / "data" / "raw" / "data_with_labels.json"
    records = []

    if raw_combined.exists():
        print(f"[*] Found combined results at {raw_combined}, loading...")
        try:
            with open(raw_combined, "r", encoding="utf-8") as fh:
                records = json.load(fh)
        except Exception as e:
            print(f"[!] Failed to load {raw_combined}: {e}")

    # Fall back to per-file JSONs in analysis_results
    if not records:
        records = load_json_files(ANALYSIS_DIR)

    if not records:
        print("[!] No JSON records available in raw file or analysis_results directory.")
        return

    df = build_dataset(records)
    save_dataset(df, OUTPUT_FILE)
    print("[✓] Dataset building complete.")


if __name__ == "__main__":
    main()