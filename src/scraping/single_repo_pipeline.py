from pathlib import Path
from src.scraping.downloader import Downloader
from src.scraping.file_extractor import FileExtractor
import shutil

def run_repository_pipeline(repo_url: str):
    temp_dir = Path("data/temp")
    run_dir = Path("run")

    temp_dir.mkdir(exist_ok=True)
    run_dir.mkdir(exist_ok=True)

    # Clone repo
    dw = Downloader(None, temp_dir)
    dw.clone_repos(repo_url)

    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = temp_dir / repo_name

    # Extract kept files into run/
    extractor = FileExtractor(temp_dir, run_dir)
    result = extractor.extract_to_run_dir(repo_path)
    return result

def clear_run_directory(run_dir: str = "run"):
    run_path = Path(run_dir)

    if not run_path.exists():
        return {"status": "run directory does not exist"}

    for item in run_path.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return {"status": "cleared"}