from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, List, Optional

from .core import Dice, Hit, UnknownCodeException
from .items import (
    Armor,
    Item,
    ItemCatalog,
    MageKitFactory,
    RangerKitFactory,
    StarterKitFactory,
    WarriorKitFactory,
    Weapon,
)


class Combatant(ABC):
    @property
    @abstractmethod
    def code(self) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def health(self) -> int: ...

    @property
    @abstractmethod
    def max_health(self) -> int: ...

    @abstractmethod
    def is_alive(self) -> bool: ...

    @abstractmethod
    def roll_damage(self) -> Hit: ...

    @abstractmethod
    def receive_hit(self, amount: int) -> int: ...


class HeroClass(Enum):
    WARRIOR = ("warrior", "Воин", 120, WarriorKitFactory)
    RANGER = ("ranger", "Следопыт", 100, RangerKitFactory)
    MAGE = ("mage", "Маг", 85, MageKitFactory)

    def __init__(
        self,
        code: str,
        display_name: str,
        base_health: int,
        kit_factory_cls: Callable[[ItemCatalog], StarterKitFactory],
    ) -> None:
        self.code = code
        self.display_name = display_name
        self.base_health = base_health
        self._kit_factory_cls = kit_factory_cls

    def get_starter_kit(self, catalog: ItemCatalog) -> StarterKitFactory:
        return self._kit_factory_cls(catalog)

    @classmethod
    def by_code(cls, code: str) -> HeroClass:
        for hero_class in cls:
            if hero_class.code == code:
                return hero_class
        raise UnknownCodeException("Класс героя", code)


class Hero(Combatant):
    MAX_NAME_LENGTH = 20
    STARTING_GOLD = 50
    HEALTH_PER_LEVEL = 15
    DAMAGE_PER_LEVEL = 3
    EXPERIENCE_PER_LEVEL = 100

    def __init__(
        self,
        name: str,
        hero_class: HeroClass,
        weapon: Weapon,
        armor: Armor,
        level: int = 1,
        gold: int = STARTING_GOLD,
    ) -> None:
        self._name = name
        self._hero_class = hero_class
        self._level = level
        self._experience = 0
        self._gold = gold
        self._weapon = weapon
        self._armor = armor
        self._inventory: List[Item] = []
        self._health = self.max_health

    class Builder:
        """Паттерн Строитель (Builder): пошаговая сборка и валидация героя."""

        def __init__(self) -> None:
            self._name: Optional[str] = None
            self._hero_class: Optional[HeroClass] = None
            self._weapon: Optional[Weapon] = None
            self._armor: Optional[Armor] = None
            self._level: int = 1
            self._gold: int = Hero.STARTING_GOLD

        def set_name(self, name: str) -> Hero.Builder:
            self._name = name
            return self

        def set_hero_class(self, hero_class: HeroClass) -> Hero.Builder:
            self._hero_class = hero_class
            return self

        def set_weapon(self, weapon: Weapon) -> Hero.Builder:
            self._weapon = weapon
            return self

        def set_armor(self, armor: Armor) -> Hero.Builder:
            self._armor = armor
            return self

        def set_starter_kit(self, kit: StarterKitFactory) -> Hero.Builder:
            self._weapon = kit.create_weapon()
            self._armor = kit.create_armor()
            return self

        def set_level(self, level: int) -> Hero.Builder:
            self._level = level
            return self

        def set_gold(self, gold: int) -> Hero.Builder:
            self._gold = gold
            return self

        def build(self) -> Hero:
            if not self._name or not self._name.strip():
                raise ValueError("У героя должно быть имя")
            if len(self._name) > Hero.MAX_NAME_LENGTH:
                raise ValueError(f"Имя героя не может быть длиннее {Hero.MAX_NAME_LENGTH} символов")
            if self._hero_class is None:
                raise ValueError("Не выбран класс героя")
            if self._weapon is None or self._armor is None:
                raise ValueError("Герою нужны оружие и броня")
            if self._level < 1:
                raise ValueError("Уровень героя не может быть меньше 1")
            if self._gold < 0:
                raise ValueError("Золота не может быть меньше нуля")

            return Hero(
                name=self._name,
                hero_class=self._hero_class,
                weapon=self._weapon,
                armor=self._armor,
                level=self._level,
                gold=self._gold,
            )

    def roll_damage(self) -> Hit:
        hit = self._weapon.roll_damage()
        return Hit(hit.damage + (self._level - 1) * self.DAMAGE_PER_LEVEL, hit.critical)

    def receive_hit(self, amount: int) -> int:
        reduced = round(amount * (1 - self._armor.defense))
        dealt = max(1, reduced)
        self._health = max(0, self._health - dealt)
        return dealt

    def is_alive(self) -> bool:
        return self._health > 0

    def restore_health(self) -> None:
        self._health = self.max_health

    def gain_experience(self, amount: int) -> int:
        self._experience += amount
        levels_gained = 0
        while self._experience >= self.experience_to_next_level:
            self._experience -= self.experience_to_next_level
            self._level += 1
            levels_gained += 1
        return levels_gained

    def add_gold(self, amount: int) -> None:
        self._gold += amount

    def spend_gold(self, amount: int) -> None:
        if amount > self._gold:
            raise RuntimeError(f"Не хватает золота: нужно {amount}, есть {self._gold}")
        self._gold -= amount

    def add_item(self, item: Item) -> None:
        self._inventory.append(item)

    def remove_item(self, item: Item) -> None:
        if item not in self._inventory:
            raise ValueError(f"В инвентаре нет предмета {item.name}")
        self._inventory.remove(item)

    def equip(self, item: Item) -> None:
        if isinstance(item, Weapon):
            self.remove_item(item)
            self._inventory.append(self._weapon)
            self._weapon = item
        elif isinstance(item, Armor):
            self.remove_item(item)
            self._inventory.append(self._armor)
            self._armor = item
        else:
            raise ValueError(f"Предмет нельзя экипировать: {item.name}")

    @property
    def code(self) -> str:
        return self._hero_class.code

    @property
    def name(self) -> str:
        return self._name

    @property
    def health(self) -> int:
        return self._health

    @property
    def max_health(self) -> int:
        return self._hero_class.base_health + (self._level - 1) * self.HEALTH_PER_LEVEL

    @property
    def hero_class(self) -> HeroClass:
        return self._hero_class

    @property
    def level(self) -> int:
        return self._level

    @property
    def experience(self) -> int:
        return self._experience

    @property
    def experience_to_next_level(self) -> int:
        return self._level * self.EXPERIENCE_PER_LEVEL

    @property
    def gold(self) -> int:
        return self._gold

    @property
    def weapon(self) -> Weapon:
        return self._weapon

    @property
    def armor(self) -> Armor:
        return self._armor

    @property
    def inventory(self) -> tuple[Item, ...]:
        return tuple(self._inventory)


class Enemy(Combatant, ABC):
    @abstractmethod
    def get_experience_reward(self) -> int: ...

    @abstractmethod
    def roll_gold_reward(self) -> int: ...


class AbstractEnemy(Enemy):
    def __init__(
        self,
        code: str,
        name: str,
        max_health: int,
        min_damage: int,
        max_damage: int,
        experience_reward: int,
        gold_reward: int,
    ) -> None:
        self._code = code
        self._name = name
        self._max_health = max_health
        self._min_damage = min_damage
        self._max_damage = max_damage
        self._experience_reward = experience_reward
        self._gold_reward = gold_reward
        self._health = max_health

    def roll_damage(self) -> Hit:
        return Hit(Dice.get_instance().roll(self._min_damage, self._max_damage), False)

    def receive_hit(self, amount: int) -> int:
        dealt = max(1, self._reduce_damage(amount))
        self._health = max(0, self._health - dealt)
        return dealt

    def _reduce_damage(self, amount: int) -> int:
        return amount

    def is_alive(self) -> bool:
        return self._health > 0

    def roll_gold_reward(self) -> int:
        return Dice.get_instance().roll(self._gold_reward // 2, self._gold_reward)

    def get_experience_reward(self) -> int:
        return self._experience_reward

    @property
    def code(self) -> str:
        return self._code

    @property
    def name(self) -> str:
        return self._name

    @property
    def health(self) -> int:
        return self._health

    @property
    def max_health(self) -> int:
        return self._max_health


class Goblin(AbstractEnemy):
    def __init__(self) -> None:
        super().__init__("goblin", "Гоблин", 50, 6, 14, 40, 30)


class Skeleton(AbstractEnemy):
    RESISTANCE = 0.3

    def __init__(self) -> None:
        super().__init__("skeleton", "Скелет", 110, 10, 24, 90, 70)

    def _reduce_damage(self, amount: int) -> int:
        return round(amount * (1 - self.RESISTANCE))


class Dragon(AbstractEnemy):
    RESISTANCE = 0.25
    FIRE_BREATH_CHANCE = 0.25
    FIRE_BREATH_MULTIPLIER = 2

    def __init__(self) -> None:
        super().__init__("dragon", "Дракон", 260, 16, 22, 500, 400)

    def roll_damage(self) -> Hit:
        bite = super().roll_damage()
        if Dice.get_instance().chance(self.FIRE_BREATH_CHANCE):
            return Hit(bite.damage * self.FIRE_BREATH_MULTIPLIER, True)
        return bite

    def _reduce_damage(self, amount: int) -> int:
        return round(amount * (1 - self.RESISTANCE))
