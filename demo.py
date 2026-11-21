from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List

from rpg.combat import AggressiveTactic, BalancedTactic, CautiousTactic, Tactic
from rpg.core import Dice, ExpeditionReport, Outcome
from rpg.defense import ArmorHandler, BarrierHandler, Damage, DamageHandler, EvasionHandler
from rpg.entities import (
    ArmoredEnemy,
    Dragon,
    Enemy,
    Goblin,
    HauntedWeapon,
    Hero,
    HeroClass,
    LegendaryEnemy,
    WindfuryEnemy,
)
from rpg.events import (
    AchievementTracker,
    ExpeditionJournal,
    GameEvent,
    GameEventListener,
    GameEventPublisher,
    GameEventType,
)
from rpg.facade import GameFacade
from rpg.items import DefaultCatalog, ItemCatalog
from rpg.storage import CachingHeroRepository, FileHeroRepository, HeroRepository
from rpg.view import ConsoleView
from rpg.world import Crypt, Forest, HauntedManor

VIEW = ConsoleView()


class PrintVictoryListener(GameEventListener):
    def on_event(self, event: GameEvent) -> None:
        print(f"Событие {event.type.value}: герой {event.hero.name}")


def new_hero(name: str, hero_class: HeroClass, level: int, catalog: ItemCatalog) -> Hero:
    return (
        Hero.Builder()
        .set_name(name)
        .set_hero_class(hero_class)
        .set_starter_kit(hero_class.get_starter_kit(catalog))
        .set_level(level)
        .build()
    )


def print_hits(title: str, chain: DamageHandler, count: int) -> None:
    results: List[str] = []
    for _ in range(count):
        damage = Damage(30)
        chain.handle(damage)
        if damage.evaded:
            results.append("уклонение")
        elif damage.absorbed > 0:
            results.append(f"поглощено {damage.absorbed}, прошло {damage.amount}")
        else:
            results.append(f"прошло {damage.amount}")
    print(f"{title}: {'; '.join(results)}")


def describe_outcome(report: ExpeditionReport) -> str:
    return "победа" if report.battle.outcome == Outcome.VICTORY else "поражение"


def count_rounds(report: ExpeditionReport) -> int:
    return report.battle.events[-1].round


def main() -> None:
    catalog = DefaultCatalog.create()
    dice = Dice.get_instance()

    print("===== Цепочка обязанностей =====")
    armor_only = ArmorHandler(0.3)
    print_hits("Броня 30%", armor_only, 2)

    armor_and_barrier = ArmorHandler(0.3)
    armor_and_barrier.set_next(BarrierHandler(30))
    print_hits("Броня 30% -> барьер 30", armor_and_barrier, 3)

    dice.reseed(3)
    full_chain = EvasionHandler(0.5)
    full_chain.set_next(ArmorHandler(0.3)).set_next(BarrierHandler(30))
    print_hits("Уклонение 50% -> броня 30% -> барьер 30", full_chain, 3)

    print()
    print("===== Стратегия =====")
    crypt = Crypt(catalog)
    tactics: List[Tactic] = [BalancedTactic(), AggressiveTactic(), CautiousTactic()]
    for tactic in tactics:
        mage = new_hero("Мерлин", HeroClass.MAGE, 2, catalog)
        report = crypt.explore(mage, tactic, seed=3)
        print(
            f"{tactic.display_name}: {describe_outcome(report)}, "
            f"раундов {count_rounds(report)}, "
            f"у героя осталось {mage.health}/{mage.max_health} здоровья"
        )

    print()
    print("===== Декоратор =====")
    enemies: List[Enemy] = [
        Goblin(),
        LegendaryEnemy(Goblin()),
        WindfuryEnemy(Goblin()),
        LegendaryEnemy(WindfuryEnemy(Goblin())),
        ArmoredEnemy(Goblin()),
        ArmoredEnemy(LegendaryEnemy(WindfuryEnemy(Dragon()))),
    ]
    for enemy in enemies:
        dice.reseed(5)
        hits = [str(enemy.roll_damage().damage) for _ in range(3)]
        received = enemy.receive_hit(20)
        print(
            f"{enemy.name}: удары {', '.join(hits)}, награда {enemy.get_experience_reward()} опыта; "
            f"входящий урон 20 -> {received.amount}, здоровье {enemy.health}/{enemy.max_health}"
        )

    print()
    print("===== Адаптер =====")
    bow = catalog.create_weapon(DefaultCatalog.ELVEN_BOW)
    haunted_bow: Enemy = HauntedWeapon(bow)
    print(f"Предмет: {VIEW.describe_item(bow)}")
    print(
        f"Враг:    {haunted_bow.name} "
        f"({haunted_bow.max_health} здоровья, награда {haunted_bow.get_experience_reward()} опыта)"
    )
    manor = HauntedManor(catalog)
    ranger = new_hero("Леголас", HeroClass.RANGER, 2, catalog)
    VIEW.print_report(manor.explore(ranger, CautiousTactic(), seed=55), manor.display_name)

    print()
    print("===== Наблюдатель =====")
    events = GameEventPublisher()
    journal = ExpeditionJournal()
    achievements = AchievementTracker()
    events.subscribe(GameEventType.VICTORY, achievements)
    events.subscribe(GameEventType.VICTORY, journal)
    events.subscribe(GameEventType.DEFEAT, journal)
    events.subscribe(GameEventType.VICTORY, PrintVictoryListener())

    warrior = new_hero("Артур", HeroClass.WARRIOR, 1, catalog)
    forest = Forest(catalog)
    victory = forest.explore(warrior, BalancedTactic(), seed=7)
    events.publish(GameEvent(GameEventType.VICTORY, warrior, victory))
    ach_names = ", ".join(a.display_name for a in warrior.achievements)
    print(f"Достижения героя: {ach_names}")
    print(f"Записей в журнале: {len(journal.get_entries(warrior.name))}")

    print()
    print("===== Заместитель =====")
    with tempfile.TemporaryDirectory() as tmp_dir:
        save_file = Path(tmp_dir) / "heroes.json"
        file_repo: HeroRepository = FileHeroRepository(save_file, catalog)
        file_repo.save(warrior)
        print("Содержимое файла:")
        print(save_file.read_text(encoding="utf-8"), end="")

        same_without_proxy = file_repo.find_by_name("Артур") is file_repo.find_by_name("Артур")
        print(f"Без заместителя два поиска дают один и тот же объект: {same_without_proxy}")

        cached: HeroRepository = CachingHeroRepository(file_repo)
        from_cache = cached.find_by_name("Артур")
        assert from_cache is not None
        same_with_proxy = from_cache is cached.find_by_name("Артур")
        print(f"С заместителем два поиска дают один и тот же объект: {same_with_proxy}")

        from_cache.add_gold(100)
        cached.save(from_cache)
        reloaded = file_repo.find_by_name("Артур")
        assert reloaded is not None
        print(f"После сохранения через заместитель золото героя в файле: {reloaded.gold}")

    print()
    print("===== Фасад =====")
    with tempfile.TemporaryDirectory() as tmp_dir:
        game_file = Path(tmp_dir) / "game.json"
        game = GameFacade(game_file)
        game.create_hero("Гэндальф", HeroClass.MAGE.code)
        dice.reseed(11)
        expedition = game.explore("Гэндальф", Forest.CODE, "cautious")
        summary = VIEW.summarize(
            expedition,
            game.get_location(expedition.location_code).display_name,
            game.get_tactic(expedition.tactic_code).display_name,
        )
        print(f"Экспедиция через фасад: {summary}")
        VIEW.print_hero(game.get_hero("Гэндальф"))


if __name__ == "__main__":
    main()
