import requests

import common

USERNAME = "maikhel"
REPO = "vas-panel/VAS_valuation_manager"
API = "https://api.github.com/search/issues"


def fetch_github():
    headers = {
        'Authorization': f"token {common.require_env('GITHUB_TOKEN')}",
        'Accept': 'application/vnd.github.v3+json',
    }

    created = requests.get(
        f"{API}?q=type:pr+author:{USERNAME}+is:open+repo:{REPO}", headers=headers)
    created.raise_for_status()

    opened_prs = [
        {
            'title': item['title'],
            'state': item['state'],
            'draft': item.get('draft', False),
        }
        for item in created.json().get('items', [])
    ]

    review = requests.get(
        f"{API}?q=type:pr+review-requested:{USERNAME}+is:open", headers=headers)
    review.raise_for_status()

    return {
        'opened_prs': opened_prs,
        'prs_for_review': review.json().get('total_count', 0),
    }


common.run('github', fetch_github)
