from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import List

from .core import BattleEvent, BattleReport, EventType, Outcome, Participant, Side
from .entities import Combatant


class Action(Enum):
    ATTACK = (1.0, 1.0)
    POWER_STRIKE = (1.5, 1.5)
    DEFEND = (0.5, 0.3)

    def __init__(self, attack_multiplier: float, incoming_multiplier: float) -> None:
        self.attack_multiplier = attack_multiplier
        self.incoming_multiplier = incoming_multiplier


class Tactic(ABC):
    """Паттерн Стратегия (Strategy): алгоритм выбора действия героя в каждом раунде."""

    @property
    @abstractmethod
    def code(self) -> str: ...

    @property
    @abstractmethod
    def display_name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def choose_action(self, round_num: int, hero: Combatant, enemy: Combatant) -> Action: ...


class BalancedTactic(Tactic):
    @property
    def code(self) -> str:
        return "balanced"

    @property
    def display_name(self) -> str:
        return "Баланс"

    @property
    def description(self) -> str:
        return "обычный удар каждый раунд"

    def choose_action(self, round_num: int, hero: Combatant, enemy: Combatant) -> Action:
        return Action.ATTACK


class AggressiveTactic(Tactic):
    @property
    def code(self) -> str:
        return "aggressive"

    @property
    def display_name(self) -> str:
        return "Натиск"

    @property
    def description(self) -> str:
        return "совершать безрассудные удары, пока у врага больше здоровья, чем у героя"

    def choose_action(self, round_num: int, hero: Combatant, enemy: Combatant) -> Action:
        return Action.POWER_STRIKE if enemy.health > hero.health else Action.ATTACK


class CautiousTactic(Tactic):
    LOW_HEALTH = 0.4

    @property
    def code(self) -> str:
        return "cautious"

    @property
    def display_name(self) -> str:
        return "Осторожность"

    @property
    def description(self) -> str:
        return "при здоровье ниже 40% через раунд уходить в оборону"

    def choose_action(self, round_num: int, hero: Combatant, enemy: Combatant) -> Action:
        wounded = hero.health < hero.max_health * self.LOW_HEALTH
        return Action.DEFEND if (wounded and round_num % 2 == 0) else Action.ATTACK


class Battle:
    def __init__(self, hero: Combatant, enemy: Combatant, tactic: Tactic) -> None:
        self._hero = hero
        self._enemy = enemy
        self._tactic = tactic
        self._events: List[BattleEvent] = []
        self._round = 0

    def run(self) -> BattleReport:
        while self._hero.is_alive() and self._enemy.is_alive():
            self._round += 1
            action = self._tactic.choose_action(self._round, self._hero, self._enemy)
            self._announce(action)

            self._strike(self._hero, Side.HERO, self._enemy, Side.ENEMY, action.attack_multiplier)
            if self._enemy.is_alive():
                self._strike(self._enemy, Side.ENEMY, self._hero, Side.HERO, action.incoming_multiplier)

        outcome = Outcome.VICTORY if self._hero.is_alive() else Outcome.DEFEAT
        return BattleReport(
            Participant.of(self._hero),
            Participant.of(self._enemy),
            outcome,
            tuple(self._events),
        )

    def _announce(self, action: Action) -> None:
        if action == Action.POWER_STRIKE:
            self._emit(BattleEvent(self._round, EventType.POWER_STRIKE, Side.HERO, Side.ENEMY, 0, 0))
        elif action == Action.DEFEND:
            self._emit(BattleEvent(self._round, EventType.DEFEND, Side.HERO, Side.HERO, 0, 0))

    def _strike(
        self,
        attacker: Combatant,
        source: Side,
        defender: Combatant,
        target: Side,
        multiplier: float,
    ) -> None:
        hit = attacker.roll_damage()
        amount = max(1, round(hit.damage * multiplier))
        damage = defender.receive_hit(amount)

        if damage.evaded:
            self._emit(BattleEvent(self._round, EventType.EVADE, source, target, 0, defender.health))
            return
        if damage.absorbed > 0:
            self._emit(BattleEvent(self._round, EventType.ABSORB, source, target, damage.absorbed, defender.health))
        if damage.amount > 0:
            event_type = EventType.CRITICAL_HIT if hit.critical else EventType.HIT
            self._emit(BattleEvent(self._round, event_type, source, target, damage.amount, defender.health))

        if not defender.is_alive():
            self._emit(BattleEvent(self._round, EventType.DEATH, source, target, 0, 0))

    def _emit(self, event: BattleEvent) -> None:
        self._events.append(event)
