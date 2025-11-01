def detect_smells(metrics, language):
    smells = []
    if metrics["avg_complexity"] > 10:
        smells.append("High Complexity")
    if metrics["warning_count"] > 10:
        smells.append("Too Many Warnings")
    if metrics["security_high"] > 0:
        smells.append("Security Issues Found")
    if metrics["comment_density"] < 0.1:
        smells.append("Poor Documentation")
    return smells
