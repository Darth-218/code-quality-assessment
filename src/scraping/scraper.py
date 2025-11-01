from metadata_collector import Scraper

METADATA_PATH = ""
TOKEN = ""

scraper = Scraper(TOKEN)
repos = scraper.search_repositories(["python", "java", "cpp"], min_stars=10)
scraper.save_list(repos)

extractor = Extractor()
files = extractor.extract_files(METADATA_PATH)
extractor.download_files(files)

