import os
from pathlib import Path
import argparse
import shutil

class FileExtractor:

    def __init__(self, repo_dir, output_dir=None) -> None:
        self.repo_dir = Path(repo_dir)
        self.output_dir = Path(output_dir) if output_dir is not None else None
        self.languages = {
            ".py": "python",
            ".java": "java",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".hpp": "cpp",
            ".h": "cpp",
        }
        self._git_names = {".git", ".gitignore", ".gitattributes", ".gitmodules"}

    def get_repos(self):
        """Return subdirectories in the configured repo directory."""
        return [p for p in self.repo_dir.iterdir() if p.is_dir()]

    def list_all_files(self, repo_path: Path):
        """Return all files under repo_path (excluding .git directory)."""
        files = []
        # avoid descending into .git by pruning dirs in topdown walk
        for root, dirs, filenames in os.walk(repo_path, topdown=True):
            # remove .git from dirs to avoid walking into it
            dirs[:] = [d for d in dirs if d != '.git']
            for fname in filenames:
                files.append(Path(root) / fname)
        return files

    def prune_repo(self, repo_path: Path, execute: bool = False, remove_empty_dirs: bool = True):
        """Delete all files in repo_path except files with extensions in self.languages.

        - execute=False performs a dry run and returns what would be deleted
        - execute=True performs the deletions (destructive)
        - .git and git-related files/folders are ignored and left untouched
        Returns a dict with counts and lists of files/dirs affected.
        """
        to_delete = []
        kept = []
        git_related = []

        # First pass: topdown traversal, avoid walking into .git by pruning dirs
        for root, dirs, files in os.walk(repo_path, topdown=True):
            dirs[:] = [d for d in dirs if d != '.git']

            for fname in files:
                path = Path(root) / fname
                # skip git-related files like .gitignore
                if fname in self._git_names or fname.startswith('.git'):
                    git_related.append(str(path))
                    continue

                ext = path.suffix.lower()
                if ext in self.languages:
                    kept.append(str(path))
                    continue

                to_delete.append(str(path))

        # Second pass: if executing, perform deletions and remove empty dirs bottom-up
        result = {
            "repo": str(repo_path),
            "files_kept": len(kept),
            "files_marked_for_deletion": len(to_delete),
            "kept_examples": kept[:20],
            "to_delete_examples": to_delete[:20],
            "git_related_ignored": git_related[:20]
        }

        if execute:
            deleted = 0
            for f in to_delete:
                try:
                    Path(f).unlink()
                    deleted += 1
                except Exception:
                    print(f"Failed to delete {f}")

            # remove empty dirs (bottom-up) but never remove directories that contain a .git child
            dirs_removed = 0
            for root, dirs, files in os.walk(repo_path, topdown=False):
                # ensure we never operate inside .git
                if any(part == '.git' for part in Path(root).parts):
                    continue
                try:
                    # if directory is empty or contains only files that were removed, and does not contain a .git subdir, remove it
                    if not os.listdir(root):
                        os.rmdir(root)
                        dirs_removed += 1
                except Exception:
                    pass

            result["files_deleted"] = deleted
            result["dirs_removed"] = dirs_removed

        return result
    def extract_to_run_dir(self, repo_path: Path):
        repo_name = repo_path.name
        target_repo_dir = self.output_dir / repo_name
        target_repo_dir.mkdir(parents=True, exist_ok=True)

        kept_files = []
        all_files = []

        for root, _, files in os.walk(repo_path):
            if ".git" in root:
                continue

            for file in files:
                src_path = Path(root) / file
                all_files.append(str(src_path))
                if src_path.suffix.lower() not in self.languages:
                    continue

                relative_path = src_path.relative_to(repo_path)
                dest_path = target_repo_dir / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(src_path, dest_path)
                kept_files.append(str(dest_path))

        files_marked_for_deletion = [f for f in all_files if f not in kept_files]

        return {
            "repo": repo_name,
            "files_kept": len(kept_files),
            "files_marked_for_deletion": len(files_marked_for_deletion),
            "kept_examples": kept_files[:20],
            "output_dir": str(target_repo_dir)
        }

    

if __name__ == "__main__":
    fe = FileExtractor("data/temp/")
    repos = fe.get_repos()
    for repo in repos:
        print(f"Processing repo: {repo}")
        res = fe.prune_repo(repo, execute=True, remove_empty_dirs=True)
        print(res)
