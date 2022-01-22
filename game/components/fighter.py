from __future__ import annotations

import game.color
import game.entity
import game.input_handlers
import game.render_order
from game.components.ai import BaseAI
from game.components.base_component import BaseComponent


class Fighter(BaseComponent):
    parent: game.entity.Actor

    def __init__(self, hp: int, base_defense: int, base_power: int):
        super().__init__()
        self.max_hp = hp
        self._hp = hp
        self.base_defense = base_defense
        self.base_power = base_power

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.entity.try_get(BaseAI):
            self.die()

    @property
    def defense(self) -> int:
        return self.base_defense + self.defense_bonus

    @property
    def power(self) -> int:
        return self.base_power + self.power_bonus

    @property
    def defense_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus
        else:
            return 0

    @property
    def power_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.power_bonus
        else:
            return 0

    def die(self) -> None:
        if self.entity.gamemap.engine.player is self.entity:
            death_message = "You died!"
            death_message_color = game.color.player_die
        else:
            death_message = f"{self.entity.name} is dead!"
            death_message_color = game.color.enemy_die

        self.entity.char = "%"
        self.entity.color = (191, 0, 0)
        self.entity.blocks_movement = False
        self.entity.set_child(BaseAI, None)
        self.entity.name = f"remains of {self.entity.name}"
        self.entity.render_order = game.render_order.RenderOrder.CORPSE

        self.entity.gamemap.engine.message_log.add_message(death_message, death_message_color)

        self.engine.player.level.add_xp(self.parent.level.xp_given)

    def heal(self, amount: int) -> int:
        if self.hp == self.max_hp:
            return 0

        new_hp_value = self.hp + amount

        if new_hp_value > self.max_hp:
            new_hp_value = self.max_hp

        amount_recovered = new_hp_value - self.hp

        self.hp = new_hp_value

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
