import uuid
from typing import Any, Dict


def make_status_column() -> Dict[str, Any]:
    options_uuid = {
        "Not started": _str_uuid4(),
        "In progress": _str_uuid4(),
        "Done": _str_uuid4(),
    }

    return {
        "options": [
            {"id": options_uuid["Not started"], "value": "Not started"},
            {
                "id": options_uuid["In progress"],
                "value": "In progress",
                "color": "blue",
            },
            {"id": options_uuid["Done"], "value": "Done", "color": "green"},
        ],
        "groups": [
            {
                "id": _str_uuid4(),
                "name": "To-do",
                "optionIds": [options_uuid["Not started"]],
                "color": "gray",
            },
            {
                "id": _str_uuid4(),
                "name": "In progress",
                "optionIds": [options_uuid["In progress"]],
                "color": "blue",
            },
            {
                "id": _str_uuid4(),
                "name": "Complete",
                "optionIds": [options_uuid["Done"]],
                "color": "green",
            },
        ],
        "defaultOption": "Not started",
    }


def _str_uuid4() -> str:
    return str(uuid.uuid4())
