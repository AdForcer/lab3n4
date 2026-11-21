from __future__ import annotations

from typing import Sequence

from rpg.core import Outcome
from rpg.entities import Hero, HeroClass
from rpg.items import DefaultCatalog, Item, ItemCatalog
from rpg.view import ConsoleView
from rpg.world import Crypt, DragonLair, Forest, LocationRegistry, Merchant

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


def create_hero(catalog: ItemCatalog) -> Hero:
    print("Создайте своего героя!")
    hero_classes = list(HeroClass)
    while True:
        print("Выберите класс:")
        for i, hc in enumerate(hero_classes, start=1):
            kit = hc.get_starter_kit(catalog)
            print(
                f"{i} - {hc.display_name} (здоровье {hc.base_health}): "
                f"{VIEW.describe_item(kit.create_weapon())}, {VIEW.describe_item(kit.create_armor())}"
            )
        idx = read_choice(len(hero_classes))
        if idx < 0:
            continue
        hc = hero_classes[idx]
        print("Введите имя:")
        name = input().strip()
        try:
            return Hero.Builder().set_name(name).set_hero_class(hc).set_starter_kit(hc.get_starter_kit(catalog)).build()
        except ValueError as err:
            print(f"Не получилось создать героя: {err}")


def main() -> None:
    catalog = DefaultCatalog.create()
    locations = LocationRegistry([Forest(catalog), Crypt(catalog), DragonLair(catalog)])
    merchant = Merchant(
        catalog,
        [
            DefaultCatalog.IRON_SWORD,
            DefaultCatalog.ELVEN_BOW,
            DefaultCatalog.EMBER_STAFF,
            DefaultCatalog.CHAINMAIL,
            DefaultCatalog.PLATE_ARMOR,
        ],
    )

    hero = create_hero(catalog)
    print(f"{hero.name} разбивает лагерь на опушке мистического леса.")

    while True:
        print()
        VIEW.print_hero(hero)
        print("1 - отправиться в экспедицию, 2 - снаряжение, 3 - торговец, 0 - выйти из игры")
        choice = input().strip()
        if choice == "1":
            all_locs = locations.get_all()
            print("Куда отправимся?")
            for i, loc in enumerate(all_locs, start=1):
                print(f"{i} - {loc.display_name} (рекомендуемый уровень {loc.recommended_level})")
            idx = read_choice(len(all_locs))
            if idx < 0:
                continue
            loc = all_locs[idx]
            report = loc.explore(hero)
            print()
            VIEW.print_report(report, loc.display_name)
            if report.battle.outcome == Outcome.VICTORY and loc.code == DragonLair.CODE:
                print(f"\nДракон повержен! Барды еще долго будут петь о подвиге героя по имени {hero.name}.")
        elif choice == "2":
            inv = hero.inventory
            if not inv:
                print("Инвентарь пуст")
                continue
            print("Что экипировать? (0 - назад)")
            print_items(inv)
            idx = read_choice(len(inv))
            if idx >= 0:
                item = inv[idx]
                hero.equip(item)
                print(f"Экипировано: {VIEW.describe_item(item)}")
        elif choice == "3":
            print(f'Торговец: "Чего желаешь?" (золото: {hero.gold})')
            print("1 - купить, 2 - продать, 0 - назад")
            sub = input().strip()
            if sub == "1":
                showcase = merchant.get_showcase()
                for i, item in enumerate(showcase, start=1):
                    print(f"{i} - {VIEW.describe_item(item)}: {item.price} золота")
                idx = read_choice(len(showcase))
                if idx >= 0:
                    try:
                        bought = merchant.buy(hero, showcase[idx].code)
                        print(f"Куплено: {VIEW.describe_item(bought)}")
                    except RuntimeError as err:
                        print(err)
            elif sub == "2":
                inv = hero.inventory
                if not inv:
                    print("Продавать нечего (экипированные предметы продать нельзя)")
                    continue
                for i, item in enumerate(inv, start=1):
                    print(f"{i} - {VIEW.describe_item(item)}: {merchant.get_sell_price(item)} золота")
                idx = read_choice(len(inv))
                if idx >= 0:
                    item = inv[idx]
                    price = merchant.sell(hero, item)
                    print(f"Продано: {item.name} за {price} золота")
        elif choice == "0":
            return
        else:
            print("Такого варианта нет")


if __name__ == "__main__":
    main()
