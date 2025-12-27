import json
import os
from pathlib import Path

from .python_analyzer import PythonCodeAnalyzer
from .smell_detector import CodeSmellDetector

class Analyzer:
    def analyzing(self, input_dir: Path, output_dir: Path):
        # Determine data/temp relative to repository root
        project_root = Path(__file__).resolve().parents[2]
        data_dir = Path(input_dir)

        if not data_dir.exists():
            print(f"Data directory not found: {data_dir}")
            return

        results = []
        total = 0
        errors = 0

        for root, _, files in os.walk(data_dir):
            for fname in files:
                if not fname.lower().endswith('.py'):
                    continue
                fp = Path(root) / fname
                total += 1
                try:
                    analyzer = PythonCodeAnalyzer(str(fp))
                    metrics = analyzer.analyze()
                    # use numerical_summary when available, otherwise full metrics
                    m = metrics.get('numerical_summary', metrics)
                    # remove file_info (do not output file paths)
                    if isinstance(m, dict) and 'file_info' in m:
                        m = dict(m)  # shallow copy
                        m.pop('file_info', None)
                    results.append(m)
                    print(f"Analyzed: {fp.name}")
                except Exception as e:
                    errors += 1
                    print(f"Failed to analyze {fp.name}: {e}")

        # Prepare aggregated results
        summary = {
            'scanned_files': total,
            'errors': errors,
            'results': results
        }

        # Print summary to stdout for visibility
        print(json.dumps(summary, indent=2))

        # Save only the results list to data/raw/data.json (JSON array suitable for CSV conversion)
        out_dir = Path(output_dir)
        out_path = out_dir / 'data.json'
        try:
            with open(out_path, 'w', encoding='utf-8') as fh:
                json.dump(results, fh, indent=2, sort_keys=True)
            print(f"Wrote results array to {out_path}")
        except Exception as e:
            print(f"Failed to write output file {out_path}: {e}")

        return results

    def labeling(self, data, output_dir=Path('data/raw')):
        # Run smell detector over the results and save an annotated copy
        try:
            detector = CodeSmellDetector()
            annotated = detector.detect_smells_in_records(data)
            annotated_path = output_dir / 'data_with_labels.json'
            with open(annotated_path, 'w', encoding='utf-8') as fh:
                json.dump(annotated, fh, indent=2, sort_keys=True)
            print(f"Wrote annotated results with labels to {annotated_path}")
        except Exception as e:
            print(f"Label detection failed: {e}")


if __name__ == "__main__":
    analyzer = Analyzer()
    with open("data/raw/data.json", 'r') as f:
        results = json.load(f)
    analyzer.labeling(data=results)