# (generated with --quick)

import __future__
from typing import Any, Dict, List, Optional

division: __future__._Feature
itertools: module
np: module
print_function: __future__._Feature

class FPGrowth:
    __doc__: str
    frequent_itemsets: list
    min_sup: Any
    prefixes: Dict[Any, List[Dict[str, Any]]]
    transactions: Any
    tree_root: Optional[FPTreeNode]
    def __init__(self, min_sup = ...) -> None: ...
    def _calculate_support(self, item, transactions) -> int: ...
    def _construct_tree(self, transactions, frequent_items = ...) -> FPTreeNode: ...
    def _determine_frequent_itemsets(self, conditional_database, suffix) -> None: ...
    def _determine_prefixes(self, itemset, node, prefixes = ...) -> None: ...
    def _get_frequent_items(self, transactions) -> List[list]: ...
    def _get_itemset_key(self, itemset) -> str: ...
    def _insert_tree(self, node, children) -> None: ...
    def _is_prefix(self, itemset, node) -> bool: ...
    def find_frequent_itemsets(self, transactions, suffix = ..., show_tree = ...) -> list: ...
    def print_tree(self, node = ..., indent_times = ...) -> None: ...

class FPTreeNode:
    children: Dict[Any, FPTreeNode]
    item: Any
    support: Any
    def __init__(self, item = ..., support = ...) -> None: ...
