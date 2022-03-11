from __future__ import annotations

from typing import Any

import numpy as np
import tcod
from numpy.typing import NDArray

tile_graphics: NDArray[Any] = np.array(
    [
        (ord("#"), (0x80, 0x80, 0x80), (0x40, 0x40, 0x40)),  # wall
        (ord("."), (0x40, 0x40, 0x40), (0x18, 0x18, 0x18)),  # floor
        (ord(">"), (0xFF, 0xFF, 0xFF), (0x18, 0x18, 0x18)),  # down stairs
        (ord(","), (0x40, 0x40, 0x40), (0x18, 0x18, 0x18)),  # outdoors
    ],
    dtype=tcod.console.rgb_graphic,
)

tile_fuel: NDArray[np.int32] = np.array([8000, 24000, 0, 3000])
fire_resist: NDArray[np.int32] = np.array([2000, 0, 0, 0])
