import requests, datetime, time, json

class Scraper:
    def __init__(self, token) -> None:
        self.token = token
        self.session = requests.Session()
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Repo-Scraper/1.0'
        }
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        self.session.headers.update(headers)

    def rate_limit(self):
        try:
            response = self.session.get("https://api.github.com/rate_limit")
            if response.status_code == 200:
                data = response.json()
                core = data['resources']['core']
                rate_limit_remaining = core['remaining']
                
                if rate_limit_remaining < 10:
                    reset_time = datetime.fromtimestamp(core['reset'])
                    wait_time = (reset_time - datetime.now()).total_seconds()
                    if wait_time > 0:
                        print(f"Rate limit low. Waiting {wait_time/60:.1f} minutes")
                        time.sleep(wait_time + 10)
                    return True
                return False

        except Exception as e:
            print(f"Error checking rate limit: {e}")

        return False


    def extract_metadata(self, repo_data):
        return {
            'id': repo_data['id'],
            'name': repo_data['name'],
            'full_name': repo_data['full_name'],
            'html_url': repo_data['html_url'],
            'clone_url': repo_data['clone_url'],
            'description': repo_data.get('description', ''),
            'language': repo_data.get('language'),
            'created_at': repo_data['created_at'],
            'updated_at': repo_data['updated_at'],
            'size': repo_data['size'],
            'stargazers_count': repo_data['stargazers_count'],
            'forks_count': repo_data['forks_count'],
            'open_issues_count': repo_data['open_issues_count'],
            'license': repo_data.get('license', {}).get('key') if repo_data.get('license') else None,
            'topics': repo_data.get('topics', []),
            'owner_login': repo_data['owner']['login'],
            'is_fork': repo_data['fork'],
            'is_archived': repo_data.get('archived', False),
        }


    def search_repositories(self, languages=[], topics=[], max_size=None, min_stars=0, pages=10):

        if self.rate_limit():
            return []
            
        repositories = []
        url = "https://api.github.com/search/repositories"

        for lang in languages:
            for page in range(pages):
                query = f"language: {lang} stars:>{min_stars} size:<{max_size}"
                params = {
                    'q': query,
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 100,
                    'page': page
                }

                print(f"Fetching page {page} with query '{query}'")

                response = self.session.get(url, params=params)
                items = response.json().get('items', [])

                for repo in items:
                    repo_data = self.extract_metadata(repo)
                    repositories.append(repo_data)

                print(f"Page {page}, total repos: {len(repositories)})")

        return repositories


    def save_list(self, repositories):
        with open("../../data/metadata/metadata.json", 'w', encoding='utf-8') as f:
            json.dump(repositories, f, indent=2, ensure_ascii=True)
        
        print(f"Saved {len(repositories)} repositories to data/metadata/metadata.json")
        return True

