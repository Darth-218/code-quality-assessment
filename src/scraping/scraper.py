from metadata_collector import Scraper
from downloader import Downloader
from file_extractor import FileExtractor

TOKEN = ""
count = 0

scraper = Scraper(TOKEN)
repos = scraper.search_repositories(["python", "cpp", "java"], max_size=50000, min_stars=0, pages=100)
scraper.save_list(repos)

downldr = Downloader("data/metadata/metadata.json", "data/temp/")
repos = downldr.load_repos()
for repo in repos:
    max_count = 10
    if count > max_count:
        break
    downldr.clone_repos(repo)
    count += 1

extractor = FileExtractor("data/temp/")
repos = extractor.get_repos()
for repo in repos:
    extractor.prune_repo(repo, execute=False, remove_empty_dirs=False)
    print(f"Extracted files from {repo}")

