"""
Main code analysis engine that coordinates all analyzers.
"""

import ast
import json
import os
from typing import Dict, Any, List
from .python_analyzer import PythonCodeAnalyzer
from .metrics_extractor import extract_actual_metrics
from .smell_detector import CodeSmellDetector

class CodeAnalysisEngine:
    """Main engine for analyzing Python code."""
    
    def __init__(self):
        self.smell_detector = CodeSmellDetector()
        
    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """
        Analyze a Python file and extract all metrics.
        
        Args:
            filepath: Path to the Python file
            
        Returns:
            Dictionary with all analysis results
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        print(f"🔍 Analyzing: {filepath}")
        
        # 1. Basic code analysis
        analyzer = PythonCodeAnalyzer(filepath)
        basic_metrics = analyzer.analyze()
        
        # 2. Extract actual code metrics (complexity, etc.)
        actual_metrics = extract_actual_metrics(filepath)
        
        # 3. Detect code smells
        smells = self.smell_detector.detect_smells(actual_metrics)
        
        # 4. Combine all results
        analysis_result = {
            "file_info": {
                "filename": os.path.basename(filepath),
                "filepath": os.path.abspath(filepath),
                "file_size_bytes": os.path.getsize(filepath),
                "lines_of_code": basic_metrics["size_metrics"]["LOC"]
            },
            "size_metrics": basic_metrics["size_metrics"],
            "structure_metrics": basic_metrics["structure_metrics"],
            "complexity_metrics": actual_metrics.get("complexity", {}),
            "object_oriented_metrics": actual_metrics.get("oo_metrics", {}),
            "code_smells": smells,
            "quality_assessment": self._assess_quality(actual_metrics, smells)
        }
        
        return analysis_result
    
    def _assess_quality(self, metrics: Dict[str, Any], smells: List[Dict]) -> Dict[str, Any]:
        """Assess code quality based on metrics and smells."""
        quality_score = 100
        
        # Deduct points for issues
        if "cyclomatic" in metrics.get("complexity", {}):
            if metrics["complexity"]["cyclomatic"] > 15:
                quality_score -= 20
            elif metrics["complexity"]["cyclomatic"] > 10:
                quality_score -= 10
        
        if "method_loc" in metrics.get("size", {}):
            if metrics["size"]["method_loc"] > 50:
                quality_score -= 15
        
        if len(smells) > 0:
            quality_score -= len(smells) * 5
        
        # Categorize quality
        if quality_score >= 90:
            quality_label = "Excellent"
        elif quality_score >= 75:
            quality_label = "Good"
        elif quality_score >= 60:
            quality_label = "Fair"
        elif quality_score >= 40:
            quality_label = "Poor"
        else:
            quality_label = "Very Poor"
        
        return {
            "score": max(0, quality_score),
            "label": quality_label,
            "issues_found": len(smells)
        }
    
    def analyze_directory(self, directory: str) -> Dict[str, Any]:
        """
        Analyze all Python files in a directory.
        
        Args:
            directory: Path to directory
            
        Returns:
            Combined analysis results
        """
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        results = {}
        total_files = 0
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        results[filepath] = self.analyze_file(filepath)
                        total_files += 1
                    except Exception as e:
                        print(f"⚠️  Error analyzing {filepath}: {e}")
        
        # Generate summary
        summary = self._generate_summary(results)
        
        return {
            "summary": summary,
            "files_analyzed": total_files,
            "detailed_analysis": results
        }
    
    def _generate_summary(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate summary statistics from analysis results."""
        total_loc = 0
        total_complexity = 0
        total_smells = 0
        quality_scores = []
        
        for file_analysis in results.values():
            total_loc += file_analysis["file_info"]["lines_of_code"]
            total_smells += len(file_analysis["code_smells"])
            quality_scores.append(file_analysis["quality_assessment"]["score"])
            
            if "cyclomatic" in file_analysis.get("complexity_metrics", {}):
                total_complexity += file_analysis["complexity_metrics"]["cyclomatic"]
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "total_files": len(results),
            "total_lines_of_code": total_loc,
            "average_cyclomatic_complexity": total_complexity / len(results) if results else 0,
            "total_code_smells": total_smells,
            "average_quality_score": avg_quality,
            "files_by_quality": {
                "excellent": sum(1 for r in results.values() if r["quality_assessment"]["score"] >= 90),
                "good": sum(1 for r in results.values() if 75 <= r["quality_assessment"]["score"] < 90),
                "fair": sum(1 for r in results.values() if 60 <= r["quality_assessment"]["score"] < 75),
                "poor": sum(1 for r in results.values() if r["quality_assessment"]["score"] < 60)
            }
        }