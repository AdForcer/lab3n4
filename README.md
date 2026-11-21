# Лабораторная работа 3 — Порождающие шаблоны проектирования (Python)

Консольная текстовая RPG на Python 3 с реализацией 5 порождающих паттернов:
1. Одиночка (Singleton) — `rpg/core.py` (`Dice`)
2. Прототип (Prototype) — `rpg/items.py` (`Item.copy`, `ItemCatalog`)
3. Абстрактная фабрика (Abstract Factory) — `rpg/items.py` (`StarterKitFactory`)
4. Строитель (Builder) — `rpg/entities.py` (`Hero.Builder`)
5. Фабричный метод (Factory Method) — `rpg/world.py` (`Location._create_enemy`)

## Запуск
```bash
python demo.py
python main.py
```
