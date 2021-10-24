# (generated with --quick)

from typing import Any, Dict, FrozenSet, List, Pattern

DEFAULT_FORMAT_OPTIONS: List[str]
HTTP_GET: str
HTTP_POST: str
OUTPUT_OPTIONS: FrozenSet[str]
OUTPUT_OPTIONS_DEFAULT: str
OUTPUT_OPTIONS_DEFAULT_OFFLINE: str
OUTPUT_OPTIONS_DEFAULT_STDOUT_REDIRECTED: str
OUT_REQ_BODY: str
OUT_REQ_HEAD: str
OUT_RESP_BODY: str
OUT_RESP_HEAD: str
PRETTY_MAP: Dict[str, List[str]]
PRETTY_STDOUT_TTY_ONLY: Any
SEPARATORS_GROUP_MULTIPART: FrozenSet[str]
SEPARATOR_CREDENTIALS: str
SEPARATOR_DATA_EMBED_FILE_CONTENTS: str
SEPARATOR_DATA_EMBED_RAW_JSON_FILE: str
SEPARATOR_DATA_RAW_JSON: str
SEPARATOR_DATA_STRING: str
SEPARATOR_FILE_UPLOAD: str
SEPARATOR_FILE_UPLOAD_TYPE: str
SEPARATOR_GROUP_ALL_ITEMS: FrozenSet[str]
SEPARATOR_GROUP_DATA_EMBED_ITEMS: FrozenSet[str]
SEPARATOR_GROUP_DATA_ITEMS: FrozenSet[str]
SEPARATOR_GROUP_RAW_JSON_ITEMS: FrozenSet[str]
SEPARATOR_HEADER: str
SEPARATOR_HEADER_EMPTY: str
SEPARATOR_PROXY: str
SEPARATOR_QUERY_PARAM: str
SORTED_FORMAT_OPTIONS: List[str]
SORTED_FORMAT_OPTIONS_STRING: str
UNSORTED_FORMAT_OPTIONS_STRING: str
URL_SCHEME_RE: Pattern[str]
enum: module
re: module

class RequestType(enum.Enum):
    FORM: enum.auto
    JSON: enum.auto
    MULTIPART: enum.auto