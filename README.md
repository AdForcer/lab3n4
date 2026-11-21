# Лабораторная работа 4 — Структурные и поведенческие шаблоны проектирования (Python)

Реализация консольной RPG-игры на Python 3 (без внешних зависимостей — только стандартная библиотека).

## Запуск

Демонстрация всех 7 паттернов Лабы 4 одним запуском:
```bash
python demo.py
```

Запуск интерактивной консольной игры:
```bash
python main.py
```

## Реализованные паттерны

### Структурные паттерны (Лаба 4)
1. **Декоратор (Decorator)** — `rpg/entities.py` (`EnemyDecorator`, `LegendaryEnemy`, `WindfuryEnemy`, `ArmoredEnemy`).
2. **Заместитель (Proxy)** — `rpg/storage.py` (`HeroRepository`, `FileHeroRepository`, `CachingHeroRepository`).
3. **Адаптер (Adapter)** — `rpg/entities.py` (`HauntedWeapon`) и `rpg/world.py` (`HauntedManor`).
4. **Фасад (Facade)** — `rpg/facade.py` (`GameFacade`).

### Поведенческие паттерны (Лаба 4)
5. **Стратегия (Strategy)** — `rpg/combat.py` (`Tactic`, `BalancedTactic`, `AggressiveTactic`, `CautiousTactic`, `Battle`).
6. **Наблюдатель (Observer)** — `rpg/events.py` (`GameEventPublisher`, `GameEventListener`, `AchievementTracker`, `ExpeditionJournal`).
7. **Цепочка обязанностей (Chain of Responsibility)** — `rpg/defense.py` (`Damage`, `DamageHandler`, `EvasionHandler`, `ArmorHandler`, `BarrierHandler`).

### Порождающие паттерны (база из Лабы 3)
- **Одиночка (Singleton)** — `rpg/core.py` (`Dice`).
- **Прототип (Prototype)** — `rpg/items.py` (`Item.copy`, `ItemCatalog`).
- **Абстрактная фабрика (Abstract Factory)** — `rpg/items.py` (`StarterKitFactory` и фабрики классов).
- **Строитель (Builder)** — `rpg/entities.py` (`Hero.Builder`).
- **Фабричный метод (Factory Method)** — `rpg/world.py` (`Location._create_enemy`).
