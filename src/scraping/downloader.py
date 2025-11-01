import subprocess
import json
import os
from pathlib import Path

REPO_LIST= "../../data/repo_details/repository_list_scrap_list.json"
OUTPUT_DIR = "../../data/temp/"

def load_repos(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    urls = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "clone_url" in item:
                urls.append(item["clone_url"])
    elif isinstance(data, dict):
        for v in data.values():
            if isinstance(v, dict) and "clone_url" in v:
                urls.append(v["clone_url"])
    return urls

def clone_repos(repo_url, outdir, depth=1):
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    target = Path(outdir) / repo_name
    if target.exists():
        print(f"{repo_name} already exists.")
        return
    cmd = ["git", "clone", "--depth", str(depth), repo_url, str(target)]
    print(" ".join(cmd))
    subprocess.run(cmd, check=False)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    repos = load_repos(REPO_LIST)
    print(f"Found {len(repos)} repositories.")
    for url in repos:
        clone_repos(url, OUTPUT_DIR)

if __name__ == "__main__":
    main()

