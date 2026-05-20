"""
Run all Dagster asset checks, including extra checks for duplicates, nulls, and value ranges.
"""
from src.dagster_pipeline import checks, checks_extra

if __name__ == "__main__":
    # This will register all checks when run with Dagster CLI or as a script
    pass
