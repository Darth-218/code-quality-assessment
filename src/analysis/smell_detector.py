"""
Module for detecting code smells (rule-based weak supervision).
Covers strong, proxy-based, and contextual smells based on available features.
"""

from typing import List, Dict, Any
from venv import logger

SMELL_INDEX = {
    "LongMethod": 0,
    "LargeParameterList": 1,
    "GodClass": 2,
    "LazyClass": 3,
    "SpaghettiCode": 4,
    "PoorDocumentation": 5,
    "MisleadingComments": 6,
    "GlobalStateAbuse": 7,
    "FeatureEnvy": 8,
    "ShotgunSurgery": 9,
    "UntestedCode": 10,
    "FormattingIssues": 11,
    "UnstableModule": 12,
}

class CodeSmellDetector:
    def __init__(self, smell_index: Dict[str, int] = SMELL_INDEX):
        self.smell_index = smell_index
        self.num_labels = len(smell_index)

    # ---------- Binary encoder ----------
    def smells_to_binary(self, smells: List[Dict[str, Any]]) -> List[int]:
        y = [0] * self.num_labels
        for s in smells:
            smell_type = s.get("type")
            if smell_type in self.smell_index:
                y[self.smell_index[smell_type]] = 1
        return y

    # ---------- Smell detection ----------
    def detect_smells_from_summary(self, s: Dict[str, Any]) -> List[Dict[str, Any]]:
        smells: List[Dict[str, Any]] = []

        loc = s.get("lines_of_code", 0)
        has_functions = s.get("functions", 0) > 0
        has_classes = s.get("classes", 0) > 0

        # --- STRONG SMELLS ---

        if has_functions and (
            s.get("max_lines_per_function", 0) > 50 or
            s.get("max_cyclomatic_ratio", 0) > 0.5 or
            s.get("max_nesting_level", 0) > 4
        ):
            smells.append({
                "type": "LongMethod",
                "severity": "MAJOR"
            })

        if has_functions and (
            s.get("large_parameter_list_indicator", False) or
            s.get("mean_param_entropy", 0) > 2.0
        ):
            smells.append({
                "type": "LargeParameterList",
                "severity": "MINOR"
            })

        if has_classes and (
            s.get("average_methods_per_class", 0) < 2 and
            s.get("mean_lines_per_class", 0) < 50
        ):
            smells.append({
                "type": "LazyClass",
                "severity": "MINOR"
            })

        cross_calls = len(s.get("cross_file_call_edges", [])) \
            if isinstance(s.get("cross_file_call_edges", []), list) else 0

        if has_classes and (
            s.get("inter_file_coupling", 0) > 20 or
            cross_calls > 15 or
            s.get("average_cyclomatic_complexity", 0) > 15
        ):
            smells.append({
                "type": "GodClass",
                "severity": "CRITICAL"
            })

        if has_functions and (
            s.get("average_cyclomatic_complexity", 0) > 10 or
            s.get("nesting_variance", 0) > 1.5
        ):
            smells.append({
                "type": "SpaghettiCode",
                "severity": "MAJOR"
            })

        # --- PROXY SMELLS ---

        if loc > 20 and (
            s.get("documentation_coverage", 100) < 20 or
            s.get("comment_percentage", 100) < 5
        ):
            smells.append({
                "type": "PoorDocumentation",
                "severity": "MINOR"
            })

        if s.get("comment_code_mismatch_score", 0) > 0.7:
            smells.append({
                "type": "MisleadingComments",
                "severity": "MINOR"
            })

        if (
            s.get("globals_declared", 0) > 3 or
            s.get("global_usages_total", 0) > 10
        ):
            smells.append({
                "type": "GlobalStateAbuse",
                "severity": "MAJOR"
            })

        if has_functions and (
            s.get("external_vs_internal_field_access_ratio", 0) > 3 or
            cross_calls > 10
        ):
            smells.append({
                "type": "FeatureEnvy",
                "severity": "MINOR"
            })

        if (
            s.get("commit_bursts", 0) > 3 and
            s.get("inter_file_coupling", 0) > 10
        ):
            smells.append({
                "type": "ShotgunSurgery",
                "severity": "MAJOR"
            })

        # --- CONTEXTUAL SMELLS ---

        if (
            s.get("pep8_violations", 0) > 5 or
            s.get("indentation_irregularity", {}).get("irregularity_score", 0) > 1.0
        ):
            smells.append({
                "type": "FormattingIssues",
                "severity": "INFO"
            })

        if loc > 50 and not s.get("unit_test_presence", False):
            smells.append({
                "type": "UntestedCode",
                "severity": "MAJOR"
            })

        if (
            s.get("commit_bursts", 0) > 5 or
            s.get("lines_added", 0) > 500
        ):
            smells.append({
                "type": "UnstableModule",
                "severity": "MINOR"
            })

        return smells

    # ---------- Batch processing ----------
    def detect_smells_in_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        
        for idx, r in enumerate(records):
            rec = dict(r)
            try:
                smells = self.detect_smells_from_summary(rec)
                rec["smells"] = smells
                
                # Get binary vector
                binary_vector = self.smells_to_binary(smells)
                
                # UNPACK: Convert vector to individual label columns
                # y_binary: [0, 1, 0] → y_LongMethod: 0, y_LargeParameterList: 1, y_GodClass: 0
                for smell_name, label_idx in self.smell_index.items():
                    rec[f"y_{smell_name}"] = int(binary_vector[label_idx])
                    
            except Exception as e:
                logger.warning(f"Error processing record {idx}: {e}")
                rec["smells"] = []
                # Error case: all labels set to 0
                for smell_name in self.smell_index.keys():
                    rec[f"y_{smell_name}"] = 0

            results.append(rec)

        return results
