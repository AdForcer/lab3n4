from __future__ import annotations

from .core import BattleEvent, BattleReport, EventType, ExpeditionReport, Outcome, Participant, Rewards, Side
from .entities import Hero, HeroClass
from .items import Item


class ConsoleView:
    def describe_item(self, item: Item) -> str:
        text = item.name
        if item.enchantments:
            ench_names = ", ".join(e.name for e in item.enchantments)
            text += f" [{ench_names}]"
        return f"{text} ({item.get_description()})"

    def describe_class(self, hero_class: HeroClass) -> str:
        if hero_class.evasion > 0:
            return f"уклонение {round(hero_class.evasion * 100)}%"
        if hero_class.barrier > 0:
            return f"магический барьер {hero_class.barrier}"
        return "без особенностей"

    def print_hero(self, hero: Hero) -> None:
        print(
            f"{hero.name}, {hero.hero_class.display_name} {hero.level} ур. | "
            f"здоровье {hero.max_health} | опыт {hero.experience}/{hero.experience_to_next_level} | "
            f"золото {hero.gold}"
        )
        print(f"  Оружие: {self.describe_item(hero.weapon)}")
        print(f"  Броня:  {self.describe_item(hero.armor)}")
        if hero.achievements:
            names = ", ".join(a.display_name for a in hero.achievements)
            print(f"  Достижения: {names}")

    def print_report(self, report: ExpeditionReport, location_name: str) -> None:
        battle = report.battle
        print(f"=== {location_name} (сид {report.seed}) ===")
        print(f"{battle.hero.name} встречает врага: {battle.enemy.name} ({battle.enemy.max_health} здоровья)")
        for event in battle.events:
            self._print_event(event, battle)
        self._print_rewards(battle, report.rewards)

    def summarize(self, report: ExpeditionReport, location_name: str, tactic_name: str) -> str:
        result = "победа" if report.battle.outcome == Outcome.VICTORY else "поражение"
        return f'{location_name}, {report.battle.enemy.name}, тактика "{tactic_name}": {result}'

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
        elif event.type == EventType.EVADE:
            print(f"[раунд {event.round}] {source.name} -> {target.name}: промах, {target.name} уклоняется")
        elif event.type == EventType.ABSORB:
            print(f"[раунд {event.round}] {source.name} -> {target.name}: барьер поглощает {event.amount} урона")
        elif event.type == EventType.POWER_STRIKE:
            print(f"[раунд {event.round}] {source.name} бьет в полную силу")
        elif event.type == EventType.DEFEND:
            print(f"[раунд {event.round}] {source.name} уходит в оборону")
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
