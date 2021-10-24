# (generated with --quick)

from typing import Any, TypeVar

sys: module

_T0 = TypeVar('_T0')

class PriorityQueue:
    array: list
    def __init__(self) -> None: ...
    def __len__(self) -> int: ...
    def decrease_key(self, obj, new_key) -> None: ...
    def extract_min(self) -> None: ...
    def insert(self, node: _T0) -> _T0: ...

class PriorityQueueNode:
    key: Any
    obj: Any
    def __init__(self, obj, key) -> None: ...
    def __repr__(self) -> str: ...