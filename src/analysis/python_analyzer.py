"""
Module for analyzing Python code files - UPDATED with numerical metrics extraction.
"""

import ast
import os
from typing import Dict, Any, List

class PythonCodeAnalyzer:
    """Analyzer for Python source code files."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tree = None
        self.content = ""
        self.lines = []
        
    def analyze(self) -> Dict[str, Any]:
        """Analyze the Python file and extract ALL metrics."""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            self.content = f.read()
        
        self.lines = self.content.split('\n')
        self.tree = ast.parse(self.content)
        
        # Extract ALL metrics
        self.metrics = {
            "file_info": self._get_file_info(),
            "size_metrics": self._get_size_metrics(),
            "structure_metrics": self._get_structure_metrics(),
            "complexity_metrics": self._get_complexity_metrics(),
            "function_metrics": self._get_function_metrics(),
            "class_metrics": self._get_class_metrics(),
            "import_analysis": self._get_import_analysis(),
            "documentation_metrics": self._get_documentation_metrics(),
            "object_oriented_metrics": self._get_object_oriented_metrics(),
            "numerical_summary": self._get_numerical_summary()
        }
        
        return self.metrics
    
    def _get_file_info(self) -> Dict[str, Any]:
        return {
            "filename": os.path.basename(self.filepath),
            "file_size_bytes": os.path.getsize(self.filepath),
            "encoding": "utf-8"
        }
    
    def _get_size_metrics(self) -> Dict[str, int]:
        total_lines = len(self.lines)
        
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        docstring_lines = 0
        
        in_docstring = False
        
        for line in self.lines:
            stripped = line.strip()
            
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
                if in_docstring:
                    docstring_lines += 1
                continue
            
            if in_docstring:
                docstring_lines += 1
            elif stripped == '':
                blank_lines += 1
            elif stripped.startswith('#'):
                comment_lines += 1
            else:
                code_lines += 1
        
        return {
            "LOC": total_lines,
            "SLOC": code_lines,
            "CLOC": comment_lines,
            "DLOC": docstring_lines,
            "blank_lines": blank_lines,
            "comment_density": comment_lines / total_lines if total_lines > 0 else 0
        }
    
    def _get_complexity_metrics(self) -> Dict[str, Any]:
        # Calculate complexity metrics
        max_nesting = 0
        current_nesting = 0
        total_decisions = 0
        
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                total_decisions += 1
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                current_nesting = 0
        
        estimated_cyclomatic = total_decisions + 1
        
        return {
            "max_nesting_level": max_nesting,
            "total_control_structures": total_decisions,
            "estimated_cyclomatic_complexity": estimated_cyclomatic,
            "average_cyclomatic_per_function": estimated_cyclomatic / max(1, self._get_structure_metrics()["functions"])
        }
    
    def _get_structure_metrics(self) -> Dict[str, int]:
        class_count = 0
        function_count = 0
        async_function_count = 0
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                class_count += 1
            elif isinstance(node, ast.FunctionDef):
                function_count += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                async_function_count += 1
        
        return {
            "classes": class_count,
            "functions": function_count,
            "async_functions": async_function_count,
            "total_elements": class_count + function_count + async_function_count
        }
    
    def _get_function_metrics(self) -> List[Dict[str, Any]]:
        functions = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = {
                    "name": node.name,
                    "args_count": len(node.args.args),
                    "default_args": len(node.args.defaults),
                    "lineno": node.lineno,
                    "has_decorators": len(node.decorator_list) > 0,
                    "has_docstring": ast.get_docstring(node) is not None,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "is_method": any(isinstance(parent, ast.ClassDef) for parent in ast.iter_child_nodes(self.tree))
                }
                functions.append(func_info)
        
        return functions
    
    def _get_class_metrics(self) -> Dict[str, Any]:
        classes = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                # Count methods in class
                methods = sum(1 for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))
                attributes = sum(1 for item in node.body if isinstance(item, ast.Assign))
                
                class_info = {
                    "name": node.name,
                    "methods": methods,
                    "attributes": attributes,
                    "has_inheritance": len(node.bases) > 0,
                    "has_docstring": ast.get_docstring(node) is not None,
                    "line_count": 0
                }
                
                if hasattr(node, 'end_lineno'):
                    class_info["line_count"] = node.end_lineno - node.lineno
                
                classes.append(class_info)
        
        if not classes:
            return {"total_classes": 0}
        
        return {
            "total_classes": len(classes),
            "classes": classes,
            "average_methods_per_class": sum(c["methods"] for c in classes) / len(classes),
            "classes_with_inheritance": sum(1 for c in classes if c["has_inheritance"]),
            "classes_with_docstrings": sum(1 for c in classes if c["has_docstring"])
        }
    
    def _get_import_analysis(self) -> Dict[str, Any]:
        imports = []
        import_froms = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    import_froms.append(f"{module}.{alias.name}")
        
        return {
            "imports": imports,
            "import_froms": import_froms,
            "total_imports": len(imports) + len(import_froms)
        }
    
    def _get_documentation_metrics(self) -> Dict[str, Any]:
        """Analyze documentation quality."""
        function_with_docstring = 0
        class_with_docstring = 0
        total_functions = 0
        total_classes = 0
        
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_functions += 1
                if ast.get_docstring(node):
                    function_with_docstring += 1
            elif isinstance(node, ast.ClassDef):
                total_classes += 1
                if ast.get_docstring(node):
                    class_with_docstring += 1
        
        total_elements = total_functions + total_classes
        documented_elements = function_with_docstring + class_with_docstring
        
        return {
            "functions_with_docstrings": function_with_docstring,
            "classes_with_docstrings": class_with_docstring,
            "total_documented_elements": documented_elements,
            "documentation_coverage": documented_elements / max(1, total_elements)
        }
    
    def _get_object_oriented_metrics(self) -> Dict[str, Any]:
        """Extract object-oriented metrics."""
        classes = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                methods = sum(1 for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))
                has_inheritance = len(node.bases) > 0
                
                classes.append({
                    "name": node.name,
                    "methods": methods,
                    "has_inheritance": has_inheritance,
                    "inheritance_depth": 1 if has_inheritance else 0
                })
        
        if not classes:
            return {
                "total_classes": 0,
                "average_methods_per_class": 0,
                "classes_with_inheritance": 0,
                "average_inheritance_depth": 0
            }
        
        return {
            "total_classes": len(classes),
            "total_methods": sum(c["methods"] for c in classes),
            "average_methods_per_class": sum(c["methods"] for c in classes) / len(classes),
            "classes_with_inheritance": sum(1 for c in classes if c["has_inheritance"]),
            "average_inheritance_depth": sum(c["inheritance_depth"] for c in classes) / len(classes),
            "max_methods_in_class": max((c["methods"] for c in classes), default=0)
        }
    
    def _get_numerical_summary(self) -> Dict[str, Any]:
        """Generate numerical summary of all metrics."""
        size = self._get_size_metrics()
        structure = self._get_structure_metrics()
        complexity = self._get_complexity_metrics()
        oo_metrics = self._get_object_oriented_metrics()
        doc_metrics = self._get_documentation_metrics()
        imports = self._get_import_analysis()
        
        return {
            "lines_of_code": size["LOC"],
            "source_lines": size["SLOC"],
            "comment_lines": size["CLOC"],
            "comment_percentage": round(size["comment_density"] * 100, 1),
            "classes": structure["classes"],
            "functions": structure["functions"],
            "methods": oo_metrics.get("total_methods", 0),
            "average_cyclomatic_complexity": round(complexity["average_cyclomatic_per_function"], 2),
            "max_nesting_level": complexity["max_nesting_level"],
            "average_methods_per_class": round(oo_metrics.get("average_methods_per_class", 0), 2),
            "classes_with_inheritance": oo_metrics.get("classes_with_inheritance", 0),
            "documentation_coverage": round(doc_metrics["documentation_coverage"] * 100, 1),
            "total_imports": imports["total_imports"],
            "maintainability_score": self._calculate_maintainability_score()
        }
    
    def _calculate_maintainability_score(self) -> float:
        """Calculate a simple maintainability score (0-100)."""
        score = 100
        
        # Adjust based on various factors
        size = self._get_size_metrics()
        complexity = self._get_complexity_metrics()
        doc_metrics = self._get_documentation_metrics()
        
        # Size penalty
        if size["LOC"] > 200:
            score -= 20
        elif size["LOC"] > 100:
            score -= 10
        
        # Complexity penalty
        if complexity["estimated_cyclomatic_complexity"] > 20:
            score -= 20
        elif complexity["estimated_cyclomatic_complexity"] > 10:
            score -= 10
        
        # Documentation bonus/penalty
        if doc_metrics["documentation_coverage"] > 0.8:
            score += 10
        elif doc_metrics["documentation_coverage"] < 0.3:
            score -= 15
        
        return max(0, min(100, round(score, 1)))