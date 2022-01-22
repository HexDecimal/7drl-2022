from __future__ import annotations

from typing import List

import game.entity
from game.components.base_component import BaseComponent


class Inventory(BaseComponent):
    def __init__(self, capacity: int):
        super().__init__()
        self.capacity = capacity
        self.items: List[game.entity.Item] = []

    def drop(self, item: game.entity.Item) -> None:
        """
        Removes an item from the inventory and restores it to the game map, at the player's current location.
        """
        self.items.remove(item)

        item.parent = self.gamemap
        self.gamemap.add(item)
        item.x = self.owner.x
        item.y = self.owner.y

        self.engine.message_log.add_message(f"You dropped the {item.name}.")
