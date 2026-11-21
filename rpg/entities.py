from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, List, Optional, Sequence

from .core import Dice, Hit, UnknownCodeException
from .defense import ArmorHandler, BarrierHandler, Damage, DamageHandler, EvasionHandler
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


class Achievement(Enum):
    FIRST_BLOOD = ("first-blood", "Первая кровь", "одержать первую победу")
    LUCKY = ("lucky", "Счастливчик", "найти зачарованный лут")
    VETERAN = ("veteran", "Ветеран", "достичь 5 уровня")
    DRAGON_SLAYER = ("dragon-slayer", "Драконоборец", "победить дракона")

    def __init__(self, code: str, display_name: str, description: str) -> None:
        self.code = code
        self.display_name = display_name
        self.description = description

    @classmethod
    def by_code(cls, code: str) -> Achievement:
        for ach in cls:
            if ach.code == code:
                return ach
        raise UnknownCodeException("Достижение", code)


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
    def receive_hit(self, amount: int) -> Damage: ...


class HeroClass(Enum):
    WARRIOR = ("warrior", "Воин", 120, WarriorKitFactory, 0.0, 0)
    RANGER = ("ranger", "Следопыт", 100, RangerKitFactory, 0.15, 0)
    MAGE = ("mage", "Маг", 85, MageKitFactory, 0.0, 30)

    def __init__(
        self,
        code: str,
        display_name: str,
        base_health: int,
        kit_factory_cls: Callable[[ItemCatalog], StarterKitFactory],
        evasion: float,
        barrier: int,
    ) -> None:
        self.code = code
        self.display_name = display_name
        self.base_health = base_health
        self._kit_factory_cls = kit_factory_cls
        self.evasion = evasion
        self.barrier = barrier

    def get_starter_kit(self, catalog: ItemCatalog) -> StarterKitFactory:
        return self._kit_factory_cls(catalog)

    def create_defense(self, armor: Armor, level: int) -> DamageHandler:
        """Динамически собирает цепочку обязанностей: уклонение -> броня -> барьер."""
        evasion = self.evasion
        barrier = self.barrier
        if self == HeroClass.WARRIOR and level >= 3:
            barrier = 20
        elif self == HeroClass.RANGER and level >= 5:
            barrier = 15
        elif self == HeroClass.MAGE and level >= 3:
            evasion = 0.10

        armor_handler: DamageHandler = ArmorHandler(armor.defense)
        first: DamageHandler = armor_handler

        if evasion > 0:
            first = EvasionHandler(evasion)
            first.set_next(armor_handler)
        if barrier > 0:
            armor_handler.set_next(BarrierHandler(barrier))

        return first

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
        experience: int = 0,
        gold: int = STARTING_GOLD,
        inventory: Sequence[Item] = (),
        achievements: Sequence[Achievement] = (),
    ) -> None:
        self._name = name
        self._hero_class = hero_class
        self._level = level
        self._experience = experience
        self._gold = gold
        self._weapon = weapon
        self._armor = armor
        self._inventory: List[Item] = list(inventory)
        self._achievements: List[Achievement] = list(achievements)
        self._health = 0
        self._defense: DamageHandler = hero_class.create_defense(armor, level)
        self.rest()

    class Builder:
        """Паттерн Строитель (Builder): пошаговая сборка и валидация героя."""

        def __init__(self) -> None:
            self._name: Optional[str] = None
            self._hero_class: Optional[HeroClass] = None
            self._weapon: Optional[Weapon] = None
            self._armor: Optional[Armor] = None
            self._level: int = 1
            self._experience: int = 0
            self._gold: int = Hero.STARTING_GOLD
            self._inventory: List[Item] = []
            self._achievements: List[Achievement] = []

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

        def set_experience(self, experience: int) -> Hero.Builder:
            self._experience = experience
            return self

        def set_gold(self, gold: int) -> Hero.Builder:
            self._gold = gold
            return self

        def set_inventory(self, inventory: Sequence[Item]) -> Hero.Builder:
            self._inventory = list(inventory)
            return self

        def set_achievements(self, achievements: Sequence[Achievement]) -> Hero.Builder:
            self._achievements = list(achievements)
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
            if self._experience < 0:
                raise ValueError("Опыта не может быть меньше нуля")
            if self._gold < 0:
                raise ValueError("Золота не может быть меньше нуля")

            return Hero(
                name=self._name,
                hero_class=self._hero_class,
                weapon=self._weapon,
                armor=self._armor,
                level=self._level,
                experience=self._experience,
                gold=self._gold,
                inventory=self._inventory,
                achievements=self._achievements,
            )

    def roll_damage(self) -> Hit:
        hit = self._weapon.roll_damage()
        return Hit(hit.damage + (self._level - 1) * self.DAMAGE_PER_LEVEL, hit.critical)

    def receive_hit(self, amount: int) -> Damage:
        damage = Damage(amount)
        self._defense.handle(damage)
        self._health = max(0, self._health - damage.amount)
        return damage

    def is_alive(self) -> bool:
        return self._health > 0

    def rest(self) -> None:
        self._health = self.max_health
        self._defense = self._hero_class.create_defense(self._armor, self._level)

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
            self._defense = self._hero_class.create_defense(self._armor, self._level)
        else:
            raise ValueError(f"Предмет нельзя экипировать: {item.name}")

    def unlock(self, achievement: Achievement) -> bool:
        if achievement in self._achievements:
            return False
        self._achievements.append(achievement)
        return True

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

    @property
    def achievements(self) -> tuple[Achievement, ...]:
        return tuple(self._achievements)


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
        defense: Optional[DamageHandler] = None,
    ) -> None:
        self._code = code
        self._name = name
        self._max_health = max_health
        self._min_damage = min_damage
        self._max_damage = max_damage
        self._experience_reward = experience_reward
        self._gold_reward = gold_reward
        self._defense = defense
        self._health = max_health

    def roll_damage(self) -> Hit:
        return Hit(Dice.get_instance().roll(self._min_damage, self._max_damage), False)

    def receive_hit(self, amount: int) -> Damage:
        damage = Damage(amount)
        if self._defense is not None:
            self._defense.handle(damage)
        self._health = max(0, self._health - damage.amount)
        return damage

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
        super().__init__("goblin", "Гоблин", 50, 6, 14, 40, 30, None)


class Skeleton(AbstractEnemy):
    RESISTANCE = 0.3

    def __init__(self) -> None:
        super().__init__("skeleton", "Скелет", 110, 10, 24, 90, 70, ArmorHandler(self.RESISTANCE))


class Dragon(AbstractEnemy):
    RESISTANCE = 0.25
    FIRE_BREATH_CHANCE = 0.25
    FIRE_BREATH_MULTIPLIER = 2

    def __init__(self) -> None:
        super().__init__("dragon", "Дракон", 260, 16, 22, 500, 400, ArmorHandler(self.RESISTANCE))

    def roll_damage(self) -> Hit:
        bite = super().roll_damage()
        if Dice.get_instance().chance(self.FIRE_BREATH_CHANCE):
            return Hit(bite.damage * self.FIRE_BREATH_MULTIPLIER, True)
        return bite


class HauntedWeapon(Enemy):
    """Паттерн Адаптер (Adapter): адаптирует Weapon к интерфейсу Enemy."""

    HEALTH_PER_DAMAGE = 5

    def __init__(self, weapon: Weapon) -> None:
        self._weapon = weapon
        self._max_health = weapon.damage * self.HEALTH_PER_DAMAGE
        self._health = self._max_health

    @property
    def code(self) -> str:
        return "haunted-weapon"

    @property
    def name(self) -> str:
        return f"Одержимый {self._weapon.name}"

    def roll_damage(self) -> Hit:
        # Основная ценность адаптера: переиспользуем боевую логику оружия
        return self._weapon.roll_damage()

    def receive_hit(self, amount: int) -> Damage:
        damage = Damage(amount)
        self._health = max(0, self._health - damage.amount)
        return damage

    def is_alive(self) -> bool:
        return self._health > 0

    def get_experience_reward(self) -> int:
        return self._weapon.price // 2

    def roll_gold_reward(self) -> int:
        return Dice.get_instance().roll(self._weapon.price // 4, self._weapon.price // 2)

    @property
    def health(self) -> int:
        return self._health

    @property
    def max_health(self) -> int:
        return self._max_health


class EnemyDecorator(Enemy):
    """Паттерн Декоратор (Decorator): базовый декоратор для комбинируемых модификаторов врагов."""

    def __init__(self, wrapped: Enemy) -> None:
        self._wrapped = wrapped

    @property
    def code(self) -> str:
        return self._wrapped.code

    @property
    def name(self) -> str:
        return self._wrapped.name

    @property
    def health(self) -> int:
        return self._wrapped.health

    @property
    def max_health(self) -> int:
        return self._wrapped.max_health

    def is_alive(self) -> bool:
        return self._wrapped.is_alive()

    def roll_damage(self) -> Hit:
        return self._wrapped.roll_damage()

    def receive_hit(self, amount: int) -> Damage:
        return self._wrapped.receive_hit(amount)

    def get_experience_reward(self) -> int:
        return self._wrapped.get_experience_reward()

    def roll_gold_reward(self) -> int:
        return self._wrapped.roll_gold_reward()


class LegendaryEnemy(EnemyDecorator):
    """Легендарный модификатор: удваивает урон и награду."""

    MULTIPLIER = 2

    @property
    def name(self) -> str:
        return f"Легендарный {super().name}"

    def roll_damage(self) -> Hit:
        hit = super().roll_damage()
        return Hit(hit.damage * self.MULTIPLIER, hit.critical)

    def get_experience_reward(self) -> int:
        return super().get_experience_reward() * self.MULTIPLIER

    def roll_gold_reward(self) -> int:
        return super().roll_gold_reward() * self.MULTIPLIER


class WindfuryEnemy(EnemyDecorator):
    """Неистовство ветра: складывает два броска урона в один удар, +50% награды."""

    REWARD_BONUS_PERCENT = 50

    @property
    def name(self) -> str:
        return f"Неистовый {super().name}"

    def roll_damage(self) -> Hit:
        first = super().roll_damage()
        second = super().roll_damage()
        return Hit(first.damage + second.damage, first.critical or second.critical)

    def get_experience_reward(self) -> int:
        return self._with_bonus(super().get_experience_reward())

    def roll_gold_reward(self) -> int:
        return self._with_bonus(super().roll_gold_reward())

    def _with_bonus(self, reward: int) -> int:
        return reward + reward * self.REWARD_BONUS_PERCENT // 100


class ArmoredEnemy(EnemyDecorator):
    """Бронированный модификатор: режет входящий урон вдвое перед передачей дальше."""

    @property
    def name(self) -> str:
        return f"Бронированный {super().name}"

    def receive_hit(self, amount: int) -> Damage:
        if amount < 0:
            raise ValueError("Урон не может быть отрицательным")
        if amount == 0:
            return Damage(0)
        return super().receive_hit(amount - amount // 2)
