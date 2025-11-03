import os
import requests
import json
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

USERNAME = "maikhel"
REPO= "vas-panel/VAS_valuation_manager"

load_dotenv()

def fetch_github():
    api_key = os.getenv('GITHUB_TOKEN')
    if not api_key:
        raise ValueError("GITHUB_TOKEN not set")

    headers = {
        'Authorization': f'token {api_key}',
        'Accept': 'application/vnd.github.v3+json'
    }

    created_url = f"https://api.github.com/search/issues?q=type:pr+author:{USERNAME}+is:open+repo:{REPO}"
    opened_prs_count = requests.get(created_url, headers=headers).json().get("total_count", 0)

    review_url = f"https://api.github.com/search/issues?q=type:pr+review-requested:{USERNAME}+is:open"
    review_prs_count = requests.get(review_url, headers=headers).json().get("total_count", 0)

    github_info = {
        'opened_prs': opened_prs_count,
        'prs_for_review': review_prs_count,
        'last_updated': datetime.now(timezone.utc).isoformat()
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(script_dir, '..', 'data', 'github.json')
    with open(data_file, 'w') as f:
        json.dump(github_info, f, indent=2)

    return github_info

try:
    fetch_github()
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
