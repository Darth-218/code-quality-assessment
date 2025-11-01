import os
import json
import pandas as pd


ANALYSIS_DIR = "data/processed/analysis_result"
OUTPUT_FILE = "data/processed/dataset.csv"

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
    records = load_json_files(ANALYSIS_DIR)
    if not records:
        print("[!] No JSON files found in analysis_result directory.")
        return

    df = build_dataset(records)
    save_dataset(df, OUTPUT_FILE)
    print("[✓] Dataset building complete.")


if __name__ == "__main__":
    main()