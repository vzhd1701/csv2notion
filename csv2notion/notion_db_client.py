from copy import deepcopy
from typing import Any, Optional

from notion.client import NotionClient, create_session
from notion.space import Space
from notion.store import RecordStore
from notion.user import User


class ClonableNotionClient(NotionClient):
    def __init__(
        self,
        *args: Any,
        old_client: Optional[NotionClient] = None,
        **kwargs: Any,
    ):
        if old_client is None:
            super().__init__(*args, **kwargs)

        self._monitor = None

        self.session = create_session()
        self.session.cookies = old_client.session.cookies.copy()  # type: ignore

        self._store = self._clone_store(old_client)

        self._clone_user_info(old_client)

    def _clone_store(self, old_client: NotionClient) -> RecordStore:
        new_store = RecordStore(self)
        old_store = old_client._store

        new_store._values = deepcopy(old_store._values)
        new_store._role = deepcopy(old_store._role)
        new_store._collection_row_ids = deepcopy(old_store._collection_row_ids)

        return new_store

    def _clone_user_info(self, old_client: NotionClient) -> None:
        self.current_user = User(self, old_client.current_user.id)
        self.current_space = Space(self, old_client.current_space.id)

        self.session.headers.update(
            {"x-notion-active-user-header": self.current_user.id}
        )
