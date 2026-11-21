from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .core import Dice


class Damage:
    """Контейнер данных об уроне, проходящий по цепочке обязанностей."""

    def __init__(self, amount: int) -> None:
        self._amount = amount
        self._evaded = False
        self._absorbed = 0

    def reduce_to(self, amount: int) -> None:
        self._amount = amount

    def evade(self) -> None:
        self._amount = 0
        self._evaded = True

    def absorb(self, value: int) -> None:
        self._amount -= value
        self._absorbed += value

    @property
    def amount(self) -> int:
        return self._amount

    @property
    def evaded(self) -> bool:
        return self._evaded

    @property
    def absorbed(self) -> int:
        return self._absorbed


class DamageHandler(ABC):
    """Паттерн Цепочка обязанностей (Chain of Responsibility): базовое звено защиты."""

    def __init__(self) -> None:
        self._next: Optional[DamageHandler] = None

    def set_next(self, handler: DamageHandler) -> DamageHandler:
        self._next = handler
        return handler

    @abstractmethod
    def handle(self, damage: Damage) -> None:
        ...

    def _pass_to_next(self, damage: Damage) -> None:
        if self._next is not None:
            self._next.handle(damage)


class EvasionHandler(DamageHandler):
    """Уклонение: при срабатывании обнуляет урон и останавливает цепочку."""

    def __init__(self, chance: float) -> None:
        super().__init__()
        self._chance = chance

    def handle(self, damage: Damage) -> None:
        if Dice.get_instance().chance(self._chance):
            damage.evade()
            return
        self._pass_to_next(damage)


class ArmorHandler(DamageHandler):
    """Броня: уменьшает урон пропорционально защите (минимум 1)."""

    def __init__(self, defense: float) -> None:
        super().__init__()
        self._defense = defense

    def handle(self, damage: Damage) -> None:
        reduced = round(damage.amount * (1 - self._defense))
        damage.reduce_to(max(1, reduced))
        self._pass_to_next(damage)


class BarrierHandler(DamageHandler):
    """Магический барьер: поглощает урон, пока есть запас прочности."""

    def __init__(self, strength: int) -> None:
        super().__init__()
        self._strength = strength

    def handle(self, damage: Damage) -> None:
        absorbed = min(self._strength, damage.amount)
        if absorbed > 0:
            self._strength -= absorbed
            damage.absorb(absorbed)
        self._pass_to_next(damage)
