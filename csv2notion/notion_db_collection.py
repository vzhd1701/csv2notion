import random
from typing import Any, Dict, List, Optional, Tuple, cast

from notion.collection import Collection, NotionSelect

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

    def check_schema_select_options(  # noqa: WPS210
        self, prop: Dict[str, Any], values: Any  # noqa: WPS110
    ) -> Tuple[bool, Dict[str, Any]]:
        schema_update = False

        prop_options = prop.setdefault("options", [])
        current_options = [p["value"].lower() for p in prop_options]
        if not isinstance(values, list):
            values = [values]  # noqa: WPS110

        for v in values:
            if v and v.lower() not in current_options:
                schema_update = True

                if self._client.options.get("is_randomize_select_colors") is True:
                    color = _get_random_select_color()
                else:
                    color = "default"

                prop_options.append(NotionSelect(v, color).to_dict())
        return schema_update, prop


def _get_random_select_color() -> str:
    return str(random.choice(NotionSelect.valid_colors))  # noqa: S311
