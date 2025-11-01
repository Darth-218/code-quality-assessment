import subprocess, json

def analyze_python_code(file_path):
    data = {}

    # --- 1️⃣ Pylint (errors, warnings, style, refactor) ---
    pylint_result = subprocess.run(
        ["pylint", file_path, "-f", "json"],
        capture_output=True, text=True
    )
    try:
        data["pylint"] = json.loads(pylint_result.stdout)
    except json.JSONDecodeError:
        data["pylint"] = []

    # --- 2️⃣ Radon (complexity) ---
    radon_cc = subprocess.run(["radon", "cc", "-j", file_path],
                              capture_output=True, text=True)
    data["complexity"] = json.loads(radon_cc.stdout)

    # --- 3️⃣ Radon (maintainability) ---
    radon_mi = subprocess.run(["radon", "mi", "-j", file_path],
                              capture_output=True, text=True)
    data["maintainability"] = json.loads(radon_mi.stdout)

    # --- 4️⃣ Bandit (security) ---
    bandit_result = subprocess.run(
        ["bandit", "-f", "json", "-q", "-r", file_path],
        capture_output=True, text=True
    )
    try:
        data["bandit"] = json.loads(bandit_result.stdout)
    except json.JSONDecodeError:
        data["bandit"] = {"results": []}

    # --- 5️⃣ Vulture (dead code) ---
    vulture_result = subprocess.run(
        ["vulture", file_path, "--min-confidence", "80"],
        capture_output=True, text=True
    )
    data["vulture"] = vulture_result.stdout.strip().splitlines()

    # --- 6️⃣ Count Lines and Comments ---
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    total_lines = len(lines)
    comment_lines = sum(1 for l in lines if l.strip().startswith("#"))
    blank_lines = sum(1 for l in lines if not l.strip())

    data["loc"] = total_lines
    data["comments"] = comment_lines
    data["blank"] = blank_lines

    return data
