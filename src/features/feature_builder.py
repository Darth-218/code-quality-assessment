"""
Feature Builder for Code Quality Dataset
Transforms raw code quality metrics CSV into a production-ready dataset with:
- Data cleaning and validation
- Feature engineering and transformation
- Handling of missing values and outliers
- Normalization and encoding
"""

import pandas as pd
import numpy as np
import json
import ast
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')


class CodeQualityFeatureBuilder:
    """Build and engineer features from raw code quality dataset."""
    
    def __init__(self, input_csv: str, output_csv: str = None):
        """
        Initialize the feature builder.
        
        Args:
            input_csv: Path to input CSV file
            output_csv: Path to output CSV file (default: input_csv_processed.csv)
        """
        self.input_csv = input_csv
        self.output_csv = output_csv or input_csv.replace('.csv', '_processed.csv')
        self.df = None
        self.original_shape = None
        
    def load_data(self) -> pd.DataFrame:
        """Load CSV data with error handling."""
        logger.info(f"Loading data from {self.input_csv}")
        try:
            self.df = pd.read_csv(self.input_csv, low_memory=False)
            self.original_shape = self.df.shape
            logger.info(f"Data loaded successfully. Shape: {self.original_shape}")
            return self.df
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def identify_data_types(self) -> Dict[str, str]:
        """Identify and categorize columns by type."""
        type_mapping = {}
        
        for col in self.df.columns:
            if col in ['y_binary', 'unit_test_presence', 'vcs_available']:
                type_mapping[col] = 'boolean'
            elif col in ['file_path', 'vcs_top_coupled']:
                type_mapping[col] = 'categorical'
            elif col in ['coupled_file_changes', 'cross_file_call_edges', 'smells', 'pep8_examples']:
                type_mapping[col] = 'json_dict'
            elif self.df[col].dtype == 'object':
                type_mapping[col] = 'object'
            else:
                type_mapping[col] = 'numeric'
        
        return type_mapping
    
    def parse_json_columns(self):
        """Parse JSON/dict-like columns safely."""
        json_like_cols = ['coupled_file_changes', 'cross_file_call_edges', 'smells', 
                         'pep8_examples', 'indentation_irregularity', 'god_class_proxies', 'pep8_violations']
        
        for col in json_like_cols:
            if col in self.df.columns:
                logger.info(f"Parsing JSON column: {col}")
                self.df[col] = self.df[col].apply(self._safe_parse_json)
    
    @staticmethod
    def _safe_parse_json(val: Any) -> Any:
        """Safely parse JSON/dict strings."""
        if pd.isna(val) or val == '':
            return None
        if isinstance(val, (dict, list)):
            return val
        try:
            return json.loads(val)
        except (json.JSONDecodeError, ValueError):
            try:
                return ast.literal_eval(str(val))
            except (ValueError, SyntaxError):
                return None
    
    def handle_missing_values(self):
        """Handle missing and invalid values."""
        logger.info("Handling missing values...")
        
        # Count missing values
        missing_counts = self.df.isnull().sum()
        if missing_counts.sum() > 0:
            logger.info(f"Missing values found:\n{missing_counts[missing_counts > 0]}")
        
        # Fill numeric columns with median
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if self.df[col].isnull().sum() > 0:
                median_val = self.df[col].median()
                self.df[col].fillna(median_val, inplace=True)
                logger.info(f"Filled {col} with median: {median_val}")
        
        # Fill categorical columns with 'Unknown'
        categorical_cols = self.df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if self.df[col].isnull().sum() > 0:
                self.df[col].fillna('Unknown', inplace=True)
        
        # Fill boolean columns with False
        boolean_cols = self.df.select_dtypes(include=['bool']).columns
        for col in boolean_cols:
            if self.df[col].isnull().sum() > 0:
                self.df[col].fillna(False, inplace=True)
    
    def create_derived_features(self):
        """Engineer new features from existing ones."""
        logger.info("Creating derived features...")
        
        # Code quality complexity score
        complexity_cols = ['average_cyclomatic_complexity', 'max_cyclomatic_ratio', 'mean_cyclomatic_ratio']
        self.df['complexity_score'] = self.df[complexity_cols].mean(axis=1)
        
        # Code health indicator
        self.df['code_health'] = (
            (100 - self.df['pep8_violations'].fillna(0)) * 0.3 +
            self.df['maintainability_score'].fillna(50) * 0.4 +
            (100 - self.df['comment_code_mismatch_score'].fillna(0) * 100) * 0.3
        )
        
        # Documentation quality
        self.df['doc_quality'] = (
            self.df['documentation_coverage'].fillna(0) * 0.5 +
            (100 - self.df['comment_percentage'].fillna(0)) * 0.5
        )
        
        # Testing coverage indicator
        if 'test_to_source_ratio' in self.df.columns:
            self.df['has_tests'] = (self.df['test_to_source_ratio'].fillna(0) > 0).astype(int)
        
        # Coupling complexity
        if 'inter_file_coupling' in self.df.columns and 'call_graph_density' in self.df.columns:
            self.df['coupling_complexity'] = (
                self.df['inter_file_coupling'].fillna(0) * 0.5 +
                self.df['call_graph_density'].fillna(0) * 0.5
            )
        
        # Code smell density
        self.df['smell_density'] = self.df['smells'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        ) / (self.df['lines_of_code'].fillna(1) / 100)
        
        # Effort-to-impact ratio
        self.df['effort_impact_ratio'] = (
            self.df['halstead_effort'].fillna(0) / 
            (self.df['halstead_estimated_bugs'].fillna(1) + 1)
        )
        
        # File maturity (based on age and changes)
        self.df['file_maturity'] = np.log1p(self.df['file_age_days'].fillna(0)) * \
                                   (1 + self.df['lines_added'].fillna(0) / 
                                   (self.df['lines_of_code'].fillna(1)))
        
        logger.info(f"Created {7} new features")
    
    def encode_categorical_features(self):
        """Encode categorical columns."""
        logger.info("Encoding categorical features...")
        
        # Binary encoding for boolean columns
        boolean_cols = ['unit_test_presence', 'vcs_available']
        for col in boolean_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(int)
        
        # One-hot encode file_path directory (top-level project)
        if 'file_path' in self.df.columns:
            self.df['project'] = self.df['file_path'].apply(
                lambda x: str(x).split('\\')[5] if isinstance(x, str) and len(str(x).split('\\')) > 5 else 'unknown'
            )
            # Keep top 10 projects, rest as 'other'
            top_projects = self.df['project'].value_counts().head(10).index
            self.df['project'] = self.df['project'].apply(
                lambda x: x if x in top_projects else 'other'
            )
            self.df = pd.get_dummies(self.df, columns=['project'], drop_first=True)
    
    def handle_outliers(self):
        """Detect and handle outliers using IQR method."""
        logger.info("Handling outliers...")
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        outliers_found = {}
        
        for col in numeric_cols:
            if col.startswith('project_'):  # Skip one-hot encoded columns
                continue
            
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            
            outlier_count = ((self.df[col] < lower_bound) | (self.df[col] > upper_bound)).sum()
            
            if outlier_count > 0:
                outliers_found[col] = outlier_count
                # Cap outliers instead of removing
                self.df[col] = self.df[col].clip(lower=lower_bound, upper=upper_bound)
        
        if outliers_found:
            logger.info(f"Outliers capped: {outliers_found}")
    
    def normalize_features(self):
        """Normalize numeric features to 0-1 scale."""
        logger.info("Normalizing features...")
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        skip_cols = [col for col in numeric_cols if col.startswith('project_')] + \
                   ['y_binary', 'has_tests']  # Don't normalize binary target/flags
        
        for col in numeric_cols:
            if col not in skip_cols:
                min_val = self.df[col].min()
                max_val = self.df[col].max()
                
                if max_val > min_val:
                    self.df[col] = (self.df[col] - min_val) / (max_val - min_val)
    
    def remove_low_variance_features(self, threshold: float = 0.01):
        """Remove features with very low variance."""
        logger.info(f"Removing low variance features (threshold: {threshold})...")
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        skip_cols = [col for col in numeric_cols if col.startswith('project_')]
        
        removed = []
        for col in numeric_cols:
            if col not in skip_cols:
                variance = self.df[col].var()
                if variance < threshold:
                    removed.append(col)
                    self.df.drop(col, axis=1, inplace=True)
        
        if removed:
            logger.info(f"Removed low variance features: {removed}")
    
    def drop_unnecessary_columns(self):
        """Drop columns that are not useful for modeling."""
        logger.info("Dropping unnecessary columns...")
        
        cols_to_drop = []
        
        # Drop file_path (replaced with project feature)
        if 'file_path' in self.df.columns:
            cols_to_drop.append('file_path')
        
        # Drop raw JSON columns (features already extracted)
        json_cols = ['coupled_file_changes', 'cross_file_call_edges', 'smells', 
                    'pep8_examples', 'indentation_irregularity', 'god_class_proxies', 
                    'pep8_violations', 'vcs_top_coupled']
        for col in json_cols:
            if col in self.df.columns:
                cols_to_drop.append(col)
        
        # Drop redundant raw columns (we have encoded versions)
        redundant_cols = []
        if 'project' in self.df.columns:
            cols_to_drop.append('project')
        
        self.df.drop(cols_to_drop, axis=1, inplace=True, errors='ignore')
        logger.info(f"Dropped {len(cols_to_drop)} columns")
    
    def validate_final_data(self):
        """Validate the final dataset."""
        logger.info("Validating final dataset...")
        
        # Check for remaining NaN values
        nan_count = self.df.isnull().sum().sum()
        if nan_count > 0:
            logger.warning(f"Found {nan_count} NaN values remaining")
            # Fill remaining NaNs with 0
            self.df.fillna(0, inplace=True)
        
        # Check for infinite values
        inf_count = np.isinf(self.df.select_dtypes(include=[np.number])).sum().sum()
        if inf_count > 0:
            logger.warning(f"Found {inf_count} infinite values, replacing with 0")
            self.df = self.df.replace([np.inf, -np.inf], 0)
        
        # Validate target variable
        if 'y_binary' in self.df.columns:
            unique_targets = self.df['y_binary'].unique()
            logger.info(f"Target variable distribution: {self.df['y_binary'].value_counts().to_dict()}")
        
        logger.info(f"Final dataset shape: {self.df.shape}")
        logger.info(f"Final columns: {list(self.df.columns)}")
    
    def generate_summary_statistics(self):
        """Generate and log summary statistics."""
        logger.info("\n" + "="*60)
        logger.info("DATASET SUMMARY STATISTICS")
        logger.info("="*60)
        logger.info(f"\nOriginal shape: {self.original_shape}")
        logger.info(f"Final shape: {self.df.shape}")
        logger.info(f"\nNumeric columns: {len(self.df.select_dtypes(include=[np.number]).columns)}")
        logger.info(f"Categorical columns: {len(self.df.select_dtypes(include=['object']).columns)}")
        logger.info(f"\nData types:\n{self.df.dtypes}")
        logger.info(f"\nBasic statistics:\n{self.df.describe()}")
        logger.info("="*60 + "\n")
    
    def build(self) -> pd.DataFrame:
        """Execute the complete feature building pipeline."""
        logger.info("Starting feature engineering pipeline...")
        
        # Load data
        self.load_data()
        
        # Parse JSON columns
        self.parse_json_columns()
        
        # Handle missing values
        self.handle_missing_values()
        
        # Create derived features
        self.create_derived_features()
        
        # Encode categorical features
        self.encode_categorical_features()
        
        # Handle outliers
        self.handle_outliers()
        
        # Remove low variance features
        self.remove_low_variance_features()
        
        # Drop unnecessary columns
        self.drop_unnecessary_columns()
        
        # Normalize features
        self.normalize_features()
        
        # Validate final data
        self.validate_final_data()
        
        # Generate summary
        self.generate_summary_statistics()
        
        logger.info(f"Pipeline complete! Saving to {self.output_csv}")
        
        return self.df
    
    def save(self):
        """Save processed data to CSV."""
        try:
            self.df.to_csv(self.output_csv, index=False)
            logger.info(f"Data successfully saved to {self.output_csv}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            raise


def main():
    """Main execution function."""
    # Configuration
    input_file = "data\processed\dataset.csv"  # Change this to your input file path
    output_file = "data\processed\dataset_processed.csv"  # Output file name
    
    # Initialize and run the feature builder
    builder = CodeQualityFeatureBuilder(input_file, output_file)
    processed_df = builder.build()
    builder.save()
    
    logger.info(f"\n✓ Feature engineering complete!")
    logger.info(f"✓ Output saved to: {output_file}")
    logger.info(f"✓ Ready for machine learning models")
    
    return processed_df


if __name__ == "__main__":
    df = main()
