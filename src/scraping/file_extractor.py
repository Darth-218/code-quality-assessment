import os
import shutil
from pathlib import Path

class FileExtractor:

    def __init__(self, repo_dir, output_dir) -> None:
        self.repo_dir = repo_dir
        self.output_dir = output_dir
        self.languages = {
            ".py": "python",
            ".java": "java",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".hpp": "cpp",
            ".h": "cpp",
        }

    def get_repos(self):
        return [p for p in self.repo_dir.iterdir() if p.is_dir()]


    def extract_files(self, repo_path: Path):
        repo_name = str(repo_path).split("/")[-2]
        copied = 0

        for root, _, files in os.walk(repo_path):
            if ".git" in root.split(os.sep):
                continue

            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext in self.languages:
                    lang = self.languages[ext]
                    src_path = Path(root) / fname
                    dest_dir = self.output_dir / repo_name / lang
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    dest_file = dest_dir / fname

                    try:
                        shutil.copy2(src_path, dest_file)
                        copied += 1
                    except Exception:
                        continue
        return copied

