import numpy as np
import scipy.signal  # type: ignore
from numpy.typing import NDArray

import game.combat
import game.entity
import game.game_map
import game.tiles

CARDINAL: NDArray[np.int8] = np.asarray([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.int8)


def fire_step(gamemap: game.game_map.GameMap) -> None:
    exhaused = (gamemap.fire != 0) & (gamemap.fuel <= gamemap.fire)
    gamemap.tiles[exhaused] = 1

    gamemap.fuel[:] -= gamemap.fire
    gamemap.fuel.clip(min=0, out=gamemap.fuel)

    gamemap.heat += scipy.signal.convolve2d(gamemap.fire, CARDINAL, "same")
    gamemap.heat -= gamemap.heat // 10

    fire_gen = np.random.randint(100, 800, (gamemap.height, gamemap.width), dtype=np.int16).T
    new_fire = (
        gamemap.heat >= fire_gen + game.tiles.fire_resist[gamemap.tiles] * (gamemap.fire == 0) + gamemap.fire * 10
    )
    gamemap.fire[:] += new_fire

    max_fire = gamemap.fuel // 16 + 1
    max_fire[gamemap.fuel == 0] = 0
    max_fire.clip(max=100, out=max_fire)
    gamemap.fire.clip(max=max_fire, out=gamemap.fire)

    for obj in gamemap.entities:
        if not isinstance(obj, game.entity.Actor):
            continue
        damage = gamemap.fire[obj.x, obj.y]
        game.combat.apply_damage(obj.fighter, damage)
