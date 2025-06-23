# Heroku Dev Environment - ÆON Interview System

## 🚀 Развернутое приложение

**URL:** https://qip-aeon-dev-95ccf5155d46.herokuapp.com/

**Приложение:** `qip-aeon-dev`

**Регион:** EU (Europe)

## 📋 Конфигурация

### База данных
- **Тип:** PostgreSQL (Essential 0)
- **План:** ~$0.007/hour (максимум $5/месяц)
- **Статус:** Активна

### Переменные окружения
- `DATABASE_URL` - автоматически настроена Heroku
- `SECRET_KEY` - aeon-dev-super-secret-key-2024
- `ALGORITHM` - HS256
- `ACCESS_TOKEN_EXPIRE_MINUTES` - 30
- `DEBUG` - False
- `ALLOWED_HOSTS` - qip-aeon-dev-95ccf5155d46.herokuapp.com
- `CORS_ORIGINS` - https://web.telegram.org,https://qip-aeon-dev-95ccf5155d46.herokuapp.com

## 🔧 Управление приложением

### Просмотр логов
```bash
heroku logs --tail --app qip-aeon-dev
```

### Проверка статуса
```bash
heroku ps --app qip-aeon-dev
```

### Запуск команд
```bash
heroku run <command> --app qip-aeon-dev
```

### Обновление переменных окружения
```bash
heroku config:set VARIABLE_NAME="value" --app qip-aeon-dev
```

### Просмотр конфигурации
```bash
heroku config --app qip-aeon-dev
```

## 🧪 Тестирование API

### Проверка здоровья
```bash
curl https://qip-aeon-dev-95ccf5155d46.herokuapp.com/health
```

### Запуск ÆON интервью
```bash
curl -X POST https://qip-aeon-dev-95ccf5155d46.herokuapp.com/api/aeon/start_interview \
  -H "Content-Type: application/json" \
  -d '{"user_name": "Test User", "user_email": "test@example.com"}'
```

### Отправка ответа
```bash
curl -X POST https://qip-aeon-dev-95ccf5155d46.herokuapp.com/api/aeon/answer \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "answer": "Мой ответ на вопрос"}'
```

### Проверка статуса сессии
```bash
curl https://qip-aeon-dev-95ccf5155d46.herokuapp.com/api/aeon/session/SESSION_ID/status
```

### Скачивание отчета
```bash
curl https://qip-aeon-dev-95ccf5155d46.herokuapp.com/api/aeon/download_report/SESSION_ID
```

## 📊 Мониторинг

### Heroku Dashboard
https://dashboard.heroku.com/apps/qip-aeon-dev

### Метрики
- **Dynos:** Basic (1x)
- **База данных:** Essential 0
- **Логи:** Доступны через CLI и Dashboard

## 🔄 Деплой

### Автоматический деплой
При пуше в ветку `dev`:
```bash
git push origin dev
```

### Ручной деплой на Heroku
```bash
git push heroku dev:main
```

### Инициализация базы данных после деплоя
```bash
heroku run python scripts/init_db.py --app qip-aeon-dev
```

## 🛠️ Разработка

### Локальное тестирование
```bash
# Клонирование и настройка
git clone <repository>
cd tg_api_c
git checkout dev

# Установка зависимостей
pip install -r requirements.txt

# Запуск локально
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Тестирование ÆON системы
```bash
python scripts/test_aeon.py
```

## 📝 Примечания

- Это dev-окружение для тестирования ÆON Interview системы
- База данных автоматически создается при первом деплое
- Все API endpoints доступны по базовому URL приложения
- Логи доступны через Heroku CLI и Dashboard
- Система готова к интеграции с Telegram ботом

## 🔗 Полезные ссылки

- [Heroku CLI Documentation](https://devcenter.heroku.com/articles/heroku-cli)
- [Heroku PostgreSQL](https://devcenter.heroku.com/articles/heroku-postgresql)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ÆON Interview System Documentation](README.md) 