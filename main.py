#!/usr/bin/env python3
import logging
import traceback

import tcod

import game.color
import game.engine
import game.entity
import game.exceptions
import game.input_handlers
import game.procgen
import game.setup_game
import game.typing


def save_game(handler: game.typing.EventHandler, filename: str) -> None:
    """If the current event handler has an active Engine then save it."""
    if isinstance(handler, game.input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print("Game saved.")


def main() -> None:
    screen_width = 80
    screen_height = 50

    tileset = tcod.tileset.load_tilesheet("data/dejavu16x16_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD)

    event_handler: game.typing.EventHandler = game.setup_game.MainMenu()

    with tcod.context.new(
        columns=screen_width,
        rows=screen_height,
        tileset=tileset,
        title="Yet Another Roguelike Tutorial",
        vsync=True,
    ) as context:
        root_console = tcod.Console(screen_width, screen_height, order="F")
        try:
            while True:
                root_console.clear()
                event_handler.on_render(console=root_console)
                context.present(root_console)

                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        event_handler = event_handler.handle_events(event)
                except Exception:  # Handle exceptions in game.
                    traceback.print_exc()  # Print error to stderr.
                    # Then print the error to the message log.
                    if isinstance(event_handler, game.input_handlers.EventHandler):
                        event_handler.engine.message_log.add_message(traceback.format_exc(), game.color.error)
        except game.exceptions.QuitWithoutSaving:
            raise SystemExit()
        except SystemExit:  # Save and quit.
            save_game(event_handler, "savegame.sav")
            raise
        except BaseException:  # Save on any other error.
            save_game(event_handler, "savegame.sav")
            raise


if __name__ == "__main__":
    if __debug__:
        logging.basicConfig(level=logging.DEBUG)
    main()
