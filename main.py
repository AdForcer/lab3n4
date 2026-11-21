from __future__ import annotations

from pathlib import Path
from typing import Sequence

from rpg.core import Outcome
from rpg.facade import GameFacade
from rpg.items import Item
from rpg.view import ConsoleView

SAVE_FILE = Path("saves") / "heroes.json"
VIEW = ConsoleView()


def read_choice(count: int) -> int:
    try:
        choice = int(input().strip())
        if 1 <= choice <= count:
            return choice - 1
    except ValueError:
        pass
    return -1


def print_items(items: Sequence[Item]) -> None:
    for i, item in enumerate(items, start=1):
        print(f"{i} - {VIEW.describe_item(item)}")


def create_hero(game: GameFacade) -> str:
    print("Создайте своего героя!")
    while True:
        print("Выберите класс:")
        hero_classes = game.get_hero_classes()
        for i, hc in enumerate(hero_classes, start=1):
            kit = game.get_starter_kit(hc.code)
            print(
                f"{i} - {hc.display_name} (здоровье {hc.base_health}, {VIEW.describe_class(hc)}): "
                f"{VIEW.describe_item(kit[0])}, {VIEW.describe_item(kit[1])}"
            )
        class_index = read_choice(len(hero_classes))
        if class_index < 0:
            continue

        print("Введите имя:")
        name = input().strip()
        try:
            return game.create_hero(name, hero_classes[class_index].code).name
        except ValueError as err:
            print(f"Не получилось создать героя: {err}")


def choose_hero(game: GameFacade) -> str:
    saved = game.get_heroes()
    if saved:
        print("Выберите героя (0 - создать нового):")
        for i, hero in enumerate(saved, start=1):
            print(f"{i} - {hero.name}, {hero.hero_class.display_name} {hero.level} ур.")
        index = read_choice(len(saved))
        if index >= 0:
            name = saved[index].name
            print(f"{name} возвращается в лагерь на опушке мистического леса.")
            return name

    name = create_hero(game)
    print(f"{name} разбивает лагерь на опушке мистического леса.")
    return name


def go_on_expedition(game: GameFacade, hero_name: str) -> None:
    locations = game.get_locations()
    print("Куда отправимся?")
    for i, loc in enumerate(locations, start=1):
        print(f"{i} - {loc.display_name} (рекомендуемый уровень {loc.recommended_level})")
    loc_index = read_choice(len(locations))
    if loc_index < 0:
        return

    tactics = game.get_tactics()
    print("Какой тактики держаться в бою?")
    for i, tactic in enumerate(tactics, start=1):
        print(f"{i} - {tactic.display_name}: {tactic.description}")
    tactic_index = read_choice(len(tactics))
    if tactic_index < 0:
        return

    location = locations[loc_index]
    report = game.explore(hero_name, location.code, tactics[tactic_index].code)
    print()
    VIEW.print_report(report, location.display_name)
    if report.battle.outcome == Outcome.VICTORY and report.battle.enemy.code == "dragon":
        print(f"\nДракон повержен! Барды еще долго будут петь о подвиге героя по имени {hero_name}.")


def manage_equipment(game: GameFacade, hero_name: str) -> None:
    inventory = game.get_hero(hero_name).inventory
    if not inventory:
        print("Инвентарь пуст")
        return
    print("Что экипировать? (0 - назад)")
    print_items(inventory)
    index = read_choice(len(inventory))
    if index < 0:
        return
    item = game.equip(hero_name, index)
    print(f"Экипировано: {VIEW.describe_item(item)}")


def visit_merchant(game: GameFacade, hero_name: str) -> None:
    print(f'Торговец: "Чего желаешь?" (золото: {game.get_hero(hero_name).gold})')
    print("1 - купить, 2 - продать, 0 - назад")
    choice = input().strip()
    if choice == "1":
        showcase = game.get_showcase()
        for i, item in enumerate(showcase, start=1):
            print(f"{i} - {VIEW.describe_item(item)}: {item.price} золота")
        index = read_choice(len(showcase))
        if index < 0:
            return
        try:
            bought = game.buy(hero_name, showcase[index].code)
            print(f"Куплено: {VIEW.describe_item(bought)}")
        except RuntimeError as err:
            print(err)
    elif choice == "2":
        inventory = game.get_hero(hero_name).inventory
        if not inventory:
            print("Продавать нечего (экипированные предметы продать нельзя)")
            return
        for i, item in enumerate(inventory, start=1):
            print(f"{i} - {VIEW.describe_item(item)}: {game.get_sell_price(item)} золота")
        index = read_choice(len(inventory))
        if index < 0:
            return
        item_name = inventory[index].name
        price = game.sell(hero_name, index)
        print(f"Продано: {item_name} за {price} золота")


def print_journal(game: GameFacade, hero_name: str) -> None:
    journal = game.get_journal(hero_name)
    if not journal:
        print("В этот раз экспедиций еще не было")
        return
    for i, report in enumerate(journal, start=1):
        summary = VIEW.summarize(
            report,
            game.get_location(report.location_code).display_name,
            game.get_tactic(report.tactic_code).display_name,
        )
        print(f"{i}. {summary}")


def main() -> None:
    print(f"Файл сохранения: {SAVE_FILE.resolve()}")
    game = GameFacade(SAVE_FILE)
    hero_name = choose_hero(game)

    while True:
        print()
        VIEW.print_hero(game.get_hero(hero_name))
        print("1 - отправиться в экспедицию, 2 - снаряжение, 3 - торговец, 4 - журнал экспедиций, 0 - выйти из игры")
        choice = input().strip()
        if choice == "1":
            go_on_expedition(game, hero_name)
        elif choice == "2":
            manage_equipment(game, hero_name)
        elif choice == "3":
            visit_merchant(game, hero_name)
        elif choice == "4":
            print_journal(game, hero_name)
        elif choice == "0":
            return
        else:
            print("Такого варианта нет")


if __name__ == "__main__":
    main()
