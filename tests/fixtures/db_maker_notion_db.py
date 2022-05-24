from csv2notion.notion_row import CollectionRowBlockExtended
from csv2notion.utils_rand_id import rand_id


class NotionDB(object):  # noqa: WPS214
    def __init__(self, page, url):
        self.page = page
        self.url = url

    def set_relation(self, column_name, relation_db):
        schema_raw = self.page.collection.get("schema")

        col_id = _get_dict_key_by_item_value(schema_raw, "name", column_name)

        schema_raw[col_id] = {
            "name": column_name,
            "type": "relation",
            "property": rand_id(4),
            "collection_id": relation_db.page.collection.id,
            "collection_pointer": {
                "id": relation_db.page.collection.id,
                "spaceId": relation_db.page.space_info["spaceId"],
                "table": "collection",
            },
        }
        self.page.collection.set("schema", schema_raw)

    def add_row(self, row):
        new_row = self.page.collection.add_row(**row)
        return CollectionRowBlockExtended(new_row._client, new_row._id)

    @property
    def header(self):
        return set(self.schema_dict.keys())

    @property
    def default_view(self):
        return list(self.page.views)[0]

    @property
    def default_view_header(self):
        header_order = self.default_view.get(
            "format.table_properties", force_refresh=True
        )

        # if header order is not set explicitly, it will be in alphabetical order
        if not header_order:
            other_columns = [c["name"] for c in self.schema if c["type"] != "title"]
            return [self.title_column_name] + sorted(other_columns)

        view_header = []
        for h in header_order:
            h_key = _get_dict_key_by_item_value(self.schema_dict, "id", h["property"])
            view_header.append(h_key)

        return view_header

    @property
    def schema(self):
        return self.page.collection.get_schema_properties()

    @property
    def schema_dict(self):
        return {p["name"]: p for p in self.schema}

    @property
    def title_column_name(self):
        schema_items = self.schema_dict.items()
        title_column = (k for k, v in schema_items if v["type"] == "title")
        return next(title_column)

    @property
    def rows(self):
        sorted_rows = sorted(
            self.page.collection.get_rows(),
            key=lambda r: r.columns[self.title_column_name],
        )
        return [CollectionRowBlockExtended(r._client, r._id) for r in sorted_rows]

    def refresh(self):
        self.page.refresh()

    def remove(self):
        if self.page:
            self.page.remove(permanently=True)
            self.page = None


def _get_dict_key_by_item_value(d, item_key, item_value):
    for key, value in d.items():
        if value[item_key] == item_value:
            return key
    return None
