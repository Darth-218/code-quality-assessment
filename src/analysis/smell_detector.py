def detect_smells(metrics):
    smells = []
    if metrics["avg_complexity"] > 10:
        smells.append("High Complexity")
    if metrics["maintainability_index"] < 65:
        smells.append("Low Maintainability")
    if metrics["warning_count"] > 15:
        smells.append("Too Many Warnings")
    if metrics["security_high"] > 0:
        smells.append("High-Risk Security Issue")
    if metrics["dead_code"] > 0:
        smells.append("Dead Code Found")
    if metrics["comment_density"] < 0.1:
        smells.append("Poor Documentation")
    return smells
