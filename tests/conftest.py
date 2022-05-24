import base64

import pytest

from tests.fixtures.db_maker import db_maker  # noqa: F401
from tests.fixtures.vcr_uuid4 import vcr_uuid4  # noqa: F401


@pytest.fixture(scope="session")
def vcr_config():
    """Remove meta bloat to reduce cassette size"""

    def response_cleaner(response):
        bloat_headers = [
            "Content-Security-Policy",
            "Expect-CT",
            "ETag",
            "Referrer-Policy",
            "Strict-Transport-Security",
            "Vary",
            "Date",
            "Server",
            "Connection",
            "Set-Cookie",
        ]

        for h in response["headers"].copy():
            if h.startswith("X-") or h.startswith("CF-") or h in bloat_headers:
                response["headers"].pop(h)

        return response

    return {
        "filter_headers": [
            ("cookie", "PRIVATE"),
            "Accept",
            "Accept-Encoding",
            "Connection",
            "User-Agent",
        ],
        "before_record_response": response_cleaner,
        "decode_compressed_response": True,
    }


@pytest.fixture()
def smallest_gif():
    yield base64.b64decode("R0lGODlhAQABAAAAACH5BAEAAAAALAAAAAABAAEAAAIA")
