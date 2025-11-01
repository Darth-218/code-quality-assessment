def detect_cpp_smells(metrics):
    smells = []
    if metrics["avg_complexity"] > 10:
        smells.append("High Complexity")
    if metrics["warning_count"] > 10:
        smells.append("Too Many Warnings")
    if metrics["security_issues"] > 0:
        smells.append("Security Issues Found")
    if metrics["loc"] > 1000:
        smells.append("Large File Size")
    return smells
