-- Создаёт пользователя и базу для проекта «Лесная Чашка».
-- Запустить один раз от администратора PostgreSQL (как — см. README, шаг 1).
-- Логин и пароль совпадают с backend/.env. Все данные тестовые.

CREATE USER lesnaya WITH PASSWORD 'lesnaya-local-2026' CREATEDB;
CREATE DATABASE lesnaya_chashka_v2 OWNER lesnaya ENCODING 'UTF8' TEMPLATE template0;
