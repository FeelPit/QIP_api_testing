# 🧠 Quantum Insight | Telegram Test Backend

Бэкенд для мини-приложения Telegram для тестирования стажёров.

## 🚀 Быстрый старт

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Настройка базы данных
```bash
# Создайте файл .env с настройками БД
cp .env.example .env
# Отредактируйте .env файл

# Примените миграции
alembic upgrade head
```

### Запуск сервера
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Endpoints

### Тесты
- `GET /api/tests` - Получить список тестов
- `GET /api/tests/{test_id}/questions` - Получить вопросы теста
- `POST /api/tests/{test_id}/submit` - Отправить ответы на тест

### Результаты
- `GET /api/results` - Получить результаты (для админов)
- `GET /api/results/{result_id}` - Получить конкретный результат
- `POST /api/results/export` - Экспорт результатов в JSON/Markdown

## 🗄️ Структура базы данных

- **users** - Пользователи Telegram
- **tests** - Тесты (Frontend/Backend)
- **questions** - Вопросы тестов
- **answers** - Ответы пользователей
- **results** - Результаты тестирования
- **suspicious_activities** - Подозрительная активность

## 🔧 Конфигурация

Создайте файл `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost/quantum_insight
SECRET_KEY=your-secret-key
TELEGRAM_BOT_TOKEN=your-bot-token
``` 