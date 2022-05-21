import hashlib
from pathlib import Path


def get_file_sha256(file_path: Path) -> str:
    hash_sha256 = hashlib.sha256()
    chunk_size = 4096

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):  # noqa: WPS426
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()
