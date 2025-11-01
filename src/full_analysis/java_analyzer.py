import re
from base_analyzer import BaseCodeAnalyzer

class JavaAnalyzer(BaseCodeAnalyzer):
    def analyze_file(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        phase = self._collect_metrics(content, file_path)
        
        return phase
    
    def _collect_metrics(self, content: str, file_path: str):
        """Collect Phase 1 metrics for Java"""
        metrics = {
            'function_count': 0,
            'class_count': 0,
            'method_count': 0,
            'method_lengths': [],
            'methods_with_many_params': 0,
            'long_methods': 0,
            'methods_with_docstrings': 0,
            'total_methods': 0,
        }
        
        # Count classes
        class_pattern = r'(public|private|protected)?\s*(class|interface|enum)\s+(\w+)'
        metrics['class_count'] = len(re.findall(class_pattern, content))
        
        # Method detection
        method_pattern = r'(public|private|protected|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\) *\{'
        methods = re.findall(method_pattern, content)
        metrics['method_count'] = len(methods)
        metrics['total_methods'] = len(methods)
        
        # Method length estimation (simplified)
        brace_count = 0
        current_method_start = 0
        in_method = False
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if re.search(method_pattern, line) and not in_method:
                in_method = True
                current_method_start = i
                brace_count = 0
            
            brace_count += line.count('{') - line.count('}')
            
            if in_method and brace_count == 0 and i > current_method_start:
                method_length = i - current_method_start
                metrics['method_lengths'].append(method_length)
                
                if method_length > 20:
                    metrics['long_methods'] += 1
                
                # Check parameters
                param_match = re.search(r'\(([^)]*)\)', lines[current_method_start])
                if param_match:
                    params = param_match.group(1).split(',')
                    if len(params) > 4 and params[0].strip():
                        metrics['methods_with_many_params'] += 1
                
                # Check for javadoc
                doc_found = False
                for j in range(max(0, current_method_start-5), current_method_start):
                    if '/**' in lines[j]:
                        doc_found = True
                        break
                if doc_found:
                    metrics['methods_with_docstrings'] += 1
                
                in_method = False
        
        avg_length = (sum(metrics['method_lengths']) / 
                     len(metrics['method_lengths'])) if metrics['method_lengths'] else 0
        
        return {
            'function_count': metrics['method_count'],  # In Java, methods are functions
            'class_count': metrics['class_count'],
            'method_count': metrics['method_count'],
            'average_function_length': avg_length,
            'max_function_length': max(metrics['method_lengths']) if metrics['method_lengths'] else 0,
            'docstring_coverage_percent': (metrics['methods_with_docstrings'] / 
                                         metrics['total_methods'] * 100) if metrics['total_methods'] > 0 else 0,
            'duplicate_blocks_count': self._detect_duplicates(content),
            'long_methods_count': metrics['long_methods'],
            'methods_with_many_parameters': metrics['methods_with_many_params'],
            'cognitive_complexity_avg': self._estimate_cognitive_complexity(content),
            'afferent_coupling': self._calculate_afferent_coupling(content),
            
            # Derived
            'functions_over_20_lines': metrics['long_methods'],
            'functions_over_50_lines': len([l for l in metrics['method_lengths'] if l > 50]),

            'halstead_volume': self._calculate_halstead_volume(content),
            'halstead_difficulty': self._calculate_halstead_difficulty(content),
            'halstead_effort': self._calculate_halstead_effort(content),
            'lack_of_cohesion_in_methods': self._calculate_lcom(content),
            'test_coverage_percentage': self._estimate_test_coverage(file_path),
            'technical_debt_ratio': self._calculate_technical_debt(content),
            'circular_dependencies_count': 0,  # Would need full project analysis
        }
    
    def _estimate_cognitive_complexity(self, content: str) -> float:
        """Estimate cognitive complexity for Java"""
        complexity_indicators = 0
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Count control flow statements
            if any(keyword in line for keyword in ['if', 'for', 'while', 'switch', 'case', 'catch']):
                complexity_indicators += 1
            # Nested conditions
            if line.count('&&') + line.count('||') > 1:
                complexity_indicators += 1
        
        return complexity_indicators / len(lines) * 10 if lines else 0
    
    def _calculate_afferent_coupling(self, content: str) -> int:
        """Calculate afferent coupling for Java"""
        import_pattern = r'import\s+(?:static\s+)?([\w\.]+)'
        imports = re.findall(import_pattern, content)
        return len(imports)
    
    def _detect_duplicates(self, content: str) -> int:
        """Simple duplicate detection for Java"""
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('//')]
        duplicates = 0
        seen = set()
        
        for line in lines:
            if line in seen and len(line) > 10:
                duplicates += 1
            seen.add(line)
        
        return duplicates
    
    def _calculate_halstead_volume(self, content: str) -> float:
        """Simplified Halstead volume calculation"""
        operators = set(re.findall(r'[+\-*/%=<>!&|^~]+', content))
        operands = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content))
        
        n1 = len(operators)  # Distinct operators
        n2 = len(operands)   # Distinct operands
        N1 = len(re.findall(r'[+\-*/%=<>!&|^~]+', content))  # Total operators
        N2 = len(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content))  # Total operands
        
        if n1 + n2 == 0:
            return 0
        
        return (N1 + N2) * (math.log(n1 + n2) / math.log(2)) if (n1 + n2) > 0 else 0
