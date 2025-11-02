import python_analyzer, java_analyzer, cpp_analyzer, metrics_extractor, smell_detector, report_generator
import os
from pathlib import Path

# Get the project root directory (2 levels up from the current script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_DIR = str(PROJECT_ROOT / "data" / "temp")
OUTPUT_DIR = str(PROJECT_ROOT / "data" / "processed" / "analysis_results")


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
    file_path = Path(file_path)
    language = data = ""
    file_name = file_path.name
    repo_name = file_path.parent.name
    if str(file_path).endswith(".py"):
        language = "Python"
        data = python_analyzer.analyze_python_code(file_path)

    elif str(file_path).endswith(".java"):
        language = "Java"
        data = java_analyzer.analyze_java_code(file_path)

    elif str(file_path).endswith(".cpp"):
        language = "C++"
        data = cpp_analyzer.analyze_cpp_code(file_path)

    metrics = metrics_extractor.extract_metrics(data, language)
    report_generator.save_report(f"{repo_name}_{file_name.split(".")[0]}.json", OUTPUT_DIR, metrics)
    print(f"Report saved at {repo_name}_{file_name}")


if __name__ == "__main__":
    analyze_files(INPUT_DIR)
    print("Finished Analysis")
