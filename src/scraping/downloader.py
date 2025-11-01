import subprocess
import json
from pathlib import Path

class Downloader:
    def __init__(self, repo_list, output_dir) -> None:
        self.repo_list = repo_list
        self.output_dir = output_dir

    def load_repos(self):
        with open(self.repo_list, "r", encoding="utf-8") as f:
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

    def clone_repos(self, repo_url, depth=1):
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        target = Path(self.output_dir) / repo_name
        if target.exists():
            print(f"{repo_name} already exists.")
            return
        cmd = ["git", "clone", "--depth", str(depth), repo_url, str(target)]
        print(" ".join(cmd))
        subprocess.run(cmd, check=False)

