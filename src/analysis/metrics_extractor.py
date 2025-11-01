def extract_metrics(data):
    pylint_data = data["pylint"]
    bandit_data = data["bandit"]
    complexity_data = data["complexity"]
    maintainability_data = data["maintainability"]

    # --- Pylint counts ---
    errors = len([x for x in pylint_data if x.get("type") == "error"])
    warnings = len([x for x in pylint_data if x.get("type") == "warning"])
    refactors = len([x for x in pylint_data if x.get("type") == "refactor"])
    conventions = len([x for x in pylint_data if x.get("type") == "convention"])

    # --- Complexity metrics ---
    complexities = []
    for file_data in complexity_data.values():
        for item in file_data:
            complexities.append(item.get("complexity", 0))
    avg_complexity = sum(complexities) / len(complexities) if complexities else 0
    max_complexity = max(complexities) if complexities else 0

    # --- Maintainability index (Radon output fix) ---
    mi_values = []
    for file, entries in maintainability_data.items():
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and "mi" in entry:
                    mi_values.append(entry["mi"])
        elif isinstance(entries, (int, float)):
            mi_values.append(entries)

    avg_mi = sum(mi_values) / len(mi_values) if mi_values else 100

    # --- Bandit Security ---
    results = bandit_data.get("results", [])
    high = sum(1 for r in results if r.get("issue_severity") == "HIGH")
    medium = sum(1 for r in results if r.get("issue_severity") == "MEDIUM")
    low = sum(1 for r in results if r.get("issue_severity") == "LOW")

    # --- Dead code (if Vulture data present) ---
    dead_code = len(data.get("vulture", []))

    # --- Line & comment metrics ---
    loc = data.get("loc", 0)
    comments = data.get("comments", 0)
    blank = data.get("blank", 0)
    comment_density = comments / loc if loc > 0 else 0

    return {
        "error_count": errors,
        "warning_count": warnings,
        "refactor_count": refactors,
        "convention_count": conventions,
        "avg_complexity": avg_complexity,
        "max_complexity": max_complexity,
        "maintainability_index": avg_mi,
        "security_high": high,
        "security_medium": medium,
        "security_low": low,
        "dead_code": dead_code,
        "loc": loc,
        "comments": comments,
        "blank_lines": blank,
        "comment_density": round(comment_density, 3)
    }
