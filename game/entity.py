from __future__ import annotations

import copy
import math
from typing import Optional, Tuple, Type, TypeVar, Union

import game.components.ai
import game.components.consumable
import game.components.fighter
import game.components.inventory
import game.components.level
import game.game_map
import game.render_order

T = TypeVar("T", bound="Entity")


class Entity:
    """A generic object to represent players, enemies, items, etc."""

    def __init__(
        self,
        parent: Optional[Union[game.game_map.GameMap, game.components.inventory.Inventory]] = None,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        blocks_movement: bool = False,
        render_order: game.render_order.RenderOrder = game.render_order.RenderOrder.CORPSE,
    ):
        self.parent = parent
        if isinstance(parent, game.game_map.GameMap):
            parent.entities.add(self)

        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order

    @property
    def gamemap(self) -> game.game_map.GameMap:
        assert self.parent
        return self.parent.gamemap

    def spawn(self: T, gamemap: game.game_map.GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        return clone

    def place(self, x: int, y: int, gamemap: Optional[game.game_map.GameMap] = None) -> None:
        """Place this entitiy at a new location.  Handles moving across GameMaps."""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"):  # Possibly uninitialized.
                if self.parent is self.gamemap:
                    self.gamemap.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)

    def distance(self, x: int, y: int) -> float:
        """
        Return the distance between the current entity and the given (x, y) coordinate.
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move(self, dx: int, dy: int) -> None:
        # Move the entity by a given amount
        self.x += dx
        self.y += dy


class Actor(Entity):
    def __init__(
        self,
        gamemap: Optional[game.game_map.GameMap] = None,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        *,
        ai_cls: Type[game.components.ai.BaseAI],
        fighter: game.components.fighter.Fighter,
        inventory: Optional[game.components.inventory.Inventory] = None,
        level: game.components.level.Level,
    ):
        super().__init__(
            gamemap,
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,
            render_order=game.render_order.RenderOrder.ACTOR,
        )

        self.ai: Optional[game.components.ai.BaseAI] = ai_cls(self)

        self.fighter = fighter
        self.fighter.entity = self

        if inventory is None:
            inventory = game.components.inventory.Inventory(0)
        self.inventory = inventory
        self.inventory.entity = self

        self.level = level
        self.level.entity = self

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)


class Item(Entity):
    def __init__(
        self,
        parent: Optional[Union[game.game_map.GameMap, game.components.inventory.Inventory]] = None,
        x: int = 0,
        y: int = 0,
        *,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        consumable: game.components.consumable.Consumable,
    ):
        super().__init__(
            parent,
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=False,
            render_order=game.render_order.RenderOrder.ITEM,
        )
        if isinstance(parent, game.components.inventory.Inventory):
            parent.items.append(self)

        self.consumable = consumable
        self.consumable.parent = self
