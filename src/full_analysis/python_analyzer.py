# metrics_collector/python_analyzer.py
import ast
import tokenize
from io import StringIO
import radon.metrics as radon_metrics
import radon.complexity as radon_complexity
from radon.visitors import ComplexityVisitor
from lizard import analyze_file, FunctionInfo
from base_analyzer import BaseCodeAnalyzer

class PythonAnalyzer(BaseCodeAnalyzer):
    def analyze_file(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        phase1 = self._collect_phase1_metrics(content, file_path)
        phase2 = self._collect_phase2_metrics(content, file_path)
        
        return {**phase1, **phase2}
    
    def _collect_metrics(self, content: str, file_path: str):
        """Collect Phase 1 metrics for Python"""
        try:
            tree = ast.parse(content)
            lizard_analysis = analyze_file.analyze_source_code(file_path, content)

            # Halstead metrics using radon
            halstead = radon_metrics.h_visit(content)
            
            # LCOM (Lack of Cohesion in Methods) approximation
            lcom = self._calculate_lcom(content)
            
            metrics = {
                'function_count': 0,
                'class_count': 0,
                'method_count': 0,
                'function_lengths': [],
                'methods_with_many_params': 0,
                'long_methods': 0,
                'functions_with_docstrings': 0,
                'total_functions': 0,
            }
            
            # Analyze AST for basic structure
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics['function_count'] += 1
                    metrics['total_functions'] += 1
                    
                    # Function length
                    func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                    metrics['function_lengths'].append(func_lines)
                    
                    # Long methods
                    if func_lines > 20:
                        metrics['long_methods'] += 1
                    
                    # Parameters count
                    param_count = len(node.args.args) + len(node.args.kwonlyargs)
                    if param_count > 4:
                        metrics['methods_with_many_params'] += 1
                    
                    # Docstring check
                    if ast.get_docstring(node):
                        metrics['functions_with_docstrings'] += 1
                
                elif isinstance(node, ast.ClassDef):
                    metrics['class_count'] += 1
            
            # Calculate averages
            avg_length = (sum(metrics['function_lengths']) / 
                         len(metrics['function_lengths'])) if metrics['function_lengths'] else 0
            
            # Use lizard for cognitive complexity
            cognitive_complexities = []
            for func in lizard_analysis.function_list:
                cognitive_complexities.append(func.cyclomatic_complexity)
            
            return {
                'function_count': metrics['function_count'],
                'class_count': metrics['class_count'],
                'method_count': metrics['function_count'],  # In Python, methods are functions
                'average_function_length': avg_length,
                'max_function_length': max(metrics['function_lengths']) if metrics['function_lengths'] else 0,
                'docstring_coverage_percent': (metrics['functions_with_docstrings'] / 
                                             metrics['total_functions'] * 100) if metrics['total_functions'] > 0 else 0,
                'duplicate_blocks_count': self._detect_duplicates(content),
                'long_methods_count': metrics['long_methods'],
                'methods_with_many_parameters': metrics['methods_with_many_params'],
                'cognitive_complexity_avg': (sum(cognitive_complexities) / 
                                           len(cognitive_complexities)) if cognitive_complexities else 0,
                'afferent_coupling': self._calculate_afferent_coupling(content),
                
                # Derived
                'functions_over_20_lines': metrics['long_methods'],
                'functions_over_50_lines': len([l for l in metrics['function_lengths'] if l > 50]),
                'halstead_volume': halstead.total.volume,
                'halstead_difficulty': halstead.total.difficulty,
                'halstead_effort': halstead.total.effort,
                'lack_of_cohesion_in_methods': lcom,
                'test_coverage_percentage': self._estimate_test_coverage(file_path),
                'technical_debt_ratio': self._calculate_technical_debt(content),
                'circular_dependencies_count': self._detect_circular_deps(content),
            }

        except Exception as e:
            print(f"Error in phase 2 metrics for {file_path}: {e}")
            return self.collect_metrics()
    
    def _detect_duplicates(self, content: str) -> int:
        """Simple duplicate code detection"""
        lines = content.split('\n')
        code_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        
        # Simple: count identical consecutive lines (basic approach)
        duplicates = 0
        seen = set()
        for line in code_lines:
            if line in seen and len(line) > 10:  # Avoid counting short common lines
                duplicates += 1
            seen.add(line)
        
        return duplicates
    
    def _calculate_afferent_coupling(self, content: str) -> int:
        """Calculate afferent coupling (simplified)"""
        tree = ast.parse(content)
        imports = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports += 1
        
        return imports
    
    def _calculate_lcom(self, content: str) -> float:
        """Calculate Lack of Cohesion in Methods (simplified)"""
        tree = ast.parse(content)
        class_cohesion = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                class_cohesion.append(len(methods))
        
        return sum(class_cohesion) / len(class_cohesion) if class_cohesion else 0
    
    def _estimate_test_coverage(self, file_path: str) -> float:
        """Estimate test coverage based on test file presence"""
        file_dir = Path(file_path).parent
        test_files = list(file_dir.glob('test_*.py')) + list(file_dir.glob('*_test.py'))
        return min(len(test_files) * 20, 100)  # Rough estimate
    
    def _calculate_technical_debt(self, content: str) -> float:
        """Calculate technical debt ratio (simplified)"""
        issues = 0
        lines = content.split('\n')
        
        # Count potential issues
        for line in lines:
            line = line.strip()
            if len(line) > 100:  # Long line
                issues += 1
            if 'TODO' in line or 'FIXME' in line:
                issues += 1
            if 'except:' in line:  # Bare except
                issues += 1
        
        return (issues / len(lines)) * 100 if lines else 0
    
    def _detect_circular_deps(self, content: str) -> int:
        """Detect circular imports (simplified)"""
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Simple circular detection (would need project-wide analysis for real implementation)
        return 0
