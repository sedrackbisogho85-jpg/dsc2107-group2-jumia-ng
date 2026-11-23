"""Member 2 - Initialize or open the SQLite database."""

from database import Database


def init_db(db_path: str = "pharmacy.db") -> Database:
    """Create the schema and return an open repository."""
    return Database(db_path)


if __name__ == "__main__":
    repo = init_db()
    repo.close()
