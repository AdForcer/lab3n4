from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from .core import ExpeditionReport
from .entities import Achievement, Hero


class GameEventType(Enum):
    VICTORY = "VICTORY"
    DEFEAT = "DEFEAT"
    LEVEL_UP = "LEVEL_UP"


@dataclass(frozen=True)
class GameEvent:
    type: GameEventType
    hero: Hero
    expedition: ExpeditionReport


class GameEventListener(ABC):
    """Паттерн Наблюдатель (Observer): интерфейс подписчика."""

    @abstractmethod
    def on_event(self, event: GameEvent) -> None:
        ...


class GameEventPublisher:
    """Паттерн Наблюдатель (Observer): издатель игровых событий."""

    def __init__(self) -> None:
        self._listeners: Dict[GameEventType, List[GameEventListener]] = {}

    def subscribe(self, event_type: GameEventType, listener: GameEventListener) -> None:
        self._listeners.setdefault(event_type, []).append(listener)

    def unsubscribe(self, event_type: GameEventType, listener: GameEventListener) -> None:
        subscribed = self._listeners.get(event_type)
        if subscribed and listener in subscribed:
            subscribed.remove(listener)

    def publish(self, event: GameEvent) -> None:
        for listener in list(self._listeners.get(event.type, [])):
            listener.on_event(event)


class AchievementTracker(GameEventListener):
    """Подписчик, выдающий достижения герою."""

    VETERAN_LEVEL = 5

    def on_event(self, event: GameEvent) -> None:
        hero = event.hero
        if event.type == GameEventType.VICTORY:
            hero.unlock(Achievement.FIRST_BLOOD)
            if event.expedition.battle.enemy.code == "dragon":
                hero.unlock(Achievement.DRAGON_SLAYER)
            loot = event.expedition.rewards.loot
            if loot is not None and len(loot.enchantments) > 0:
                hero.unlock(Achievement.LUCKY)
        elif event.type == GameEventType.LEVEL_UP and hero.level >= self.VETERAN_LEVEL:
            hero.unlock(Achievement.VETERAN)


class ExpeditionJournal(GameEventListener):
    """Подписчик, ведущий журнал экспедиций."""

    def __init__(self) -> None:
        self._entries: Dict[str, List[ExpeditionReport]] = {}

    def on_event(self, event: GameEvent) -> None:
        self._entries.setdefault(event.hero.name, []).append(event.expedition)

    def get_entries(self, hero_name: str) -> List[ExpeditionReport]:
        return list(self._entries.get(hero_name, []))
