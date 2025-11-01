import os
import ast
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pathlib import Path

class BaseCodeAnalyzer(ABC):
    def __init__(self):
        self.metrics = {}
    
    @abstractmethod
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        pass
    
    def collect_metrics(self) -> Dict[str, Any]:
        return {
            'function_count': 0,
            'class_count': 0,
            'method_count': 0,
            'average_function_length': 0.0,
            'max_function_length': 0,
            'docstring_coverage_percent': 0.0,
            'duplicate_blocks_count': 0,
            'long_methods_count': 0,
            'methods_with_many_parameters': 0,
            'cognitive_complexity_avg': 0.0,
            'afferent_coupling': 0,
            
            'functions_over_20_lines': 0,
            'functions_over_50_lines': 0,
            'halstead_volume': 0.0,
            'halstead_difficulty': 0.0,
            'halstead_effort': 0.0,
            'lack_of_cohesion_in_methods': 0.0,
            'test_coverage_percentage': 0.0,
            'technical_debt_ratio': 0.0,
            'circular_dependencies_count': 0,
        }
