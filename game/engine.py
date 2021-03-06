from __future__ import annotations

import logging
import lzma
import pickle
import random

import tcod

import game.entity
import game.exceptions
import game.game_map
import game.message_log
import game.simulation
from game.components.ai import BaseAI
from game.node import Node

logger = logging.getLogger(__name__)


class Engine(Node):
    game_map: game.game_map.GameMap
    game_world: game.game_map.GameWorld
    player: game.entity.Actor
    rng: random.Random
    mouse_location = (0, 0)

    def __init__(self) -> None:
        super().__init__()
        self.message_log = game.message_log.MessageLog()

    def handle_enemy_turns(self) -> None:
        game.simulation.fire_step(self.game_map)
        logger.info("Enemy turn.")
        for entity in self.game_map.entities:
            if entity is self.player:
                continue
            if not isinstance(entity, game.entity.Actor):
                continue
            ai = entity.try_get(BaseAI)
            if ai:
                try:
                    ai.perform()
                except game.exceptions.Impossible:
                    pass  # Ignore impossible action exceptions from AI.

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        self.game_map.visible[:] = tcod.map.compute_fov(
            self.game_map.tiles,
            (self.player.x, self.player.y),
            radius=0,
            algorithm=tcod.FOV_SYMMETRIC_SHADOWCAST,
        )
        # If a tile is currently "visible" it will also be marked as "explored".
        self.game_map.explored |= self.game_map.visible

    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)
