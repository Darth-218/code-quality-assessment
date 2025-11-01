from metadata_collector import Scraper
from downloader import Downloader
from file_extractor import FileExtractor

TOKEN = ""
count = 0

scraper = Scraper(TOKEN)
repos = scraper.search_repositories(["python", "cpp"], min_stars=10, pages=1)
scraper.save_list(repos)

downldr = Downloader("../../data/metadata/metadata.json", "../../data/temp/")
repos = downldr.load_repos()
for repo in repos:
    max_count = 2
    if count > max_count:
        break
    downldr.clone_repos(repo)
    count += 1

extractor = FileExtractor("../../data/temp/", "../../data/raw/")
for repo in repos:
    extractor.extract_files(repo)

