import requests

import common

USERNAME = "maikhel"
REPO = "vas-panel/VAS_valuation_manager"
GRAPHQL_URL = "https://api.github.com/graphql"

MAX_PRS = 8

# One GraphQL call replaces two REST searches and adds review state and CI
# status, neither of which the REST search API can return at all.
QUERY = """
query($mine: String!, $review: String!, $limit: Int!) {
  mine: search(query: $mine, type: ISSUE, first: $limit) {
    issueCount
    nodes {
      ... on PullRequest {
        title
        isDraft
        reviewDecision
        commits(last: 1) {
          nodes { commit { statusCheckRollup { state } } }
        }
      }
    }
  }
  review: search(query: $review, type: ISSUE, first: $limit) {
    issueCount
    nodes {
      ... on PullRequest {
        title
        repository { name }
        commits(last: 1) {
          nodes { commit { statusCheckRollup { state } } }
        }
      }
    }
  }
}
"""


def _ci_state(node):
    """SUCCESS / FAILURE / PENDING / ... or None when there are no checks."""
    commits = (node.get('commits') or {}).get('nodes') or []
    if not commits:
        return None
    rollup = (commits[0].get('commit') or {}).get('statusCheckRollup')
    return rollup.get('state') if rollup else None


def fetch_github():
    headers = {'Authorization': f"bearer {common.require_env('GITHUB_TOKEN')}"}
    variables = {
        'mine': f"type:pr author:{USERNAME} is:open repo:{REPO}",
        'review': f"type:pr review-requested:{USERNAME} is:open",
        'limit': MAX_PRS,
    }

    response = requests.post(GRAPHQL_URL, headers=headers,
                             json={'query': QUERY, 'variables': variables})
    response.raise_for_status()
    body = response.json()

    # GraphQL reports errors in a 200 response, so raise_for_status is not enough.
    if body.get('errors'):
        raise ValueError(body['errors'][0].get('message', 'GraphQL error'))

    data = body['data']

    opened_prs = [
        {
            'title': node['title'],
            'draft': node.get('isDraft', False),
            'review': node.get('reviewDecision'),
            'ci': _ci_state(node),
        }
        for node in data['mine']['nodes'] if node
    ]

    review_requested = [
        {
            'title': node['title'],
            'repo': (node.get('repository') or {}).get('name'),
            'ci': _ci_state(node),
        }
        for node in data['review']['nodes'] if node
    ]

    return {
        'opened_prs': opened_prs,
        'review_requested': review_requested,
        'prs_for_review': data['review']['issueCount'],
    }


common.run('github', fetch_github)
