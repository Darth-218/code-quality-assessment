def extract_metrics(data, language):
    # process metrics based on language type
    metrics = {}
    if language == "Python":
        # Example: extract Python metrics
        metrics = {
            "error_count": len(data.get("errors", [])),
            "warning_count": len(data.get("warnings", [])),
            "avg_complexity": data.get("avg_complexity", 0),
            "max_complexity": data.get("max_complexity", 0),
            "maintainability_index": data.get("maintainability_index", 75.0),
            "security_high": data.get("security_high", 0),
            "security_medium": data.get("security_medium", 0),
            "security_low": data.get("security_low", 0),
            "loc": data.get("loc", 0),
            "comments": data.get("comments", 0),
            "blank_lines": data.get("blank_lines", 0),
            "comment_density": data.get("comment_density", 0.0),
        }

    elif language == "C++":
        # Example: extract C++ metrics
        metrics = {
            "error_count": data.get("error_count", 0),
            "warning_count": data.get("warning_count", 0),
            "avg_complexity": data.get("avg_complexity", 0),
            "max_complexity": data.get("max_complexity", 0),
            "maintainability_index": data.get("maintainability_index", 75.0),
            "security_high": data.get("security_high", 0),
            "security_medium": data.get("security_medium", 0),
            "security_low": data.get("security_low", 0),
            "loc": data.get("loc", 0),
            "comments": data.get("comments", 0),
            "blank_lines": data.get("blank_lines", 0),
            "comment_density": data.get("comment_density", 0.0),
        }

    elif language == "Java":
        # Example: extract Java metrics
        metrics = {
            "error_count": data.get("error_count", 0),
            "warning_count": data.get("warning_count", 0),
            "avg_complexity": data.get("avg_complexity", 0),
            "max_complexity": data.get("max_complexity", 0),
            "maintainability_index": data.get("maintainability_index", 75.0),
            "security_high": data.get("security_high", 0),
            "security_medium": data.get("security_medium", 0),
            "security_low": data.get("security_low", 0),
            "loc": data.get("loc", 0),
            "comments": data.get("comments", 0),
            "blank_lines": data.get("blank_lines", 0),
            "comment_density": data.get("comment_density", 0.0),
        }

    return metrics
