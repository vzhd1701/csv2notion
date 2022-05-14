ALLOWED_TYPES = frozenset(
    (
        "checkbox",
        "date",
        "multi_select",
        "select",
        "number",
        "email",
        "phone_number",
        "url",
        "text",
        "created_time",
        "last_edited_time",
        "created_by",
        "last_edited_by",
        "rollup",
        "formula",
    )
)

UNSETTABLE_TYPES = frozenset(("created_by", "last_edited_by", "rollup", "formula"))
