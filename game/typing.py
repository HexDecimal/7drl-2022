from __future__ import annotations

from typing import Protocol, Union

import tcod


class Action(Protocol):
    def perform(self) -> None:
        """Perform this action now."""
        ...


class EventHandler(Protocol):
    def handle_events(self, event: tcod.event.Event) -> EventHandler:
        """Handle an event and return the next active event handler."""
        ...

    def on_render(self, console: tcod.Console) -> None:
        ...


ActionOrHandler = Union[Action, EventHandler]
"""An event handler return value which can trigger an action or switch active handlers.

If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""
