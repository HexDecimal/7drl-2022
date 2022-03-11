from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    import game.engine

fullbright = False  # Debug, all tiles visible.
engine: game.engine.Engine
mouse_pos: Optional[Tuple[int, int]] = None
