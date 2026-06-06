"""cgimg local-only replacement of the original chatgpt2api storage factory.

The upstream factory imported DatabaseStorageBackend (sqlalchemy) and
GitStorageBackend (gitpython), pulling heavy deps cgimg does not need. For
single-user image generation there is no multi-backend account pool to persist,
so this version ALWAYS returns the local JSON backend regardless of the
STORAGE_BACKEND env var. Call signature matches the original
`create_storage_backend(data_dir: Path) -> StorageBackend`.
"""
from __future__ import annotations

from pathlib import Path

from services.storage.base import StorageBackend
from services.storage.json_storage import JSONStorageBackend


def create_storage_backend(data_dir: Path) -> StorageBackend:
    """Always construct and return a local JSON storage backend.

    Matches the original signature so existing call sites (config.py:471)
    work unchanged. The original branched on STORAGE_BACKEND for
    sqlite/postgres/git; cgimg only ever uses JSON.
    """
    file_path = data_dir / "accounts.json"
    auth_keys_path = data_dir / "auth_keys.json"
    return JSONStorageBackend(file_path, auth_keys_path)
