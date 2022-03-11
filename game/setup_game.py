"""Handle the loading and initialization of game sessions."""
from __future__ import annotations

import copy
import lzma
import pickle
import random
import traceback
from typing import Optional

import tcod

import g
import game.color
import game.engine
import game.entity_factories
import game.game_map
import game.input_handlers
import game.procgen
from game.constants import map_height, map_width, max_rooms, room_max_size, room_min_size
from game.input_handlers import BaseEventHandler


def new_game() -> game.engine.Engine:
    """Return a brand new game session as an Engine instance."""
    engine = game.engine.Engine()
    engine.game_world = game.game_map.GameWorld(
        engine=engine,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
    )
    engine.rng = random.Random()
    engine.game_world.generate_floor()
    engine.player = game.entity_factories.player.spawn(engine.game_map, *engine.game_map.enter_xy)
    engine.update_fov()

    engine.message_log.add_message("Hello and welcome, adventurer, to yet another dungeon!", game.color.welcome_text)

    dagger = copy.deepcopy(game.entity_factories.dagger)
    leather_armor = copy.deepcopy(game.entity_factories.leather_armor)

    dagger.parent = engine.player.inventory
    leather_armor.parent = engine.player.inventory

    engine.player.inventory.items.append(dagger)
    engine.player.equipment.toggle_equip(dagger, add_message=False)

    engine.player.inventory.items.append(leather_armor)
    engine.player.equipment.toggle_equip(leather_armor, add_message=False)

    g.engine = engine
    return engine


def load_game(filename: str) -> game.engine.Engine:
    """Load an Engine instance from a file."""
    with open(filename, "rb") as f:
        g.engine = engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, game.engine.Engine)
    return engine


class MainMenu(BaseEventHandler):
    """Handle the main menu rendering and input."""

    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "TOMBS OF THE ANCIENT KINGS",
            fg=game.color.menu_title,
            alignment=tcod.CENTER,
        )
        console.print(
            console.width // 2,
            console.height - 2,
            "By (Your name here)",
            fg=game.color.menu_title,
            alignment=tcod.CENTER,
        )

        menu_width = 24
        for i, text in enumerate(["[N] Play a new game", "[C] Continue last game", "[Q] Quit"]):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=game.color.menu_text,
                bg=game.color.black,
                alignment=tcod.CENTER,
                bg_blend=tcod.BKGND_ALPHA(64),
            )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[game.input_handlers.BaseEventHandler]:
        if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
            raise SystemExit()
        elif event.sym == tcod.event.K_c:
            try:
                return game.input_handlers.MainGameEventHandler(load_game("savegame.sav"))
            except FileNotFoundError:
                return game.input_handlers.PopupMessage(self, "No saved game to load.")
            except Exception as exc:
                traceback.print_exc()  # Print to stderr.
                return game.input_handlers.PopupMessage(self, f"Failed to load save:\n{exc}")
        elif event.sym == tcod.event.K_n:
            return game.input_handlers.MainGameEventHandler(new_game())

        return None
