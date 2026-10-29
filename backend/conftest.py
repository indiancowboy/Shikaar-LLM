"""Test setup.

- Ensures `backend/` is on sys.path so tests can `import app.*`.
- Points the inventory store at an isolated temp SQLite DB so tests never touch
  the real `backend/data/shikaar.db`.
"""
import os
import tempfile

# Most tests aren't about the AI quota; test_usage.py turns it on explicitly.
os.environ.setdefault("AI_DAILY_LIMIT", "0")

os.environ["SHIKAAR_DB"] = os.path.join(
    tempfile.mkdtemp(prefix="shikaar_test_"), "shikaar.db"
)
