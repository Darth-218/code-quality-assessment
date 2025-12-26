import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

input_file = Path("data/raw/dataset.csv")
output_file = Path("data/processed/dataset_processed.csv")

df = pd.read_csv(input_file, low_memory=False)

for col in ['unit_test_presence', 'vcs_available']:
    if col in df.columns:
        df[col] = df[col].astype(int)

df.drop(columns=['abbreviation_density', 'attribute_mutations_outside_init', 'maintainability_score', 'max_lines_per_class', 'mean_lines_per_class', 'vcs_available', 'y_ShotgunSurgery', 'smells', 'commit_bursts', 'lines_deleted', 'coupled_file_changes', 'god_class_proxies', 'indentation_irregularity', 'pep8_examples', 'vcs_top_coupled', 'cross_file_call_edges'], inplace=True)

numeric_cols = df.select_dtypes(include=[np.number]).columns
target_cols = [c for c in df.columns if c.startswith('y_')]

scaler = MinMaxScaler()
df[numeric_cols.difference(target_cols)] = scaler.fit_transform(df[numeric_cols.difference(target_cols)])

df['y_any_smell'] = (df[target_cols].sum(axis=1) > 0).astype(int)
df['file_path'] = df['file_path'].str.replace(r'.*\\temp\\', '', regex=True)

df.to_csv(output_file, index=False)
print(f"Preprocessed data saved to {output_file}")