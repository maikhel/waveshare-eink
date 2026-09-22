"""Shared plumbing for the fetch scripts.

Every service does the same three things: read credentials, call an API, and
hand the result to the renderer as JSON. Only the middle part differs.
"""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone

from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')

# Resolve .env from the repo, not the working directory -- cron does not run
# these from the checkout.
load_dotenv(os.path.join(ROOT, '.env'))


def require_env(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} not set")
    return value


def data_path(source):
    return os.path.join(DATA_DIR, f'{source}.json')


def write_data(source, data):
    """Write the envelope for `source` atomically.

    The renderer reads these files on its own schedule, so a half-written file
    is a real possibility: write to a temporary file in the same directory and
    rename it over the target, which is atomic on POSIX.
    """
    envelope = {
        'source': source,
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'data': data,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=DATA_DIR, prefix=f'.{source}-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(envelope, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, data_path(source))
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def run(source, fetch):
    """Run a fetch function and store its result, or fail loudly.

    On failure nothing is written, so the previous result stays in place. Data
    that is merely old is better than no screen at all.
    """
    try:
        data = fetch()
    except Exception as e:
        print(f"[ERROR] {source}: {e}", file=sys.stderr)
        sys.exit(1)

    write_data(source, data)
