def extract_cpp_metrics(data):
    cppcheck_data = data.get("cppcheck", [])
    lizard_data = data.get("lizard", [])
    flawfinder_data = data.get("flawfinder", [])

    # --- Cppcheck counts ---
    errors = len([m for m in cppcheck_data if m.get("severity") == "error"])
    warnings = len([m for m in cppcheck_data if m.get("severity") == "warning"])

    # --- Complexity ---
    avg_complexity = 0
    max_complexity = 0
    loc = 0
    if lizard_data:
        functions = lizard_data[0].get("functions", [])
        complexities = [f["cyclomatic_complexity"] for f in functions]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        max_complexity = max(complexities) if complexities else 0
        loc = lizard_data[0].get("nloc", 0)

    # --- Security ---
    security_issues = len(flawfinder_data)

    return {
        "error_count": errors,
        "warning_count": warnings,
        "avg_complexity": avg_complexity,
        "max_complexity": max_complexity,
        "loc": loc,
        "security_issues": security_issues
    }
