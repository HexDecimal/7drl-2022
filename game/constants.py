from typing import Any

import numpy as np
import tcod
from numpy.typing import NDArray

# SHROUD represents unexplored, unseen tiles
SHROUD: NDArray[Any] = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=tcod.console.rgb_graphic)
