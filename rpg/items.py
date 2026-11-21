from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

from .core import Dice, Hit, UnknownCodeException


@dataclass(frozen=True)
class Enchantment:
    code: str
    name: str
    bonus_damage: int
    bonus_defense: float
    bonus_price: int



SHARP = Enchantment("sharp", "Острое", 3, 0.0, 20)
FIERY = Enchantment("fiery", "Огненное", 6, 0.0, 50)
STURDY = Enchantment("sturdy", "Прочное", 0, 0.05, 20)
WARDING = Enchantment("warding", "Охранное", 0, 0.10, 50)

FOR_WEAPONS = (SHARP, FIERY)
FOR_ARMOR = (STURDY, WARDING)
ALL_ENCHANTMENTS = (SHARP, FIERY, STURDY, WARDING)


class Item(ABC):
    """Паттерн Прототип (Prototype): предметы клонируются из шаблонов каталога."""

    def __init__(
        self,
        code: str,
        name: str,
        base_price: int,
        enchantments: List[Enchantment] | None = None,
    ) -> None:
        self._code = code
        self._name = name
        self._base_price = base_price
        # Новый список, чтобы копия и оригинал не делили список зачарований
        self._enchantments: List[Enchantment] = list(enchantments) if enchantments else []

    @abstractmethod
    def copy(self) -> Item:
        ...

    @abstractmethod
    def get_possible_enchantments(self) -> tuple[Enchantment, ...]:
        ...

    @abstractmethod
    def get_description(self) -> str:
        ...

    def enchant(self, enchantment: Enchantment) -> None:
        if enchantment not in self.get_possible_enchantments():
            raise ValueError(
                f"Зачарование '{enchantment.name}' не подходит для предмета '{self._name}'"
            )
        self._enchantments.append(enchantment)

    @property
    def code(self) -> str:
        return self._code

    @property
    def name(self) -> str:
        return self._name

    @property
    def price(self) -> int:
        return self._base_price + sum(e.bonus_price for e in self._enchantments)

    @property
    def enchantments(self) -> tuple[Enchantment, ...]:
        return tuple(self._enchantments)


class Weapon(Item, ABC):
    def __init__(
        self,
        code: str,
        name: str,
        base_price: int,
        damage: int,
        enchantments: List[Enchantment] | None = None,
    ) -> None:
        super().__init__(code, name, base_price, enchantments)
        self._damage = damage

    @abstractmethod
    def roll_damage(self) -> Hit:
        ...

    @abstractmethod
    def copy(self) -> Weapon:
        ...

    @property
    def damage(self) -> int:
        return self._damage + sum(e.bonus_damage for e in self._enchantments)

    def get_possible_enchantments(self) -> tuple[Enchantment, ...]:
        return FOR_WEAPONS


class Sword(Weapon):
    def roll_damage(self) -> Hit:
        return Hit(self.damage, False)

    def copy(self) -> Sword:
        return Sword(self._code, self._name, self._base_price, self._damage, list(self._enchantments))

    def get_description(self) -> str:
        return f"урон {self.damage}"


class Bow(Weapon):
    CRITICAL_MULTIPLIER = 2

    def __init__(
        self,
        code: str,
        name: str,
        base_price: int,
        damage: int,
        critical_chance: float,
        enchantments: List[Enchantment] | None = None,
    ) -> None:
        super().__init__(code, name, base_price, damage, enchantments)
        self._critical_chance = critical_chance

    def roll_damage(self) -> Hit:
        if Dice.get_instance().chance(self._critical_chance):
            return Hit(self.damage * self.CRITICAL_MULTIPLIER, True)
        return Hit(self.damage, False)

    def copy(self) -> Bow:
        return Bow(
            self._code,
            self._name,
            self._base_price,
            self._damage,
            self._critical_chance,
            list(self._enchantments),
        )

    def get_description(self) -> str:
        return f"урон {self.damage}, шанс крита {round(self._critical_chance * 100)}%"


class Staff(Weapon):
    def __init__(
        self,
        code: str,
        name: str,
        base_price: int,
        damage: int,
        scatter: float,
        enchantments: List[Enchantment] | None = None,
    ) -> None:
        super().__init__(code, name, base_price, damage, enchantments)
        self._scatter = scatter

    def _min_damage(self) -> int:
        return round(self.damage * (1 - self._scatter))

    def _max_damage(self) -> int:
        return round(self.damage * (1 + self._scatter))

    def roll_damage(self) -> Hit:
        return Hit(Dice.get_instance().roll(self._min_damage(), self._max_damage()), False)

    def copy(self) -> Staff:
        return Staff(
            self._code,
            self._name,
            self._base_price,
            self._damage,
            self._scatter,
            list(self._enchantments),
        )

    def get_description(self) -> str:
        return f"урон {self._min_damage()}-{self._max_damage()}"


class Armor(Item):
    MAX_DEFENSE = 0.75

    def __init__(
        self,
        code: str,
        name: str,
        base_price: int,
        defense: float,
        enchantments: List[Enchantment] | None = None,
    ) -> None:
        super().__init__(code, name, base_price, enchantments)
        self._defense = defense

    def copy(self) -> Armor:
        return Armor(self._code, self._name, self._base_price, self._defense, list(self._enchantments))

    @property
    def defense(self) -> float:
        total = self._defense + sum(e.bonus_defense for e in self._enchantments)
        return min(total, self.MAX_DEFENSE)

    def get_possible_enchantments(self) -> tuple[Enchantment, ...]:
        return FOR_ARMOR

    def get_description(self) -> str:
        return f"защита {round(self.defense * 100)}%"


class ItemCatalog:
    """Хранит прототипы предметов и выдаёт только их копии."""

    def __init__(self) -> None:
        self._prototypes: Dict[str, Item] = {}

    def register(self, prototype: Item) -> None:
        self._prototypes[prototype.code] = prototype

    def create(self, code: str) -> Item:
        prototype = self._prototypes.get(code)
        if prototype is None:
            raise UnknownCodeException("Предмет", code)
        return prototype.copy()

    def create_weapon(self, code: str) -> Weapon:
        item = self.create(code)
        if not isinstance(item, Weapon):
            raise ValueError(f"Предмет '{code}' не является оружием")
        return item

    def create_armor(self, code: str) -> Armor:
        item = self.create(code)
        if not isinstance(item, Armor):
            raise ValueError(f"Предмет '{code}' не является броней")
        return item

    def get_codes(self) -> List[str]:
        return list(self._prototypes.keys())


class DefaultCatalog:
    TRAINING_SWORD = "training-sword"
    HUNTING_BOW = "hunting-bow"
    APPRENTICE_STAFF = "apprentice-staff"
    CHAINMAIL = "chainmail"
    LEATHER_ARMOR = "leather-armor"
    LINEN_ROBE = "linen-robe"

    IRON_SWORD = "iron-sword"
    ELVEN_BOW = "elven-bow"
    EMBER_STAFF = "ember-staff"
    PLATE_ARMOR = "plate-armor"

    GOBLIN_CLEAVER = "goblin-cleaver"
    BONE_BOW = "bone-bow"
    NECROMANCER_STAFF = "necromancer-staff"
    KNIGHT_BLADE = "knight-blade"
    CRYPT_MAIL = "crypt-mail"
    DAWN_BLADE = "dawn-blade"
    DRAGONSCALE_ARMOR = "dragonscale-armor"

    @classmethod
    def create(cls) -> ItemCatalog:
        catalog = ItemCatalog()
        # Стартовое снаряжение
        catalog.register(Sword(cls.TRAINING_SWORD, "Тренировочный меч", 20, 12))
        catalog.register(Bow(cls.HUNTING_BOW, "Охотничий лук", 20, 10, 0.3))
        catalog.register(Staff(cls.APPRENTICE_STAFF, "Посох ученика", 20, 14, 0.3))
        catalog.register(Armor(cls.CHAINMAIL, "Кольчуга", 40, 0.3))
        catalog.register(Armor(cls.LEATHER_ARMOR, "Кожаная броня", 30, 0.2))
        catalog.register(Armor(cls.LINEN_ROBE, "Льняная роба", 15, 0.1))
        # Товары торговца
        catalog.register(Sword(cls.IRON_SWORD, "Железный меч", 80, 17))
        catalog.register(Bow(cls.ELVEN_BOW, "Эльфийский лук", 90, 14, 0.4))
        catalog.register(Staff(cls.EMBER_STAFF, "Тлеющий посох", 90, 20, 0.3))
        catalog.register(Armor(cls.PLATE_ARMOR, "Латы", 120, 0.4))
        # Добыча
        catalog.register(Sword(cls.GOBLIN_CLEAVER, "Гоблинский тесак", 40, 15))
        catalog.register(Bow(cls.BONE_BOW, "Костяной лук", 140, 17, 0.4))
        catalog.register(Staff(cls.NECROMANCER_STAFF, "Посох некроманта", 150, 25, 0.35))
        catalog.register(Sword(cls.KNIGHT_BLADE, "Клинок рыцаря", 150, 23))
        catalog.register(Armor(cls.CRYPT_MAIL, "Кольчуга стража склепа", 160, 0.45))
        catalog.register(Sword(cls.DAWN_BLADE, "Клинок рассвета", 500, 35))
        catalog.register(Armor(cls.DRAGONSCALE_ARMOR, "Драконья чешуя", 500, 0.55))
        return catalog


class StarterKitFactory(ABC):
    """Паттерн Абстрактная фабрика (Abstract Factory): семейство стартового снаряжения."""

    def __init__(self, catalog: ItemCatalog) -> None:
        self._catalog = catalog

    @abstractmethod
    def create_weapon(self) -> Weapon:
        ...

    @abstractmethod
    def create_armor(self) -> Armor:
        ...


class WarriorKitFactory(StarterKitFactory):
    def create_weapon(self) -> Weapon:
        return self._catalog.create_weapon(DefaultCatalog.TRAINING_SWORD)

    def create_armor(self) -> Armor:
        return self._catalog.create_armor(DefaultCatalog.CHAINMAIL)


class RangerKitFactory(StarterKitFactory):
    def create_weapon(self) -> Weapon:
        return self._catalog.create_weapon(DefaultCatalog.HUNTING_BOW)

    def create_armor(self) -> Armor:
        return self._catalog.create_armor(DefaultCatalog.LEATHER_ARMOR)


class MageKitFactory(StarterKitFactory):
    def create_weapon(self) -> Weapon:
        return self._catalog.create_weapon(DefaultCatalog.APPRENTICE_STAFF)

    def create_armor(self) -> Armor:
        return self._catalog.create_armor(DefaultCatalog.LINEN_ROBE)
