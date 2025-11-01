import os
import shutil
from pathlib import Path

CLONED_DIR = "../../data/temp/"
OUTPUT_DIR = "../../data/raw/"
LANG = {
    ".py": "python",
    ".java": "java",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".h": "cpp",
}


def extract_files(repo_path: Path, output_base: Path):
    repo_name = repo_path.name
    copied = 0

    for root, _, files in os.walk(repo_path):
        if ".git" in root.split(os.sep):
            continue

        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext in LANG:
                lang = LANG[ext]
                src_path = Path(root) / fname
                dest_dir = output_base / repo_name / lang
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / fname

                try:
                    shutil.copy2(src_path, dest_file)
                    copied += 1
                except Exception:
                    continue
    return copied


def main():
    cloned_dir = Path(CLONED_DIR)
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    repos = [p for p in cloned_dir.iterdir() if p.is_dir()]
    print(f"Found {len(repos)} repos to process.")

    total = 0
    for repo in repos:
        n = extract_files(repo, output_dir)
        total += n
        print(f"{repo.name}: {n} files copied.")
    print(f"Total files copied: {total}")


if __name__ == "__main__":
    main()

