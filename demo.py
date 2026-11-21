from __future__ import annotations

from rpg.core import Dice
from rpg.entities import Hero, HeroClass
from rpg.items import DefaultCatalog, FIERY
from rpg.view import ConsoleView
from rpg.world import Crypt, Forest


def main() -> None:
    catalog = DefaultCatalog.create()
    view = ConsoleView()

    print("===== Одиночка =====")
    first = Dice.get_instance()
    second = Dice.get_instance()
    print(f"Dice.get_instance() возвращает один и тот же объект: {first is second}")

    print()
    print("===== Прототип =====")
    plain_sword = catalog.create(DefaultCatalog.IRON_SWORD)
    fiery_sword = catalog.create(DefaultCatalog.IRON_SWORD)
    fiery_sword.enchant(FIERY)
    print(f"Первая копия:        {view.describe_item(plain_sword)}")
    print(f"Вторая копия:        {view.describe_item(fiery_sword)}")
    print(f"Новая копия шаблона: {view.describe_item(catalog.create(DefaultCatalog.IRON_SWORD))}")
    print(f"Копии - разные объекты: {plain_sword is not fiery_sword}")

    print()
    print("===== Абстрактная фабрика =====")
    for hc in HeroClass:
        kit = hc.get_starter_kit(catalog)
        print(f"{hc.display_name}: {view.describe_item(kit.create_weapon())}, {view.describe_item(kit.create_armor())}")

    print()
    print("===== Строитель =====")
    hero = (
        Hero.Builder()
        .set_name("Артур")
        .set_hero_class(HeroClass.WARRIOR)
        .set_starter_kit(HeroClass.WARRIOR.get_starter_kit(catalog))
        .set_level(3)
        .build()
    )
    view.print_hero(hero)
    try:
        Hero.Builder().set_hero_class(HeroClass.MAGE).set_starter_kit(HeroClass.MAGE.get_starter_kit(catalog)).build()
    except ValueError as err:
        print(f"Герой без имени не создается: {err}")
    try:
        Hero.Builder().set_name("Мерлин").build()
    except ValueError as err:
        print(f"Герой без класса не создается: {err}")

    print()
    print("===== Фабричный метод =====")
    forest = Forest(catalog)
    crypt = Crypt(catalog)
    view.print_report(forest.explore(hero, seed=7), forest.display_name)
    print()
    view.print_report(crypt.explore(hero, seed=7), crypt.display_name)


if __name__ == "__main__":
    main()
