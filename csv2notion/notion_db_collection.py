from typing import Any, Dict, List, Optional, cast

from notion.collection import Collection

from csv2notion.notion_row import CollectionRowBlockExtended
from csv2notion.utils_rand_id import rand_id_unique


class CollectionExtended(Collection):
    def get_rows(self) -> List[CollectionRowBlockExtended]:  # noqa: WPS615
        return [
            CollectionRowBlockExtended(row._client, row._id)
            for row in super().get_rows()
        ]

    def get_unique_rows(self) -> Dict[str, CollectionRowBlockExtended]:
        rows: Dict[str, CollectionRowBlockExtended] = {}

        # sort rows so that only first row is kept if multiple have same title
        sorted_rows = sorted(self.get_rows(), key=lambda r: str(r.title))

        for row in sorted_rows:
            rows.setdefault(row.title, row)
        return rows

    def add_row_block(
        self,
        update_views: bool = True,
        row_class: Optional[type] = None,
        properties: Optional[Dict[str, Any]] = None,
        columns: Optional[Dict[str, Any]] = None,
    ) -> CollectionRowBlockExtended:
        row_class = row_class or CollectionRowBlockExtended

        new_row = super().add_row_block(
            update_views=update_views,
            row_class=row_class,
            properties=properties,
            columns=columns,
        )

        return cast(CollectionRowBlockExtended, new_row)

    def add_column(self, column_name: str, column_type: str) -> None:
        schema_raw = self.get("schema")
        new_id = rand_id_unique(4, schema_raw)
        schema_raw[new_id] = {"name": column_name, "type": column_type}
        self.set("schema", schema_raw)

    def has_duplicates(self) -> bool:
        row_titles = [row.title for row in self.get_rows()]
        return len(row_titles) != len(set(row_titles))

    def is_accessible(self) -> bool:
        rec = self._client.get_record_data("collection", self.id, force_refresh=True)
        return rec is not None
