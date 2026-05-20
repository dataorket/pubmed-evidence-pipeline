from __future__ import annotations

import gzip
import hashlib
import os
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

PUBMED_FTP_BASE = os.getenv("PUBMED_FTP_BASE_URL", "https://ftp.ncbi.nlm.nih.gov/pubmed/baseline")
DATA_DIR = Path(os.getenv("PUBMED_DATA_DIR", "/app/data/pubmed"))


def _file_url(file_name: str) -> str:
    return f"{PUBMED_FTP_BASE}/{file_name}"


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
def download_file(file_name: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dest = DATA_DIR / file_name
    if dest.exists():
        return dest
    url = _file_url(file_name)
    with httpx.Client(timeout=300) as client, client.stream("GET", url) as response:
        response.raise_for_status()
        with dest.open("wb") as f:
            for chunk in response.iter_bytes(chunk_size=8192):
                f.write(chunk)
    return dest


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
def fetch_md5(file_name: str) -> str:
    md5_url = _file_url(f"{file_name}.md5")
    with httpx.Client(timeout=30) as client:
        response = client.get(md5_url)
        response.raise_for_status()
    line = response.text.strip()
    return line.split("=")[-1].strip()


def verify_md5(file_path: Path, expected_md5: str) -> bool:
    hasher = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest() == expected_md5


def decompress(file_path: Path) -> Path:
    out_path = file_path.with_suffix("")
    if out_path.exists():
        return out_path
    with gzip.open(file_path, "rb") as gz, out_path.open("wb") as out:
        while chunk := gz.read(65536):
            out.write(chunk)
    return out_path


def baseline_file_name(number: int) -> str:
    return f"pubmed26n{number:04d}.xml.gz"


def download_and_verify(file_number: int) -> tuple[Path, str]:
    file_name = baseline_file_name(file_number)
    expected_md5 = fetch_md5(file_name)
    for attempt in range(3):
        file_path = download_file(file_name)
        if verify_md5(file_path, expected_md5):
            break
        # Corrupted download — delete and retry
        file_path.unlink(missing_ok=True)
        if attempt == 2:
            raise ValueError(f"MD5 mismatch for {file_name} after 3 attempts")
    xml_path = decompress(file_path)
    return xml_path, expected_md5
