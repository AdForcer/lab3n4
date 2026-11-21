from __future__ import annotations

from .core import BattleEvent, BattleReport, EventType, ExpeditionReport, Outcome, Participant, Rewards, Side
from .entities import Hero
from .items import Item


class ConsoleView:
    def describe_item(self, item: Item) -> str:
        text = item.name
        if item.enchantments:
            ench_names = ", ".join(e.name for e in item.enchantments)
            text += f" [{ench_names}]"
        return f"{text} ({item.get_description()})"

    def print_hero(self, hero: Hero) -> None:
        print(
            f"{hero.name}, {hero.hero_class.display_name} {hero.level} ур. | "
            f"здоровье {hero.max_health} | опыт {hero.experience}/{hero.experience_to_next_level} | "
            f"золото {hero.gold}"
        )
        print(f"  Оружие: {self.describe_item(hero.weapon)}")
        print(f"  Броня:  {self.describe_item(hero.armor)}")

    def print_report(self, report: ExpeditionReport, location_name: str) -> None:
        battle = report.battle
        print(f"=== {location_name} (сид {report.seed}) ===")
        print(f"{battle.hero.name} встречает врага: {battle.enemy.name} ({battle.enemy.max_health} здоровья)")
        for event in battle.events:
            self._print_event(event, battle)
        self._print_rewards(battle, report.rewards)

    def _print_event(self, event: BattleEvent, battle: BattleReport) -> None:
        source = self._participant(event.source, battle)
        target = self._participant(event.target, battle)
        if event.type == EventType.HIT:
            print(
                f"[раунд {event.round}] {source.name} -> {target.name}: "
                f"{event.amount} урона, осталось {event.target_health_after}/{target.max_health}"
            )
        elif event.type == EventType.CRITICAL_HIT:
            print(
                f"[раунд {event.round}] {source.name} -> {target.name}: "
                f"КРИТ! {event.amount} урона, осталось {event.target_health_after}/{target.max_health}"
            )
        elif event.type == EventType.DEATH:
            print(f"{target.name} повержен!")

    def _print_rewards(self, battle: BattleReport, rewards: Rewards) -> None:
        if battle.outcome == Outcome.DEFEAT:
            print(f"Поражение... {battle.hero.name} едва уносит ноги и теряет {-rewards.gold} золота")
            return
        print(f"Победа! +{rewards.experience} опыта, +{rewards.gold} золота")
        if rewards.loot is not None:
            print(f"Добыча: {self.describe_item(rewards.loot)}")
        if rewards.levels_gained > 0:
            print("Новый уровень!")

    @staticmethod
    def _participant(side: Side, battle: BattleReport) -> Participant:
        return battle.hero if side == Side.HERO else battle.enemy
