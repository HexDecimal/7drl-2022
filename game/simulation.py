import numpy as np
import scipy.signal  # type: ignore
from numpy.typing import NDArray

import game.game_map

CARDINAL: NDArray[np.int8] = np.asarray([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.int8)


def fire_step(gamemap: game.game_map.GameMap) -> None:
    exhaused = (gamemap.fire != 0) & (gamemap.fuel <= gamemap.fire)
    gamemap.tiles[exhaused] = 1

    gamemap.fuel[:] -= gamemap.fire
    gamemap.fuel.clip(min=0, out=gamemap.fuel)

    new_fire = scipy.signal.convolve2d(gamemap.fire, CARDINAL, "same")
    fire_gen = np.random.randint(1, 101, (gamemap.height, gamemap.width), dtype=np.int8).T
    new_fire = new_fire >= fire_gen
    gamemap.fire[:] += new_fire

    gamemap.fire.clip(max=gamemap.fuel, out=gamemap.fire)
