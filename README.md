# 🧠 Quantum Insight | Telegram Test Backend

Бэкенд для мини-приложения Telegram для тестирования стажёров.

## �� Быстрый старт

### Локальная разработка

#### Установка зависимостей
```bash
pip install -r requirements.txt
```

#### Настройка базы данных
```bash
# Создайте файл .env с настройками БД
cp env.example .env
# Отредактируйте .env файл

# Примените миграции
python scripts/init_db.py
```

#### Запуск сервера
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ☁️ Деплой на Heroku

### 1. Установите Heroku CLI
```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows
# Скачайте с https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Войдите в Heroku
```bash
heroku login
```

### 3. Создайте приложение на Heroku
```bash
heroku create your-app-name
```

### 4. Добавьте PostgreSQL
```bash
heroku addons:create heroku-postgresql:mini
```

### 5. Настройте переменные окружения
```bash
heroku config:set SECRET_KEY="your-super-secret-key-change-this-in-production"
heroku config:set TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
heroku config:set DEBUG="False"
```

### 6. Деплой
```bash
git push heroku main
```

### 7. Инициализация базы данных
```bash
heroku run python scripts/heroku_init.py
```

### 8. Откройте приложение
```bash
heroku open
```

## 📚 API Endpoints

### Тесты
- `GET /api/tests` - Получить список тестов
- `GET /api/tests/{test_id}/questions` - Получить вопросы теста
- `POST /api/submissions/{test_id}/submit` - Отправить ответы на тест

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

### Локальная разработка
Создайте файл `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost/quantum_insight
SECRET_KEY=your-secret-key
TELEGRAM_BOT_TOKEN=your-bot-token
```

### Heroku
Переменные окружения настраиваются автоматически:
- `DATABASE_URL` - предоставляется Heroku PostgreSQL
- `PORT` - предоставляется Heroku
- `SECRET_KEY` - настройте вручную
- `TELEGRAM_BOT_TOKEN` - настройте вручную

## 🧪 Тестирование

### Локальное тестирование
```bash
# Проверка здоровья API
curl http://localhost:8000/health

# Получение тестов
curl http://localhost:8000/api/tests/

# Отправка ответов
curl -X POST http://localhost:8000/api/submissions/1/submit \
  -H "Content-Type: application/json" \
  -H "x-telegram-user-id: 123456" \
  -d '{"test_id": 1, "answers": [...]}'
```

### Heroku тестирование
```bash
# Замените YOUR_APP_NAME на имя вашего приложения
curl https://your-app-name.herokuapp.com/health
```

## 📊 Мониторинг

### Heroku логи
```bash
heroku logs --tail
```

### Статус приложения
```bash
heroku ps
```

## 🔒 Безопасность

- Все переменные окружения хранятся в Heroku Config Vars
- База данных защищена SSL
- CORS настроен для Telegram WebApp
- Валидация всех входящих данных через Pydantic

## 🚀 Готово к продакшену!

После деплоя на Heroku API будет доступен по адресу:
`https://your-app-name.herokuapp.com`

**Готово для интеграции с Telegram WebApp!** 🎯 