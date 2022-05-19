import hashlib
import mimetypes
import re
from pathlib import Path
from typing import Optional, Tuple, Union

import requests
from notion.block import Block

from csv2notion.utils_static import FileType


def upload_filetype(parent: Block, filetype: FileType):
    url = filetype

    if isinstance(filetype, Path):
        url, meta = upload_file(parent, filetype)
    elif filetype is None:
        meta = None
    else:
        meta = {"type": "url", "url": filetype}

    return url, meta


def upload_file(block: Block, file_path: Path) -> Tuple[str, dict]:
    file_mime = mimetypes.guess_type(str(file_path))[0]

    post_data = {
        "bucket": "secure",
        "name": file_path.name,
        "contentType": file_mime,
        "record": {
            "table": "block",
            "id": block.id,
            "spaceId": block.space_info["spaceId"],
        },
    }

    upload_data = block._client.post("getUploadFileUrl", post_data).json()

    with open(file_path, "rb") as f:
        file_bin = f.read()

    requests.put(
        upload_data["signedPutUrl"],
        data=file_bin,
        headers={"Content-type": file_mime},
    ).raise_for_status()

    return upload_data["url"], {
        "type": "file",
        "file_id": get_file_id(upload_data["url"]),
        "sha256": hashlib.sha256(file_bin).hexdigest(),
    }


def get_file_sha256(file_path: Path) -> str:
    with open(file_path, "rb") as f:
        file_bin = f.read()
    return hashlib.sha256(file_bin).hexdigest()


def get_file_id(image_url: str) -> Optional[str]:
    try:
        return re.search("secure.notion-static.com/([^/]+)", image_url)[1]
    except TypeError:
        return None


def is_meta_different(image: Union[str, Path], image_url: str, image_meta: dict):
    if not image_meta:
        return True

    if isinstance(image, Path):
        checks = [
            lambda: image_meta["type"] != "file",
            lambda: image_meta["file_id"] != get_file_id(image_url),
            lambda: image_meta["sha256"] != get_file_sha256(image),
        ]

        return any(c() for c in checks)

    elif image_meta != {"type": "url", "url": image}:
        return True

    return False
