import json
import uuid
from pathlib import Path

import pytest


@pytest.fixture()
def vcr_uuid4(mocker, vcr_cassette_dir, vcr_cassette_name):
    uuid_casette_path = Path(vcr_cassette_dir) / f"{vcr_cassette_name}.uuid4.json"

    if uuid_casette_path.exists():
        uuid_casette = _load_casette(uuid_casette_path)

        mocker.patch("uuid.uuid4", side_effect=uuid_casette)
    else:
        uuid_casette = []

        orign_uuid4 = uuid.uuid4

        def uuid4():
            u = orign_uuid4()
            uuid_casette.append(u)
            return u

        mocker.patch("uuid.uuid4", side_effect=uuid4)

    yield

    if not uuid_casette_path.exists() and uuid_casette:
        _save_casette(uuid_casette, uuid_casette_path)


def _load_casette(uuid_casette_path):
    with open(uuid_casette_path, "r") as f:
        return [uuid.UUID(u) for u in json.load(f)]


def _save_casette(uuid_casette, uuid_casette_path):
    uuid_casette_path.parent.mkdir(parents=True, exist_ok=True)

    with open(uuid_casette_path, "w") as f:
        json.dump([str(u) for u in uuid_casette], f)
