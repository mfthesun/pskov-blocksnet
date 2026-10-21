---
description: Безопасно отправить проект в свой репозиторий GitHub (без force push)
argument-hint: <https-адрес пустого репозитория>
---
Перенеси проект в репозиторий пользователя: $ARGUMENTS

Правила: **никакого force push**, не меняй код, не коммить секреты.

1. `git status` и `git remote -v`. Если репозиторий не инициализирован — `git init -b main`.
2. Проверь `.gitignore`: исключены `.venv/`, `.env`, `data/cache/`, `*.pbf`, `*.pickle`, `*.parquet`. Найди крупные файлы: `git ls-files -s | ...` или `du -sh data/*`. Файлы > 50 МБ не коммить — предложи ссылку в README.
3. Проверь, что в индекс не попали секреты (`grep -rIl "api_key\|token\|password" --exclude-dir=.venv .`).
4. Если `origin` есть — `git remote set-url origin <адрес>`, иначе `git remote add origin <адрес>`. Покажи `git remote -v`.
5. `git add -A`, покажи `git status --short`, предложи сообщение коммита и спроси подтверждение.
6. `git commit -m "..."`, затем `git push -u origin main` (или текущая ветка). Если push отклонён — остановись и объясни, не используй `--force`.
