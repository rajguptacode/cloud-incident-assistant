"""Storage layer — SQLite persistence via repositories.

Repositories return Pydantic models (from ``cloudops_sentinel.models``);
domain logic never touches SQL.
"""

from cloudops_sentinel.storage.database import Database, StorageError

__all__ = ["Database", "StorageError"]