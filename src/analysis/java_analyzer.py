import subprocess, xml.etree.ElementTree as ET

def analyze_java_code(file_path):
    data = {}
    # PMD
    subprocess.run(["pmd", "-d", file_path, "-R", "rulesets/java/quickstart.xml",
                    "-f", "xml", "-r", "pmd_report.xml"])
    try:
        tree = ET.parse("pmd_report.xml")
        data["pmd"] = [v.attrib for v in tree.findall(".//violation")]
    except Exception:
        data["pmd"] = []

    # Checkstyle
    subprocess.run(["checkstyle", "-c", "/google_checks.xml", "-f", "xml", "-o", "checkstyle_report.xml", file_path])
    try:
        tree2 = ET.parse("checkstyle_report.xml")
        data["checkstyle"] = [e.attrib for e in tree2.findall(".//error")]
    except Exception:
        data["checkstyle"] = []

    # SpotBugs
    subprocess.run(["spotbugs", "-textui", "-xml", "-output", "spotbugs_report.xml", file_path])
    try:
        tree3 = ET.parse("spotbugs_report.xml")
        data["spotbugs"] = [b.attrib for b in tree3.findall(".//BugInstance")]
    except Exception:
        data["spotbugs"] = []

    return data
