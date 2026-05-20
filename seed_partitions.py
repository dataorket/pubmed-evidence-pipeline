"""
Seed dynamic partition keys for the baseline_files partition set.
Run this BEFORE launching `dagster dev` or after, from a separate terminal.

Usage:
    python seed_partitions.py [start] [end]

    start/end are inclusive file numbers (default: 1200–1209 = already downloaded)

Examples:
    python seed_partitions.py               # seeds 1200–1209
    python seed_partitions.py 1200 1260     # seeds 1200–1260 (61 files, ~50k articles)
    python seed_partitions.py 1200 1300     # seeds 1200–1300 (101 files, ~80k articles)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

from dagster import DagsterInstance
from src.dagster_pipeline.partitions import baseline_file_partitions

def seed(start: int = 1200, end: int = 1209):
    partition_keys = [str(n) for n in range(start, end + 1)]

    with DagsterInstance.get() as instance:
        existing = set(
            instance.get_dynamic_partitions(baseline_file_partitions.name)
        )
        desired = set(partition_keys)
        extra_keys = [k for k in existing if k not in desired]
        removed = 0
        for key in extra_keys:
            if instance.delete_dynamic_partition(baseline_file_partitions.name, key):
                removed += 1

        if removed:
            print(f"Removed {removed} old partition keys: {extra_keys[0]} → {extra_keys[-1]}")

        new_keys = [k for k in partition_keys if k not in existing]

        if not new_keys:
            print(f"All {len(partition_keys)} partitions already exist — nothing to add.")
            return

        instance.add_dynamic_partitions(baseline_file_partitions.name, new_keys)
        print(f"Added {len(new_keys)} new partition keys: {new_keys[0]} → {new_keys[-1]}")
    print(f"Total partitions now: {len(existing) - removed + len(new_keys)}")

if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
    end   = int(sys.argv[2]) if len(sys.argv) > 2 else 1209
    seed(start, end)
