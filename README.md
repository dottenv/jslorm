# JSLORM

**English** | [Русский](#русская-документация)

Advanced JSON-based ORM for Python with async support, query builder, caching, and production-ready features.

## Installation

```bash
pip install jslorm
```

## Quick Start

```python
from jslorm import Database, BaseModel, BaseRepository, foreign_key

# Define models with relationships
class User(BaseModel):
    name: str
    email: str
    age: int
    
    __table_name__ = "users"
    __indexes__ = ["email", "age"]
    __unique_fields__ = ["email"]

class Post(BaseModel):
    title: str
    content: str
    user_id: int = foreign_key("users")
    
    __table_name__ = "posts"

# Setup database
db = Database("myapp", enable_compression=True)
user_repo = BaseRepository(db.driver, User)
post_repo = BaseRepository(db.driver, Post)

# Auto-discover and create tables
db = Database("myapp", enable_compression=True)
await db.init_db()  # Finds all models automatically

# Advanced queries
users = await user_repo.find(age__gte=18, name__like="John")
adult_users = await user_repo.where("age", "gte", 18)
sorted_users = await user_repo.order_by("name")
paginated = await user_repo.get_all(limit=10, offset=20)

# Aggregations
user_count = await user_repo.count()
avg_age = await user_repo.avg("age")

# Query Builder
query = db.query("users").where("age", "gt", 18).order_by("name").limit(10)
results = await db.driver.select("users", query_builder=query)
```

## Real-World Example: Telegram Bot with Aiogram

```python
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from jslorm import Database, BaseModel, BaseRepository, foreign_key

# Database Models
class TelegramUser(BaseModel):
    telegram_id: int
    username: str
    first_name: str
    is_admin: bool = False
    
    __table_name__ = "telegram_users"
    __indexes__ = ["telegram_id"]
    __unique_fields__ = ["telegram_id"]

class SupportTicket(BaseModel):
    user_id: int = foreign_key("telegram_users")
    title: str
    description: str
    status: str = "open"  # open, in_progress, closed
    priority: int = 1
    
    __table_name__ = "support_tickets"
    __indexes__ = ["user_id", "status"]

class TicketMessage(BaseModel):
    ticket_id: int = foreign_key("support_tickets")
    user_id: int = foreign_key("telegram_users")
    message: str
    is_admin_reply: bool = False
    
    __table_name__ = "ticket_messages"
    __indexes__ = ["ticket_id"]

# Database Setup
db = Database("support_bot", enable_compression=True)
user_repo = BaseRepository(db.driver, TelegramUser)
ticket_repo = BaseRepository(db.driver, SupportTicket)
message_repo = BaseRepository(db.driver, TicketMessage)

# Bot Setup
bot = Bot(token="YOUR_BOT_TOKEN")
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    # Register or get user
    user = await user_repo.find_one(telegram_id=message.from_user.id)
    if not user:
        user = await user_repo.create(TelegramUser(
            telegram_id=message.from_user.id,
            username=message.from_user.username or "",
            first_name=message.from_user.first_name or ""
        ))
    
    await message.answer(
        f"Привет, {user.first_name}! 👋\n"
        "Используй /ticket для создания обращения в поддержку."
    )

@dp.message(Command("ticket"))
async def create_ticket_handler(message: types.Message):
    user = await user_repo.find_one(telegram_id=message.from_user.id)
    if not user:
        await message.answer("Сначала нажмите /start")
        return
    
    # Create new ticket
    ticket = await ticket_repo.create(SupportTicket(
        user_id=user.id,
        title=f"Обращение от {user.first_name}",
        description="Ожидание описания проблемы",
        status="open"
    ))
    
    await message.answer(
        f"✅ Тикет #{ticket.id} создан!\n"
        "Опишите вашу проблему следующим сообщением."
    )

@dp.message(Command("my_tickets"))
async def my_tickets_handler(message: types.Message):
    user = await user_repo.find_one(telegram_id=message.from_user.id)
    if not user:
        await message.answer("Сначала нажмите /start")
        return
    
    # Get user tickets with pagination
    tickets = await ticket_repo.find(user_id=user.id)
    
    if not tickets:
        await message.answer("У вас нет активных тикетов.")
        return
    
    response = "📋 Ваши тикеты:\n\n"
    for ticket in tickets:
        status_emoji = {"open": "🟡", "in_progress": "🔵", "closed": "✅"}
        response += f"{status_emoji.get(ticket.status, '⚪')} #{ticket.id} - {ticket.title}\n"
        response += f"   Статус: {ticket.status}\n\n"
    
    await message.answer(response)

@dp.message(Command("admin_stats"))
async def admin_stats_handler(message: types.Message):
    user = await user_repo.find_one(telegram_id=message.from_user.id)
    if not user or not user.is_admin:
        await message.answer("❌ Недостаточно прав")
        return
    
    # Get statistics using aggregations
    total_users = await user_repo.count()
    total_tickets = await ticket_repo.count()
    open_tickets = await ticket_repo.count({"status": "open"})
    closed_tickets = await ticket_repo.count({"status": "closed"})
    
    # Get database metrics
    metrics = await db.get_metrics()
    
    response = f"📊 Статистика бота:\n\n"
    response += f"👥 Пользователей: {total_users}\n"
    response += f"🎫 Всего тикетов: {total_tickets}\n"
    response += f"🟡 Открытых: {open_tickets}\n"
    response += f"✅ Закрытых: {closed_tickets}\n\n"
    response += f"⚡ Запросов к БД: {metrics['queries']}\n"
    response += f"⏱ Среднее время: {metrics['avg_query_time']:.3f}s"
    
    await message.answer(response)

# Middleware for logging
async def logging_middleware(operation, table, data, context):
    print(f"[DB] {operation} on {table} - {context}")
    return data

async def main():
    # Auto-discover and setup database
    await db.init_db()  # Automatically finds and creates all tables
    
    # Add middleware
    db.add_middleware(logging_middleware)
    
    # Start bot
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Features

### Query Operators
```python
# Comparison operators
users = await repo.find(age__gt=18)      # Greater than
users = await repo.find(age__gte=18)     # Greater than or equal
users = await repo.find(age__lt=65)      # Less than
users = await repo.find(age__lte=65)     # Less than or equal
users = await repo.find(age__ne=25)      # Not equal

# String operators
users = await repo.find(name__like="John")     # Contains
users = await repo.find(name__ilike="john")    # Case insensitive

# List operators
users = await repo.find(age__in=[18, 25, 30])     # In list
users = await repo.find(age__not_in=[18, 25])     # Not in list

# Null checks
users = await repo.find(email__is_null=True)      # Is null
users = await repo.find(email__is_not_null=True)  # Is not null
```

### Complex Queries with Query Builder
```python
# Advanced filtering and sorting
query = (db.query("support_tickets")
         .where("status", "in", ["open", "in_progress"])
         .where("priority", "gte", 3)
         .order_by("priority", desc=True)
         .order_by("created_at")
         .limit(50))

high_priority_tickets = await db.driver.select("support_tickets", query_builder=query)

# Aggregations for analytics
stats = {
    "total_tickets": await ticket_repo.count(),
    "open_tickets": await ticket_repo.count({"status": "open"}),
    "avg_priority": await ticket_repo.avg("priority"),
    "max_priority": await ticket_repo.aggregate("max", "priority")
}
```

### Relationships & Foreign Keys
```python
class User(BaseModel):
    name: str
    email: str

class Post(BaseModel):
    title: str
    user_id: int = foreign_key("users", on_delete="CASCADE")
    
    # Relationship definition
    user = relationship("User", RelationType.MANY_TO_ONE)

# Working with relationships
user = await user_repo.create(User(name="John", email="john@example.com"))
post = await post_repo.create(Post(title="My Post", user_id=user.id))

# Find related data
user_posts = await post_repo.find(user_id=user.id)
```

### Performance & Caching
```python
# Automatic query caching
users = await repo.find({"active": True})  # Cached automatically

# Indexes for fast queries
class User(BaseModel):
    email: str
    telegram_id: int
    
    __indexes__ = ["email", "telegram_id"]  # Fast lookups
    __unique_fields__ = ["email", "telegram_id"]  # Unique constraints

# Pagination for large datasets
page_1 = await user_repo.get_all(limit=20, offset=0)
page_2 = await user_repo.get_all(limit=20, offset=20)
```

### Monitoring & Health Checks
```python
# Get performance metrics
metrics = await db.get_metrics()
print(f"Total queries: {metrics['queries']}")
print(f"Average query time: {metrics['avg_query_time']}s")
print(f"Cache hit rate: {metrics.get('cache_hits', 0)}")

# Health check for monitoring
health = await db.health_check()
if health["status"] == "healthy":
    print("✅ Database is healthy")
else:
    print(f"❌ Database issues: {health.get('error')}")

# Database statistics
stats = await db.get_stats()
for table_name, table_stats in stats["tables"].items():
    print(f"{table_name}: {table_stats['record_count']} records")
```

### Middleware & Logging
```python
# Custom middleware for logging
async def audit_middleware(operation, table, data, context):
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] {operation.upper()} on {table}")
    
    # Log sensitive operations
    if operation in ["insert", "update", "delete"]:
        audit_log = {
            "operation": operation,
            "table": table,
            "timestamp": timestamp,
            "data_keys": list(data.keys()) if isinstance(data, dict) else None
        }
        # Save to audit table or external logging service
    
    return data

# Performance monitoring middleware
async def performance_middleware(operation, table, data, context):
    start_time = time.time()
    result = data
    duration = time.time() - start_time
    
    if duration > 0.1:  # Log slow operations
        print(f"⚠️ Slow operation: {operation} on {table} took {duration:.3f}s")
    
    return result

db.add_middleware(audit_middleware)
db.add_middleware(performance_middleware)
```

## CLI Commands

```bash
# Initialize database (auto-discovers all models)
jslorm init

# Apply migrations (updates schema)
jslorm db-upgrade

# Show migration status
jslorm db-status

# Create backup
jslorm backup

# Restore from backup
jslorm restore --path backup.json

# Show statistics and metrics
jslorm stats
```

## Configuration

```env
# Database settings
DATABASE_PATH=data/myapp
DATABASE_BACKUP_DIR=backups
DATABASE_AUTO_BACKUP=true
DATABASE_BACKUP_INTERVAL=3600

# For production
DATABASE_COMPRESSION=true
DATABASE_CACHE_SIZE=1000
```

## Production Deployment

```python
# production_bot.py
import os
from jslorm import Database

# Production configuration
db = Database(
    db_path=os.getenv("DATABASE_PATH", "data/production_bot"),
    enable_compression=True
)

# Setup automatic backups
import asyncio
from datetime import datetime

async def auto_backup():
    while True:
        try:
            backup_path = await db.backup()
            print(f"✅ Backup created: {backup_path}")
        except Exception as e:
            print(f"❌ Backup failed: {e}")
        
        # Backup every hour
        await asyncio.sleep(3600)

# Start backup task
asyncio.create_task(auto_backup())
```

## Features

### 🚀 Performance
- ✅ Query Builder with operators
- ✅ Automatic indexing
- ✅ Query result caching
- ✅ Data compression
- ✅ Pagination support

### 🔍 Querying
- ✅ Advanced operators (gt, lt, like, in, etc.)
- ✅ Sorting and ordering
- ✅ Aggregation functions (count, sum, avg, min, max)
- ✅ Complex query building

### 🔗 Relationships
- ✅ Foreign keys with constraints
- ✅ One-to-One, One-to-Many relationships
- ✅ Automatic validation

### 🛡️ Security & Validation
- ✅ Schema validation
- ✅ Unique constraints
- ✅ Foreign key validation
- ✅ Data type checking

### 📊 Monitoring
- ✅ Query performance metrics
- ✅ Operation logging
- ✅ Health checks
- ✅ Middleware support

### 🔧 Production Ready
- ✅ Async/await support
- ✅ Pydantic models
- ✅ Auto-incrementing IDs
- ✅ Timestamps (created_at, updated_at)
- ✅ Backup/restore
- ✅ CLI commands
- ✅ No external dependencies
- ✅ Compression support

---

# Русская документация

[English](#jslorm) | **Русский**

Продвинутая JSON-based ORM для Python с поддержкой async, конструктором запросов, кэшированием и готовностью к продакшену.

## Установка

```bash
pip install jslorm
```

## Быстрый старт

```python
from jslorm import Database, BaseModel, BaseRepository, foreign_key

# Определяем модели со связями
class User(BaseModel):
    name: str
    email: str
    age: int
    
    __table_name__ = "users"
    __indexes__ = ["email", "age"]
    __unique_fields__ = ["email"]

class Post(BaseModel):
    title: str
    content: str
    user_id: int = foreign_key("users")
    
    __table_name__ = "posts"

# Настройка базы данных
db = Database("myapp", enable_compression=True)
user_repo = BaseRepository(db.driver, User)
post_repo = BaseRepository(db.driver, Post)

# Создание таблиц
await user_repo.create_table()
await post_repo.create_table()

# Продвинутые запросы
users = await user_repo.find(age__gte=18, name__like="Иван")
adult_users = await user_repo.where("age", "gte", 18)
sorted_users = await user_repo.order_by("name")
paginated = await user_repo.get_all(limit=10, offset=20)

# Агрегация
user_count = await user_repo.count()
avg_age = await user_repo.avg("age")
```

## Пример Telegram бота с Aiogram

```python
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from jslorm import Database, BaseModel, BaseRepository, foreign_key

# Модели базы данных
class TelegramUser(BaseModel):
    telegram_id: int
    username: str
    first_name: str
    is_admin: bool = False
    
    __table_name__ = "telegram_users"
    __indexes__ = ["telegram_id"]
    __unique_fields__ = ["telegram_id"]

class SupportTicket(BaseModel):
    user_id: int = foreign_key("telegram_users")
    title: str
    description: str
    status: str = "open"  # open, in_progress, closed
    priority: int = 1
    
    __table_name__ = "support_tickets"
    __indexes__ = ["user_id", "status"]

# Настройка базы данных
db = Database("support_bot", enable_compression=True)
user_repo = BaseRepository(db.driver, TelegramUser)
ticket_repo = BaseRepository(db.driver, SupportTicket)

# Настройка бота
bot = Bot(token="YOUR_BOT_TOKEN")
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    # Регистрируем или получаем пользователя
    user = await user_repo.find_one(telegram_id=message.from_user.id)
    if not user:
        user = await user_repo.create(TelegramUser(
            telegram_id=message.from_user.id,
            username=message.from_user.username or "",
            first_name=message.from_user.first_name or ""
        ))
    
    await message.answer(
        f"Привет, {user.first_name}! 👋\n"
        "Используй /ticket для создания обращения в поддержку."
    )

@dp.message(Command("stats"))
async def stats_handler(message: types.Message):
    # Статистика с использованием агрегации
    total_users = await user_repo.count()
    total_tickets = await ticket_repo.count()
    open_tickets = await ticket_repo.count({"status": "open"})
    
    # Метрики производительности БД
    metrics = await db.get_metrics()
    
    response = f"📊 Статистика:\n\n"
    response += f"👥 Пользователей: {total_users}\n"
    response += f"🎫 Тикетов: {total_tickets}\n"
    response += f"🟡 Открытых: {open_tickets}\n\n"
    response += f"⚡ Запросов к БД: {metrics['queries']}\n"
    response += f"⏱ Среднее время: {metrics['avg_query_time']:.3f}s"
    
    await message.answer(response)

async def main():
    # Инициализация БД
    await db.init_db()  # Автоматически находит и создает все таблицы
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

## Продвинутые возможности

### Операторы запросов
```python
# Операторы сравнения
users = await repo.find(age__gt=18)      # Больше
users = await repo.find(age__gte=18)     # Больше или равно
users = await repo.find(age__lt=65)      # Меньше
users = await repo.find(age__lte=65)     # Меньше или равно
users = await repo.find(age__ne=25)      # Не равно

# Строковые операторы
users = await repo.find(name__like="Иван")     # Содержит
users = await repo.find(name__ilike="иван")    # Без учета регистра

# Операторы списков
users = await repo.find(age__in=[18, 25, 30])     # В списке
users = await repo.find(age__not_in=[18, 25])     # Не в списке

# Проверка на NULL
users = await repo.find(email__is_null=True)      # Пустое
users = await repo.find(email__is_not_null=True)  # Не пустое
```

### Конструктор запросов
```python
# Сложная фильтрация и сортировка
query = (db.query("support_tickets")
         .where("status", "in", ["open", "in_progress"])
         .where("priority", "gte", 3)
         .order_by("priority", desc=True)
         .limit(50))

tickets = await db.driver.select("support_tickets", query_builder=query)

# Агрегация для аналитики
stats = {
    "всего_тикетов": await ticket_repo.count(),
    "открытых": await ticket_repo.count({"status": "open"}),
    "средний_приоритет": await ticket_repo.avg("priority")
}
```

### Производительность и кэширование
```python
# Автоматическое кэширование запросов
users = await repo.find({"active": True})  # Кэшируется автоматически

# Индексы для быстрого поиска
class User(BaseModel):
    email: str
    telegram_id: int
    
    __indexes__ = ["email", "telegram_id"]  # Быстрый поиск
    __unique_fields__ = ["email"]  # Уникальные ограничения

# Пагинация для больших данных
страница_1 = await user_repo.get_all(limit=20, offset=0)
страница_2 = await user_repo.get_all(limit=20, offset=20)
```

### Мониторинг и метрики
```python
# Метрики производительности
metrics = await db.get_metrics()
print(f"Всего запросов: {metrics['queries']}")
print(f"Среднее время: {metrics['avg_query_time']}s")

# Проверка здоровья БД
health = await db.health_check()
if health["status"] == "healthy":
    print("✅ База данных работает нормально")
else:
    print(f"❌ Проблемы с БД: {health.get('error')}")
```

## CLI команды

```bash
# Инициализация базы данных (автопоиск моделей)
jslorm init

# Применение миграций (обновление схемы)
jslorm db-upgrade

# Статус миграций
jslorm db-status

# Создание резервной копии
jslorm backup

# Восстановление из копии
jslorm restore --path backup.json

# Статистика и метрики
jslorm stats
```

## Конфигурация

```env
# Настройки базы данных
DATABASE_PATH=data/myapp
DATABASE_BACKUP_DIR=backups
DATABASE_AUTO_BACKUP=true
DATABASE_BACKUP_INTERVAL=3600

# Для продакшена
DATABASE_COMPRESSION=true
DATABASE_CACHE_SIZE=1000
```

## Возможности

### 🚀 Производительность
- ✅ Конструктор запросов с операторами
- ✅ Автоматическое индексирование
- ✅ Кэширование результатов запросов
- ✅ Сжатие данных
- ✅ Поддержка пагинации

### 🔍 Запросы
- ✅ Продвинутые операторы (gt, lt, like, in и др.)
- ✅ Сортировка и упорядочивание
- ✅ Функции агрегации (count, sum, avg, min, max)
- ✅ Построение сложных запросов

### 🔗 Связи
- ✅ Внешние ключи с ограничениями
- ✅ Связи один-к-одному, один-ко-многим
- ✅ Автоматическая валидация

### 🛡️ Безопасность и валидация
- ✅ Валидация схем
- ✅ Уникальные ограничения
- ✅ Валидация внешних ключей
- ✅ Проверка типов данных

### 📊 Мониторинг
- ✅ Метрики производительности запросов
- ✅ Логирование операций
- ✅ Проверки здоровья
- ✅ Поддержка middleware

### 🔧 Готовность к продакшену
- ✅ Поддержка async/await
- ✅ Модели Pydantic
- ✅ Автоинкремент ID
- ✅ Временные метки (created_at, updated_at)
- ✅ Резервное копирование/восстановление
- ✅ CLI команды
- ✅ Без внешних зависимостей
- ✅ Поддержка сжатия