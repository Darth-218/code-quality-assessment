from metadata_collector import Scraper
from downloader import Downloader
from file_extractor import FileExtractor

METADATA_PATH = ""
TOKEN = ""

scraper = Scraper(TOKEN)
repos = scraper.search_repositories(["python", "java", "cpp"], min_stars=10)
scraper.save_list(repos)

downldr = Downloader("../../data/metadata/metadata.json", "../../data/temp/")
repos = downldr.load_repos()
for repo in repos:
    downldr.clone_repos(repo)

extractor = FileExtractor("../../data/temp/", "../../data/raw/")
for repo in repos:
    extractor.extract_files(repo)

