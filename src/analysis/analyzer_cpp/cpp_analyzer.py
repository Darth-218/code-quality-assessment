import subprocess, json, xml.etree.ElementTree as ET

def analyze_cpp_code(file_path):
    data = {}

    # --- Cppcheck ---
    cppcheck_xml = "cppcheck_report.xml"
    subprocess.run(["cppcheck", "--enable=all", "--xml", "--xml-version=2", file_path],
                   stderr=open(cppcheck_xml, "w"))
    try:
        tree = ET.parse(cppcheck_xml)
        data["cppcheck"] = [err.attrib for err in tree.findall(".//error")]
    except Exception:
        data["cppcheck"] = []

    # --- Lizard ---
    lizard = subprocess.run(["lizard", "-j", file_path], capture_output=True, text=True)
    try:
        data["lizard"] = json.loads(lizard.stdout)
    except Exception:
        data["lizard"] = []

    # --- Flawfinder ---
    flawfinder = subprocess.run(["flawfinder", "--dataonly", "--singleline", file_path],
                                capture_output=True, text=True)
    data["flawfinder"] = flawfinder.stdout.strip().splitlines()

    return data
