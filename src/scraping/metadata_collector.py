import requests, datetime, time, json

session = requests.Session()
headers = {
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'GitHub-Repo-Scraper/1.0'
}

GITHUB_TOKEN = ""

if GITHUB_TOKEN:
    headers['Authorization'] = f'token {GITHUB_TOKEN}'
session.headers.update(headers)

def rate_limit():
    try:
        response = session.get("https://api.github.com/rate_limit")
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


def extract_metadata(repo_data):
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


def search_repositories(languages=[], topics=[], min_stars=None, pages=10):

    if rate_limit():
        return []
        
    repositories = []
    url = "https://api.github.com/search/repositories"

    for lang in languages:
        for page in range(pages):
            query = f"language: {lang} stars:>{min_stars}"
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': 100,
                'page': page
            }

            print(f"Fetching page {page} with query '{query}'")

            response = session.get(url, params=params)
            items = response.json().get('items', [])

            for repo in items:
                repo_data = extract_metadata(repo)
                repositories.append(repo_data)

            print(f"Page {page}: {len(items)}, total repos: {len(repositories)})")

    return repositories


def save_list(repositories):
    with open(f'../../data/metadata/metadata.json', 'w', encoding='utf-8') as f:
        json.dump(repositories, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(repositories)} repositories to data/metadata/metadata.json")

