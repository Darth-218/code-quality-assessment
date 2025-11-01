import python_analyzer, java_analyzer, cpp_analyzer, metrics_extractor, smell_detector, report_generator
import os
from pathlib import Path

INPUT_DIR = "../../data/temp/"
OUTPUT_DIR = "../../data/processed/analysis_results/"


def analyze_files(base_dir: str):
    files = []
    for root, _, filenames in os.walk(base_dir):
        for f in filenames:
            if not f.endswith((".py", ".cpp", ".java")):
                continue
            analyze_file(os.path.join(root, f))
            files.append(str(Path(root) / f))
    return True

def analyze_file(file_path):
    print(file_path)
    language = data = ""
    file_name = file_path.split("/")[-1]
    repo_name = file_path.split("/")[-2]
    if file_path.endswith(".py"):
        language = "Python"
        data = python_analyzer.analyze_python_code(file_path)

    elif file_path.endswith(".java"):
        language = "Java"
        data = java_analyzer.analyze_java_code(file_path)

    elif file_path.endswith(".cpp"):
        language = "C++"
        data = cpp_analyzer.analyze_cpp_code(file_path)

    metrics = metrics_extractor.extract_metrics(data, language)
    report_generator.save_report(f"{repo_name}_{file_name}", OUTPUT_DIR, metrics)
    print(f"Report saved at {repo_name}_{file_name}")


if __name__ == "__main__":
    analyze_files(INPUT_DIR)
    print("Finished Analysis")
