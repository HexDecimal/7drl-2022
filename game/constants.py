from typing import Any

import numpy as np
import tcod
from numpy.typing import NDArray

# SHROUD represents unexplored, unseen tiles
SHROUD: NDArray[Any] = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=tcod.console.rgb_graphic)

screen_width = 80
screen_height = 50

map_width = 50
map_height = 50

ui_width = 30

room_max_size = 10
room_min_size = 6
max_rooms = 30
