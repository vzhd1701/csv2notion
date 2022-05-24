from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

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
        "file",
        "person",
    )
)

UNSETTABLE_TYPES = frozenset(("created_by", "last_edited_by", "rollup", "formula"))

FileType = Union[str, Path]


@dataclass
class ConversionRules(object):
    csv_file: Path

    image_column: Optional[str]
    image_column_keep: bool
    image_column_mode: str
    image_caption_column: Optional[str]
    image_caption_column_keep: bool

    icon_column: Optional[str]
    icon_column_keep: bool
    default_icon: Optional[FileType]

    merge: bool
    merge_only_column: List[str]
    merge_skip_new: bool

    add_missing_columns: bool
    add_missing_relations: bool

    mandatory_column: List[str]
    fail_on_relation_duplicates: bool
    fail_on_duplicates: bool
    fail_on_conversion_error: bool
    fail_on_inaccessible_relations: bool
    fail_on_missing_columns: bool
    fail_on_unsettable_columns: bool

    @property
    def files_search_path(self) -> Path:
        return self.csv_file.parent

    @classmethod
    def from_args(cls, args: Namespace) -> "ConversionRules":
        args_map = {
            arg_name: getattr(args, arg_name) for arg_name in cls.__dataclass_fields__
        }

        return cls(**args_map)
