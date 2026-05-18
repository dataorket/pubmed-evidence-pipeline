from __future__ import annotations

import os

from dagster import DynamicPartitionsDefinition, StaticPartitionsDefinition

# Each partition key = one baseline file number (e.g. "1138", "1137", ...)
# Populated dynamically as files are discovered
baseline_file_partitions = DynamicPartitionsDefinition(name="baseline_files")
