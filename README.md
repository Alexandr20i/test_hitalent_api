# test_hitalent_api

REST API организационной структуры — управление подразделениями и сотрудниками.

## Стек

- **FastAPI** + **Python 3.11**
- **SQLAlchemy 2 (async) + **asyncpg**
- **PostgreSQL 16**
- **Alembic** (миграции)
- **Docker** + **docker-compose**
- **pytest** + **httpx** (тесты)

## Быстрый старт

### 1. Клонируй репозиторий

```bash
git clone <repo_url>
cd test_hitalent_api
```

### 2. Создай `.env`

```bash
cp .env.example .env
```

### 3. Запусти

```bash
docker-compose up --build
```

Миграции применятся автоматически при старте контейнера.

API доступно на `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`

## Эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/departments/` | Создать подразделение |
| GET | `/departments/{id}` | Получить подразделение с деревом и сотрудниками |
| PATCH | `/departments/{id}` | Обновить имя или родителя |
| DELETE | `/departments/{id}` | Удалить подразделение |
| POST | `/departments/{id}/employees/` | Создать сотрудника |
| GET | `/health` | Healthcheck |

### Параметры GET /departments/{id}

| Параметр | По умолчанию | Описание |
|----------|-------------|----------|
| `depth` | 1 (макс. 5) | Глубина вложенных подразделений |
| `include_employees` | true | Включать ли сотрудников в ответ |

### Параметры DELETE /departments/{id}

| Параметр | Описание |
|----------|----------|
| `mode=cascade` | Удалить отдел, всех сотрудников и дочерние отделы |
| `mode=reassign` | Удалить отдел, сотрудников перевести в другой |
| `reassign_to_department_id` | Обязателен при `mode=reassign` |

## Тесты

```bash
# Поднять БД
docker-compose up -d db

# Создать тестовую БД (один раз)
docker-compose exec db createdb -U postgres hitalent_test_db

# Активировать venv
source .venv/bin/activate

# Запустить тесты
APP_ENV=test DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hitalent_test_db pytest tests/ -v
```

## Структура проекта

```
app/
├── models/        # SQLAlchemy модели
├── repositories/  # Работа с БД
├── routers/       # FastAPI роутеры
├── schemas/       # Pydantic схемы
├── services/      # Бизнес-логика
├── config.py      # Настройки
├── database.py    # Async engine, сессии
├── exceptions.py  # Доменные исключения
└── main.py        # Точка входа
alembic/           # Миграции
tests/             # Тесты
```