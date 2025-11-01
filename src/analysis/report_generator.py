import json
def save_report(filename, output_dir, data):
    with open(output_dir + filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Report saved: {filename}")
