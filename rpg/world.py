from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Sequence

from .combat import BalancedTactic, Battle, Tactic
from .core import Dice, ExpeditionReport, Outcome, Rewards, UnknownCodeException
from .entities import (
    ArmoredEnemy,
    Dragon,
    Enemy,
    Goblin,
    HauntedWeapon,
    Hero,
    LegendaryEnemy,
    Skeleton,
    WindfuryEnemy,
)
from .items import DefaultCatalog, Item, ItemCatalog


class Location(ABC):
    """Паттерн Фабричный метод (Factory Method): подклассы определяют, какого врага создать."""

    LOOT_CHANCE = 0.6
    ENCHANT_CHANCE = 0.3
    ELITE_CHANCE = 0.2
    DOUBLE_ELITE_CHANCE = 0.25
    ARMORED_CHANCE = 0.3

    def __init__(self, code: str, display_name: str, recommended_level: int, catalog: ItemCatalog) -> None:
        self._code = code
        self._display_name = display_name
        self._recommended_level = recommended_level
        self._catalog = catalog

    @abstractmethod
    def _create_enemy(self) -> Enemy:
        ...

    @abstractmethod
    def _get_loot_table(self) -> Sequence[str]:
        ...

    def explore(
        self,
        hero: Hero,
        tactic: Optional[Tactic] = None,
        seed: Optional[int] = None,
    ) -> ExpeditionReport:
        dice = Dice.get_instance()
        actual_tactic = tactic if tactic is not None else BalancedTactic()
        actual_seed = seed if seed is not None else dice.next_seed()
        dice.reseed(actual_seed)

        hero.rest()
        enemy = self._create_enemy()
        if dice.chance(self.ELITE_CHANCE):
            enemy = self._make_elite(enemy, dice)

        battle = Battle(hero, enemy, actual_tactic).run()
        rewards = (
            self._reward(hero, enemy, dice)
            if battle.outcome == Outcome.VICTORY
            else self._punish(hero)
        )
        return ExpeditionReport(actual_seed, self._code, actual_tactic.code, battle, rewards)

    def _make_elite(self, enemy: Enemy, dice: Dice) -> Enemy:
        both = dice.chance(self.DOUBLE_ELITE_CHANCE)
        if dice.chance(0.5):
            enemy = LegendaryEnemy(enemy)
            if both:
                enemy = WindfuryEnemy(enemy)
        else:
            enemy = WindfuryEnemy(enemy)
            if both:
                enemy = LegendaryEnemy(enemy)

        return ArmoredEnemy(enemy) if dice.chance(self.ARMORED_CHANCE) else enemy

    def _reward(self, hero: Hero, enemy: Enemy, dice: Dice) -> Rewards:
        experience = enemy.get_experience_reward()
        gold = enemy.roll_gold_reward()
        loot = self._roll_loot(dice)

        levels_gained = hero.gain_experience(experience)
        hero.add_gold(gold)
        if loot is not None:
            hero.add_item(loot)
        return Rewards(experience, gold, loot, levels_gained)

    def _roll_loot(self, dice: Dice) -> Optional[Item]:
        if not dice.chance(self.LOOT_CHANCE):
            return None
        loot = self._catalog.create(dice.pick(self._get_loot_table()))
        if dice.chance(self.ENCHANT_CHANCE):
            loot.enchant(dice.pick(loot.get_possible_enchantments()))
        return loot

    def _punish(self, hero: Hero) -> Rewards:
        lost_gold = hero.gold // 2
        hero.spend_gold(lost_gold)
        return Rewards(0, -lost_gold, None, 0)

    @property
    def code(self) -> str:
        return self._code

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def recommended_level(self) -> int:
        return self._recommended_level


class Forest(Location):
    CODE = "forest"

    def __init__(self, catalog: ItemCatalog) -> None:
        super().__init__(self.CODE, "Мистический лес", 1, catalog)

    def _create_enemy(self) -> Enemy:
        return Goblin()

    def _get_loot_table(self) -> Sequence[str]:
        return (DefaultCatalog.GOBLIN_CLEAVER, DefaultCatalog.HUNTING_BOW, DefaultCatalog.LEATHER_ARMOR)


class HauntedManor(Location):
    """Локация, использующая Адаптер HauntedWeapon для превращения оружия во врага."""

    CODE = "haunted-manor"
    HAUNTED_WEAPONS = (
        DefaultCatalog.IRON_SWORD,
        DefaultCatalog.ELVEN_BOW,
        DefaultCatalog.EMBER_STAFF,
    )

    def __init__(self, catalog: ItemCatalog) -> None:
        super().__init__(self.CODE, "Проклятый особняк", 2, catalog)

    def _create_enemy(self) -> Enemy:
        weapon = self._catalog.create_weapon(Dice.get_instance().pick(self.HAUNTED_WEAPONS))
        return HauntedWeapon(weapon)

    def _get_loot_table(self) -> Sequence[str]:
        return (
            DefaultCatalog.IRON_SWORD,
            DefaultCatalog.ELVEN_BOW,
            DefaultCatalog.EMBER_STAFF,
            DefaultCatalog.PLATE_ARMOR,
        )


class Crypt(Location):
    CODE = "crypt"

    def __init__(self, catalog: ItemCatalog) -> None:
        super().__init__(self.CODE, "Заброшенный склеп", 3, catalog)

    def _create_enemy(self) -> Enemy:
        return Skeleton()

    def _get_loot_table(self) -> Sequence[str]:
        return (
            DefaultCatalog.KNIGHT_BLADE,
            DefaultCatalog.BONE_BOW,
            DefaultCatalog.NECROMANCER_STAFF,
            DefaultCatalog.CRYPT_MAIL,
        )


class DragonLair(Location):
    CODE = "dragon-lair"

    def __init__(self, catalog: ItemCatalog) -> None:
        super().__init__(self.CODE, "Логово дракона", 5, catalog)

    def _create_enemy(self) -> Enemy:
        return Dragon()

    def _get_loot_table(self) -> Sequence[str]:
        return (DefaultCatalog.DAWN_BLADE, DefaultCatalog.DRAGONSCALE_ARMOR)


class LocationRegistry:
    def __init__(self, locations: Sequence[Location]) -> None:
        self._locations: Dict[str, Location] = {loc.code: loc for loc in locations}

    def get(self, code: str) -> Location:
        location = self._locations.get(code)
        if location is None:
            raise UnknownCodeException("Локация", code)
        return location

    def get_all(self) -> List[Location]:
        return list(self._locations.values())


class Merchant:
    SELL_PRICE_PERCENT = 50

    def __init__(self, catalog: ItemCatalog, assortment: Sequence[str]) -> None:
        self._catalog = catalog
        self._assortment = tuple(assortment)

    def get_showcase(self) -> List[Item]:
        return [self._catalog.create(code) for code in self._assortment]

    def buy(self, hero: Hero, code: str) -> Item:
        if code not in self._assortment:
            raise UnknownCodeException("Товар", code)
        item = self._catalog.create(code)
        hero.spend_gold(item.price)
        hero.add_item(item)
        return item

    def sell(self, hero: Hero, item: Item) -> int:
        price = self.get_sell_price(item)
        hero.remove_item(item)
        hero.add_gold(price)
        return price

    def get_sell_price(self, item: Item) -> int:
        return item.price * self.SELL_PRICE_PERCENT // 100
