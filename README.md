# Лесная Чашка — сайт промоакции

React (Vite) → Django → PostgreSQL. Бренд, компания и все данные вымышленные.
Настройки для локального запуска — в `backend/.env`, все значения тестовые.

## База данных

В папке `database/` — готовый дамп базы с данными первых 4 недель акции (01.12–27.12.2026).
Нужен PostgreSQL 14 или новее: https://www.postgresql.org/download/
(на Windows установщик спросит пароль пользователя `postgres` — запомните его).

### 1. Создать пользователя и базу

Скрипт `setup_db.sql` создаёт пользователя `lesnaya` и базу `lesnaya_chashka_v2` — с теми же данными, что в `backend/.env`.

Windows (PowerShell; номер версии в пути может отличаться):

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -f setup_db.sql
```

macOS:

```bash
psql -d postgres -f setup_db.sql
```

Linux:

```bash
sudo -u postgres psql < setup_db.sql
```

### 2. Загрузить данные

Пароль пользователя `lesnaya` — `lesnaya-local-2026`.

Windows:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U lesnaya -d lesnaya_chashka_v2 -f database\lesnaya_chashka.sql
```

macOS / Linux:

```bash
psql -h localhost -U lesnaya -d lesnaya_chashka_v2 -f database/lesnaya_chashka.sql
```

### Вариант через Docker

Если PostgreSQL ставить не хочется, а Docker есть:

```bash
docker compose up -d
docker compose exec -T db psql -U lesnaya -d lesnaya_chashka_v2 < database/lesnaya_chashka.sql
```

### Если что-то не так

| Сообщение | Что сделать |
|---|---|
| `role "lesnaya" already exists` / `database ... already exists` | Шаг 1 уже выполнен, переходите к шагу 2. |
| `password authentication failed for user "lesnaya"` | Не выполнен шаг 1 или опечатка в пароле. |
| `relation ... already exists` при шаге 2 | Данные уже загружены. Чтобы загрузить заново, удалите базу и повторите шаги 1–2. |
| `connection refused` | PostgreSQL не запущен. |
