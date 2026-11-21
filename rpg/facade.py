from __future__ import annotations

from pathlib import Path
from typing import List

from .combat import AggressiveTactic, BalancedTactic, CautiousTactic, Tactic
from .core import ExpeditionReport, Outcome, UnknownCodeException
from .entities import Hero, HeroClass
from .events import (
    AchievementTracker,
    ExpeditionJournal,
    GameEvent,
    GameEventPublisher,
    GameEventType,
)
from .items import DefaultCatalog, Item
from .storage import CachingHeroRepository, FileHeroRepository, HeroRepository
from .world import (
    Crypt,
    DragonLair,
    Forest,
    HauntedManor,
    Location,
    LocationRegistry,
    Merchant,
)


class GameFacade:
    """Паттерн Фасад (Facade): единая простая точка входа ко всем подсистемам игры."""

    def __init__(self, save_file: Path) -> None:
        self._catalog = DefaultCatalog.create()
        self._locations = LocationRegistry([
            Forest(self._catalog),
            HauntedManor(self._catalog),
            Crypt(self._catalog),
            DragonLair(self._catalog),
        ])
        self._tactics: List[Tactic] = [
            BalancedTactic(),
            AggressiveTactic(),
            CautiousTactic(),
        ]
        self._merchant = Merchant(
            self._catalog,
            [
                DefaultCatalog.IRON_SWORD,
                DefaultCatalog.ELVEN_BOW,
                DefaultCatalog.EMBER_STAFF,
                DefaultCatalog.CHAINMAIL,
                DefaultCatalog.PLATE_ARMOR,
            ],
        )
        self._heroes: HeroRepository = CachingHeroRepository(
            FileHeroRepository(save_file, self._catalog)
        )

        self._events = GameEventPublisher()
        self._journal = ExpeditionJournal()
        achievements = AchievementTracker()
        self._events.subscribe(GameEventType.VICTORY, achievements)
        self._events.subscribe(GameEventType.LEVEL_UP, achievements)
        self._events.subscribe(GameEventType.VICTORY, self._journal)
        self._events.subscribe(GameEventType.DEFEAT, self._journal)

    def get_hero_classes(self) -> List[HeroClass]:
        return list(HeroClass)

    def get_starter_kit(self, hero_class_code: str) -> List[Item]:
        kit = HeroClass.by_code(hero_class_code).get_starter_kit(self._catalog)
        return [kit.create_weapon(), kit.create_armor()]

    def get_locations(self) -> List[Location]:
        return self._locations.get_all()

    def get_location(self, code: str) -> Location:
        return self._locations.get(code)

    def get_tactics(self) -> List[Tactic]:
        return list(self._tactics)

    def get_tactic(self, code: str) -> Tactic:
        for tactic in self._tactics:
            if tactic.code == code:
                return tactic
        raise UnknownCodeException("Тактика", code)

    def get_showcase(self) -> List[Item]:
        return self._merchant.get_showcase()

    def get_sell_price(self, item: Item) -> int:
        return self._merchant.get_sell_price(item)

    def get_heroes(self) -> List[Hero]:
        return self._heroes.find_all()

    def get_hero(self, name: str) -> Hero:
        hero = self._heroes.find_by_name(name)
        if hero is None:
            raise ValueError(f"Героя с именем {name} нет")
        return hero

    def create_hero(self, name: str, hero_class_code: str) -> Hero:
        if self._heroes.find_by_name(name) is not None:
            raise ValueError(f"Герой с именем {name} уже есть")
        hero_class = HeroClass.by_code(hero_class_code)
        hero = (
            Hero.Builder()
            .set_name(name)
            .set_hero_class(hero_class)
            .set_starter_kit(hero_class.get_starter_kit(self._catalog))
            .build()
        )
        self._heroes.save(hero)
        return hero

    def explore(self, hero_name: str, location_code: str, tactic_code: str) -> ExpeditionReport:
        hero = self.get_hero(hero_name)
        report = self._locations.get(location_code).explore(hero, self.get_tactic(tactic_code))

        result_event = (
            GameEventType.VICTORY
            if report.battle.outcome == Outcome.VICTORY
            else GameEventType.DEFEAT
        )
        self._events.publish(GameEvent(result_event, hero, report))
        if report.rewards.levels_gained > 0:
            self._events.publish(GameEvent(GameEventType.LEVEL_UP, hero, report))

        self._heroes.save(hero)
        return report

    def equip(self, hero_name: str, inventory_index: int) -> Item:
        hero = self.get_hero(hero_name)
        item = hero.inventory[inventory_index]
        hero.equip(item)
        self._heroes.save(hero)
        return item

    def buy(self, hero_name: str, item_code: str) -> Item:
        hero = self.get_hero(hero_name)
        item = self._merchant.buy(hero, item_code)
        self._heroes.save(hero)
        return item

    def sell(self, hero_name: str, inventory_index: int) -> int:
        hero = self.get_hero(hero_name)
        price = self._merchant.sell(hero, hero.inventory[inventory_index])
        self._heroes.save(hero)
        return price

    def get_journal(self, hero_name: str) -> List[ExpeditionReport]:
        return self._journal.get_entries(hero_name)
