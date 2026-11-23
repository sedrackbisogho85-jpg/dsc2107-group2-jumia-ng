"""
Member 2 - SQLite database and persistence.

Database connections, foreign-key activation and schema initialization are
implemented by InventoryRepository in repository.py.
"""

from repository import InventoryRepository

# Backwards-compatible descriptive name for Member 2 database callers.
Database = InventoryRepository

__all__ = ["Database", "InventoryRepository"]
