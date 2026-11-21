from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Sequence, TypeVar

if TYPE_CHECKING:
    from .entities import Combatant
    from .items import Item

T = TypeVar("T")


class UnknownCodeException(ValueError):
    def __init__(self, what: str, code: str) -> None:
        super().__init__(f"{what} с кодом '{code}' не существует")


class Dice:
    """Паттерн Одиночка (Singleton): общий генератор случайности на всю игру."""

    _instance: Optional[Dice] = None

    def __init__(self) -> None:
        self._random = random.Random()

    @classmethod
    def get_instance(cls) -> Dice:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def reseed(self, seed: int) -> None:
        self._random.seed(seed)

    def next_seed(self) -> int:
        return self._random.randint(0, 999_999)

    def roll(self, min_val: int, max_val: int) -> int:
        return self._random.randint(min_val, max_val)

    def chance(self, probability: float) -> bool:
        return self._random.random() < probability

    def pick(self, options: Sequence[T]) -> T:
        return self._random.choice(options)


@dataclass(frozen=True)
class Hit:
    damage: int
    critical: bool


class Side(Enum):
    HERO = "HERO"
    ENEMY = "ENEMY"


class EventType(Enum):
    HIT = "HIT"
    CRITICAL_HIT = "CRITICAL_HIT"
    EVADE = "EVADE"
    ABSORB = "ABSORB"
    POWER_STRIKE = "POWER_STRIKE"
    DEFEND = "DEFEND"
    DEATH = "DEATH"


class Outcome(Enum):
    VICTORY = "VICTORY"
    DEFEAT = "DEFEAT"


@dataclass(frozen=True)
class BattleEvent:
    round: int
    type: EventType
    source: Side
    target: Side
    amount: int
    target_health_after: int


@dataclass(frozen=True)
class Participant:
    code: str
    name: str
    max_health: int

    @classmethod
    def of(cls, combatant: Combatant) -> Participant:
        return cls(combatant.code, combatant.name, combatant.max_health)


@dataclass(frozen=True)
class BattleReport:
    hero: Participant
    enemy: Participant
    outcome: Outcome
    events: tuple[BattleEvent, ...]


@dataclass(frozen=True)
class Rewards:
    experience: int
    gold: int
    loot: Optional[Item]
    levels_gained: int


@dataclass(frozen=True)
class ExpeditionReport:
    seed: int
    location_code: str
    tactic_code: str
    battle: BattleReport
    rewards: Rewards
