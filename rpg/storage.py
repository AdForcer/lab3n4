from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from .entities import Achievement, Hero, HeroClass
from .items import Armor, Enchantment, Item, ItemCatalog, Weapon


class HeroRepository(ABC):
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Hero]: ...

    @abstractmethod
    def find_all(self) -> List[Hero]: ...

    @abstractmethod
    def save(self, hero: Hero) -> None: ...


class FileHeroRepository(HeroRepository):
    """Сохраняет и загружает героев из JSON-файла."""

    def __init__(self, file_path: Path, catalog: ItemCatalog) -> None:
        self._file = file_path
        self._catalog = catalog

    def find_by_name(self, name: str) -> Optional[Hero]:
        for hero in self.find_all():
            if hero.name == name:
                return hero
        return None

    def find_all(self) -> List[Hero]:
        if not self._file.exists():
            return []
        text = self._file.read_text(encoding="utf-8").strip()
        if not text:
            return []
        raw_saves = json.loads(text)
        if not isinstance(raw_saves, list):
            raise ValueError(f"Ожидался массив героев: {self._file.resolve()}")
        return [self._restore(save) for save in raw_saves]

    def save(self, hero: Hero) -> None:
        saves = [self._snapshot(saved) for saved in self.find_all() if saved.name != hero.name]
        saves.append(self._snapshot(hero))
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(
            json.dumps(saves, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _snapshot(self, hero: Hero) -> Dict[str, Any]:
        return {
            "name": hero.name,
            "heroClass": hero.hero_class.code,
            "level": hero.level,
            "experience": hero.experience,
            "gold": hero.gold,
            "weapon": self._snapshot_item(hero.weapon),
            "armor": self._snapshot_item(hero.armor),
            "inventory": [self._snapshot_item(item) for item in hero.inventory],
            "achievements": [ach.code for ach in hero.achievements],
        }

    def _snapshot_item(self, item: Item) -> Dict[str, Any]:
        return {
            "code": item.code,
            "enchantments": [e.code for e in item.enchantments],
        }

    def _restore(self, save: Dict[str, Any]) -> Hero:
        weapon = self._restore_item(save["weapon"])
        armor = self._restore_item(save["armor"])
        if not isinstance(weapon, Weapon) or not isinstance(armor, Armor):
            raise ValueError("Некорректные типы снаряжения в сохранении")
        return (
            Hero.Builder()
            .set_name(save["name"])
            .set_hero_class(HeroClass.by_code(save["heroClass"]))
            .set_level(save["level"])
            .set_experience(save["experience"])
            .set_gold(save["gold"])
            .set_weapon(weapon)
            .set_armor(armor)
            .set_inventory([self._restore_item(i) for i in save["inventory"]])
            .set_achievements([Achievement.by_code(c) for c in save["achievements"]])
            .build()
        )

    def _restore_item(self, save: Dict[str, Any]) -> Item:
        item = self._catalog.create(save["code"])
        for ench_code in save["enchantments"]:
            item.enchant(Enchantment.by_code(ench_code))
        return item


class CachingHeroRepository(HeroRepository):
    """Паттерн Заместитель (Proxy): ленивое кэширование обращений к хранилищу."""

    def __init__(self, target: HeroRepository) -> None:
        self._target = target
        self._cache: Optional[Dict[str, Hero]] = None

    def find_by_name(self, name: str) -> Optional[Hero]:
        return self._cached().get(name)

    def find_all(self) -> List[Hero]:
        return list(self._cached().values())

    def save(self, hero: Hero) -> None:
        self._target.save(hero)
        self._cached()[hero.name] = hero

    def _cached(self) -> Dict[str, Hero]:
        if self._cache is None:
            self._cache = {hero.name: hero for hero in self._target.find_all()}
        return self._cache
