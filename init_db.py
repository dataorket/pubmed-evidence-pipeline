import os
from src.db.session import init_db

database_url = os.environ.get("DATABASE_URL")
if database_url:
    init_db(database_url)
    print("Database initialized.")
else:
    print("DATABASE_URL not set — skipping DB init.")
