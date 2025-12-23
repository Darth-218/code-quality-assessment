"""
Module for detecting code smells (optional).
This shows how the taxonomy metrics could be applied.
"""

from typing import List, Dict, Any

class CodeSmellDetector:
    """Detect code smells based on metrics thresholds."""
    
    # Thresholds based on research and best practices
    THRESHOLDS = {
        "cyclomatic_complexity": 15,
        "method_length_loc": 50,
        "class_length_loc": 500,
        "method_parameters": 5,
        "depth_of_inheritance": 6,
        "lack_of_cohesion": 0.8,
        "coupling_between_objects": 10
    }
    
    def detect_smells(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect code smells based on metrics.
        
        Args:
            metrics: Dictionary of code metrics
            
        Returns:
            List of detected code smells
        """
        smells = []
        
        # Check for various code smells
        if "complexity" in metrics:
            smells.extend(self._check_complexity_smells(metrics["complexity"]))
        
        if "size" in metrics:
            smells.extend(self._check_size_smells(metrics["size"]))
        
        if "oo_metrics" in metrics:
            smells.extend(self._check_oo_smells(metrics["oo_metrics"]))
        
        return smells
    
    def _check_complexity_smells(self, complexity_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detect complexity-related smells."""
        smells = []
        
        # Cyclomatic complexity check
        if "cyclomatic" in complexity_metrics:
            if complexity_metrics["cyclomatic"] > self.THRESHOLDS["cyclomatic_complexity"]:
                smells.append({
                    "type": "HighCyclomaticComplexity",
                    "metric": "cyclomatic_complexity",
                    "value": complexity_metrics["cyclomatic"],
                    "threshold": self.THRESHOLDS["cyclomatic_complexity"],
                    "description": "Method is too complex (high cyclomatic complexity)",
                    "severity": "MAJOR"
                })
        
        return smells
    
    def _check_size_smells(self, size_metrics: Dict[str, int]) -> List[Dict[str, Any]]:
        """Detect size-related smells."""
        smells = []
        
        # Long Method smell
        if "method_loc" in size_metrics:
            if size_metrics["method_loc"] > self.THRESHOLDS["method_length_loc"]:
                smells.append({
                    "type": "LongMethod",
                    "metric": "method_length",
                    "value": size_metrics["method_loc"],
                    "threshold": self.THRESHOLDS["method_length_loc"],
                    "description": "Method is too long",
                    "severity": "MINOR"
                })
        
        # Large Class smell
        if "class_loc" in size_metrics:
            if size_metrics["class_loc"] > self.THRESHOLDS["class_length_loc"]:
                smells.append({
                    "type": "LargeClass",
                    "metric": "class_length",
                    "value": size_metrics["class_loc"],
                    "threshold": self.THRESHOLDS["class_length_loc"],
                    "description": "Class is too large",
                    "severity": "MINOR"
                })
        
        return smells
    
    def _check_oo_smells(self, oo_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detect object-oriented smells."""
        smells = []
        
        # Deep Inheritance Tree
        if "dit" in oo_metrics:
            if oo_metrics["dit"] > self.THRESHOLDS["depth_of_inheritance"]:
                smells.append({
                    "type": "DeepInheritanceTree",
                    "metric": "depth_of_inheritance",
                    "value": oo_metrics["dit"],
                    "threshold": self.THRESHOLDS["depth_of_inheritance"],
                    "description": "Inheritance hierarchy is too deep",
                    "severity": "MAJOR"
                })
        
        # High Coupling
        if "cbo" in oo_metrics:
            if oo_metrics["cbo"] > self.THRESHOLDS["coupling_between_objects"]:
                smells.append({
                    "type": "HighCoupling",
                    "metric": "coupling_between_objects",
                    "value": oo_metrics["cbo"],
                    "threshold": self.THRESHOLDS["coupling_between_objects"],
                    "description": "Class is too coupled to other classes",
                    "severity": "MAJOR"
                })
        
        return smells