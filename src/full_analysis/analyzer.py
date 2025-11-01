# main.py
import os
import json
from pathlib import Path
import python_analyzer, cpp_analyzer, java_analyzer

class ComprehensiveMetricsCollector:
    def __init__(self):
        self.analyzers = {
            '.py': python_analyzer.PythonAnalyzer(),
            '.java': java_analyzer.JavaAnalyzer(), 
            '.cpp': cpp_analyzer.CppAnalyzer(),
            '.c': cpp_analyzer.CppAnalyzer(),
            '.h': cpp_analyzer.CppAnalyzer(),
            '.hpp': cpp_analyzer.CppAnalyzer(),
        }
    
    def analyze_project(self, project_path: str):
        """Analyze entire project and collect metrics"""
        project_metrics = {
            'project_path': project_path,
            'files_analyzed': [],
            'summary_metrics': {},
            'file_metrics': {}
        }
        
        total_metrics = {}
        file_count = 0
        
        for root, _, files in os.walk(project_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                if file_ext in self.analyzers:
                    try:
                        print(f"Analyzing: {file_path}")
                        metrics = self.analyzers[file_ext].analyze_file(file_path)
                        
                        project_metrics['files_analyzed'].append(file_path)
                        project_metrics['file_metrics'][file_path] = metrics
                        
                        # Aggregate metrics
                        for key, value in metrics.items():
                            if key not in total_metrics:
                                total_metrics[key] = []
                            total_metrics[key].append(value)
                        
                        file_count += 1
                        
                    except Exception as e:
                        print(f"Error analyzing {file_path}: {e}")
        
        # Calculate summary metrics
        if file_count > 0:
            project_metrics['summary_metrics'] = {
                key: sum(values) / len(values) if isinstance(values[0], (int, float)) else sum(values)
                for key, values in total_metrics.items()
            }
            project_metrics['summary_metrics']['total_files'] = file_count
        
        return project_metrics
    
    def save_metrics(self, metrics, output_path: str):
        """Save metrics to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)

# Usage
if __name__ == "__main__":
    collector = ComprehensiveMetricsCollector()
    
    # Analyze a project
    project_path = "../../data/temp/"
    metrics = collector.analyze_project(project_path)
    
    # Save results
    collector.save_metrics(metrics, "project_metrics.json")
    
    print(f"Analysis complete! Analyzed {len(metrics['files_analyzed'])} files")
    print("Summary metrics:", json.dumps(metrics['summary_metrics'], indent=2))
