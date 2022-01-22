from __future__ import annotations

import logging
from typing import Any, Iterator, Optional, Set, Type, TypeVar

TNode = TypeVar("TNode", bound="Node")

logger = logging.getLogger(__name__)


class Node:
    """A mixin that allows instances to be organzied into a scene graph."""

    def __init__(self, *, parent: Optional[Node] = None) -> None:
        super().__init__()
        self._parent: Optional[Node] = None
        self._children: Set[Any] = set()
        if parent is not None:
            parent.add(self)

    @property
    def parent(self) -> Optional[Node]:
        return self._parent

    @parent.setter
    def parent(self, value: Node) -> None:
        if self._parent is not None:
            logger.debug("Moving %r from %r to %r", self, self._parent, value)
            self._parent.remove(self)
        value.add(self)

    def add(self, node: Node) -> None:
        assert hasattr(node, "_parent"), f"Make sure that subclasses of Node call super().__init__()\n{node!r}"
        assert node._parent is None, f"{node!r} is already assigned to {node._parent!r}"
        node._parent = self
        self._children.add(node)

    def remove(self, node: Node) -> None:
        assert node._parent is self, node._parent
        node._parent = None
        self._children.remove(node)

    def get_parent(self, kind: Type[TNode]) -> TNode:
        while True:
            assert self._parent is not None
            self = self._parent
            if isinstance(self, kind):
                return self

    def try_get(self, kind: Type[TNode]) -> Optional[TNode]:
        for n in self._children:
            if isinstance(n, kind):
                return n
        return None

    def get_child(self, kind: Type[TNode]) -> TNode:
        for n in self._children:
            if isinstance(n, kind):
                return n
        raise TypeError(f"This node has no {kind!r} instances.")

    def set_child(self, kind: Type[TNode], node: Optional[TNode]) -> None:
        self._children = {n for n in self._children if not isinstance(n, kind)}
        if node is not None:
            self.add(node)

    def get_children(self, kind: Type[TNode]) -> Iterator[TNode]:
        for n in self._children:
            if isinstance(n, kind):
                yield n


if __name__ == "__main__":
    n = Node()
