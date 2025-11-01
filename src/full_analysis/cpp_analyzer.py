import re
from base_analyzer import BaseCodeAnalyzer

class CppAnalyzer(BaseCodeAnalyzer):
    def analyze_file(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        phase = self._collect_metrics(content, file_path)
        
        return phase
    
    def _collect_metrics(self, content: str, file_path: str):
        """Collect Phase 1 metrics for C++"""
        clean_content = self._remove_comments(content)
        
        metrics = {
            'function_count': 0,
            'class_count': 0,
            'method_count': 0,
            'function_lengths': [],
            'functions_with_many_params': 0,
            'long_functions': 0,
            'functions_with_comments': 0,
            'total_functions': 0,
        }
        
        # Count classes/structs
        class_pattern = r'(class|struct)\s+(\w+)'
        metrics['class_count'] = len(re.findall(class_pattern, clean_content))
        
        # Function detection
        function_pattern = r'(\w+)\s+(\w+)\s*\(([^)]*)\)\s*\{'
        functions = re.findall(function_pattern, clean_content)
        metrics['function_count'] = len(functions)
        metrics['total_functions'] = len(functions)
        
        # Function length estimation
        brace_count = 0
        current_func_start = 0
        in_function = False
        
        lines = clean_content.split('\n')
        for i, line in enumerate(lines):
            if re.search(function_pattern, line) and not in_function:
                in_function = True
                current_func_start = i
                brace_count = 0
            
            brace_count += line.count('{') - line.count('}')
            
            if in_function and brace_count == 0 and i > current_func_start:
                func_length = i - current_func_start
                metrics['function_lengths'].append(func_length)
                
                if func_length > 20:
                    metrics['long_functions'] += 1
                
                # Check parameters
                param_match = re.search(r'\(([^)]*)\)', lines[current_func_start])
                if param_match:
                    params = [p.strip() for p in param_match.group(1).split(',') if p.strip()]
                    if len(params) > 4:
                        metrics['functions_with_many_params'] += 1
                
                # Check for comments in original content
                original_lines = content.split('\n')
                comment_found = False
                for j in range(max(0, current_func_start-3), current_func_start):
                    if j < len(original_lines) and ('//' in original_lines[j] or '/*' in original_lines[j]):
                        comment_found = True
                        break
                if comment_found:
                    metrics['functions_with_comments'] += 1
                
                in_function = False
        
        avg_length = (sum(metrics['function_lengths']) / 
                     len(metrics['function_lengths'])) if metrics['function_lengths'] else 0
        
        return {
            'function_count': metrics['function_count'],
            'class_count': metrics['class_count'],
            'method_count': metrics['function_count'],  # In C++, methods are member functions
            'average_function_length': avg_length,
            'max_function_length': max(metrics['function_lengths']) if metrics['function_lengths'] else 0,
            'docstring_coverage_percent': (metrics['functions_with_comments'] / 
                                         metrics['total_functions'] * 100) if metrics['total_functions'] > 0 else 0,
            'duplicate_blocks_count': self._detect_duplicates(content),
            'long_methods_count': metrics['long_functions'],
            'methods_with_many_parameters': metrics['functions_with_many_params'],
            'cognitive_complexity_avg': self._estimate_cognitive_complexity(content),
            'afferent_coupling': self._calculate_afferent_coupling(content),
            
            # Derived
            'functions_over_20_lines': metrics['long_functions'],
            'functions_over_50_lines': len([l for l in metrics['function_lengths'] if l > 50]),
        }
    
    def _remove_comments(self, content: str) -> str:
        """Remove C++ comments from content"""
        # Remove single-line comments
        content = re.sub(r'//.*', '', content)
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return content
