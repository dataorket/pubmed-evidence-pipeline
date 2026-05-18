from __future__ import annotations

from unittest.mock import MagicMock, patch
from pathlib import Path

from src.ingest.downloader import baseline_file_name, verify_md5


def test_baseline_file_name():
    assert baseline_file_name(1138) == "pubmed25n1138.xml.gz"
    assert baseline_file_name(1) == "pubmed25n0001.xml.gz"


def test_verify_md5_correct(tmp_path: Path):
    import hashlib

    content = b"hello world"
    f = tmp_path / "test.gz"
    f.write_bytes(content)
    expected = hashlib.md5(content).hexdigest()
    assert verify_md5(f, expected) is True


def test_verify_md5_wrong(tmp_path: Path):
    f = tmp_path / "test.gz"
    f.write_bytes(b"hello world")
    assert verify_md5(f, "wronghash") is False
