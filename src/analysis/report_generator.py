import json

def save_report(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Report saved to {file_path}")
