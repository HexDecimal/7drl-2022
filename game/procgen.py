from __future__ import annotations

import logging
import random
from typing import Dict, Iterator, List, Tuple

import numpy as np
import scipy.signal  # type: ignore
import tcod
import wfc.wfc_control
from numpy.typing import NDArray

import game
import game.components.consumable
import game.engine
import game.entity
import game.entity_factories
import game.game_map
import game.tiles

logger = logging.getLogger(__name__)

WALL = 0
FLOOR = 1
DOWN_STAIRS = 2
OUTDOORS = 3

max_items_by_floor = [
    (1, 1),
    (4, 2),
]

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

item_chances: Dict[int, List[Tuple[game.entity.Entity, int]]] = {
    0: [(game.entity_factories.health_potion, 35)],
    2: [(game.entity_factories.confusion_scroll, 10)],
    4: [(game.entity_factories.lightning_scroll, 25), (game.entity_factories.sword, 5)],
    6: [(game.entity_factories.fireball_scroll, 25), (game.entity_factories.chain_mail, 15)],
}

enemy_chances: Dict[int, List[Tuple[game.entity.Entity, int]]] = {
    0: [(game.entity_factories.orc, 80)],
    3: [(game.entity_factories.troll, 15)],
    5: [(game.entity_factories.troll, 30)],
    7: [(game.entity_factories.troll, 60)],
}


def get_max_value_for_floor(max_value_by_floor: List[Tuple[int, int]], floor: int) -> int:
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value


def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple[game.entity.Entity, int]]],
    number_of_entities: int,
    floor: int,
) -> List[game.entity.Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(entities, weights=entity_weighted_chance_values, k=number_of_entities)

    return chosen_entities


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        """Return the center coordinates of the room."""
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return self.x1 <= other.x2 and self.x2 >= other.x1 and self.y1 <= other.y2 and self.y2 >= other.y1


def place_entities(room: RectangularRoom, dungeon: game.game_map.GameMap, floor_number: int) -> None:
    number_of_monsters = random.randint(0, get_max_value_for_floor(max_monsters_by_floor, floor_number))
    number_of_items = random.randint(0, get_max_value_for_floor(max_items_by_floor, floor_number))

    monsters: List[game.entity.Entity] = get_entities_at_random(enemy_chances, number_of_monsters, floor_number)
    items: List[game.entity.Entity] = get_entities_at_random(item_chances, number_of_items, floor_number)

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if dungeon.get_blocking_entity_at(x, y):
            continue
        if (x, y) == dungeon.enter_xy:
            continue

        entity.spawn(dungeon, x, y)


def tunnel_between(
    engine: game.engine.Engine, start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if engine.rng.random() < 0.5:  # 50% chance.
        corner_x, corner_y = x2, y1  # Move horizontally, then vertically.
    else:
        corner_x, corner_y = x1, y2  # Move vertically, then horizontally.

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def load_pattern(name: str) -> NDArray[np.uint8]:
    pattern_txt = (game.DATA_DIR / name).read_text(encoding="utf-8").strip().splitlines()
    pattern: NDArray[np.uint8] = np.asarray([[ord(c) for c in row] for row in pattern_txt], dtype=np.uint8)
    pattern = pattern[:, :, np.newaxis]
    return pattern


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    engine: game.engine.Engine,
) -> game.game_map.GameMap:
    """Generate a new dungeon map."""
    dungeon = game.game_map.GameMap(engine, map_width, map_height)
    dungeon.parent = engine

    gen = wfc.wfc_control.execute_wfc(
        image=load_pattern("pattern4.txt"),
        pattern_width=3,
        output_size=(map_height, map_width),
        output_periodic=False,
        input_periodic=False,
        input_ground=((1, 1), (1, 1)),
        output_ground=((1, 3), (1, 3)),
    )[:, :, 0].T

    dungeon.tiles[gen == ord("#")] = WALL
    dungeon.tiles[gen == ord(".")] = OUTDOORS
    dungeon.tiles[gen == ord("1")] = FLOOR

    logger.info("Making indoor areas accessible.")

    accessible_path = tcod.path.maxarray((map_width, map_height), order="F")  # Accessible area distance-path.
    accessible_path[gen == ord(".")] = 0  # Initialize with outdoors.
    unaccessible_zone = gen == ord("1")  # Connect to the innder room area.

    CARDINAL: NDArray[np.int8] = np.asarray([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=np.int8)

    while unaccessible_zone.any():
        cost: NDArray[np.int32] = np.zeros((map_width, map_height), dtype=np.int32, order="F")
        cost[dungeon.tiles == WALL] = 5
        cost[dungeon.tiles == OUTDOORS] = 10
        cost[dungeon.tiles == FLOOR] = 1

        cost = scipy.signal.convolve2d(cost, CARDINAL, "same")
        cost[dungeon.tiles != WALL] = 0
        cost[dungeon.tiles == OUTDOORS] = 1
        cost[dungeon.tiles == FLOOR] = 1

        graph = tcod.path.SimpleGraph(cost=cost, cardinal=1, diagonal=0)
        pf = tcod.path.Pathfinder(graph)
        accessible_root = random.choice(np.argwhere(accessible_path != np.iinfo(accessible_path.dtype).max))  # type: ignore
        pf.add_root(accessible_root)
        path = pf.path_from(random.choice(np.argwhere(unaccessible_zone)))  # type: ignore
        path_indexes = tuple(path.T)
        path_values = dungeon.tiles[path_indexes]
        path_doorways = path[path_values == WALL]
        logger.info(f"Opening path with walls={(path_values == WALL).sum()}, length={len(path)}.")
        path_values[path_values == WALL] = FLOOR
        dungeon.tiles[path_indexes] = path_values
        for x, y in path_doorways.tolist():
            assert isinstance(x, int)
            assert isinstance(y, int)
            # game.entity_factories.door_test.spawn(dungeon, x, y)

        tcod.path.dijkstra2d(
            accessible_path, cost=dungeon.tiles == FLOOR, cardinal=1, diagonal=None, out=accessible_path
        )
        unaccessible_zone &= accessible_path == np.iinfo(accessible_path.dtype).max

    dungeon.fuel = game.tiles.tile_fuel[dungeon.tiles]

    for x, y in random.sample(np.argwhere(gen == ord("1")).tolist(), 3):
        dungeon.fire[x, y] += 20
        dungeon.fuel[x, y] += 20 * 10
        dungeon.memory[x, y]["ch"] = ord("?")

    for x, y in random.sample(np.argwhere(gen == ord("1")).tolist(), 10):
        game.entity_factories.civ.spawn(dungeon, x, y)
        dungeon.memory[x, y]["ch"] = ord("?")

    dungeon.enter_xy = (1, 1)

    return dungeon
