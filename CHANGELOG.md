# Changelog

## 0.1.0 — 2026-10-29
Перший реліз.
- Скіл `demo-walkthrough-carousel`: від сценарію через дизайн-канвас до однієї клікабельної каруселі. Скрипт `make_carousel.py` бере екрани, підписи й меню з `carousel.json`, а формат екранів описаний у SKILL.md.
- Агент `demo-effort-estimator`: режими `estimate`, `record` і `learn`. Стартова модель (`seed_version` 0.1.0) — це тільки ціни: `scale_k` 0.55, коефіцієнт епохи «до плагіна» 2.59, правила підрахунку v2. Журнал порожній. Усі дані користувача лишаються локально в `~/.claude/demo-effort/`.
- Шаблони issues для публічного репозиторію: Carousel feedback, Estimate vs fact, Model correction. У них немає полів для назв клієнтів.
