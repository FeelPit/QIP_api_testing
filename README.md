# Quantum Insight Telegram Test API

API для мини-приложения Telegram тестирования стажёров с интегрированной системой ÆON интервью.

## 🚀 Возможности

### 📝 Система тестирования
- Создание и управление тестами (Frontend/Backend)
- Динамическая генерация вопросов
- Автоматическая проверка ответов
- Анализ подозрительной активности
- Экспорт результатов в JSON/Markdown

### 🧠 ÆON Interview System
**Новое поколение собеседований с ИИ-анализом**

- **Генерация вопросов на лету** на французском языке
- **AI-анализ ответов** в реальном времени
- **Определение архетипа кандидата** и вектора сознания
- **Оценка ключевых компетенций:**
  - Мотивация и ценности
  - Гибкость мышления
  - Потенциал и креативность
  - Поведенческие паттерны
  - Готовность к интеграции в команду
- **Генерация детального отчета** на русском языке
- **Скачивание отчета в JSON** формате

## 🏗️ Архитектура

```
tg_api_c/
├── app/
│   ├── __init__.py
│   ├── config.py          # Конфигурация приложения
│   ├── database.py        # Настройки базы данных
│   ├── main.py           # Основное приложение FastAPI
│   ├── models.py         # SQLAlchemy модели
│   ├── schemas.py        # Pydantic схемы
│   ├── services.py       # Бизнес-логика
│   └── routers/          # API роутеры
│       ├── __init__.py
│       ├── tests.py      # Управление тестами
│       ├── submissions.py # Отправка ответов
│       ├── results.py    # Результаты тестов
│       └── aeon_interview.py # ÆON интервью
├── scripts/
│   ├── init_db.py        # Инициализация БД
│   ├── test_aeon.py      # Тестирование ÆON
│   └── heroku_init.py    # Настройка Heroku
├── requirements.txt      # Зависимости
└── README.md
```

## 🗄️ База данных

### Основные таблицы
- `users` - Пользователи
- `tests` - Тесты
- `questions` - Вопросы
- `test_results` - Результаты тестов
- `answers` - Ответы
- `suspicious_activities` - Подозрительная активность

### ÆON таблицы
- `aeon_sessions` - Сессии интервью
- `aeon_questions` - Сгенерированные вопросы
- `aeon_answers` - Ответы с AI-анализом
- `aeon_reports` - Финальные отчеты

## 🚀 Установка и запуск

### 1. Клонирование и настройка
```bash
git clone <repository-url>
cd tg_api_c
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка окружения
```bash
cp env.example .env
# Отредактируйте .env файл с вашими настройками
```

### 4. Инициализация базы данных
```bash
python scripts/init_db.py
```

### 5. Запуск сервера
```bash
uvicorn app.main:app --reload
```

## 📡 API Endpoints

### Тестирование
- `GET /api/tests` - Список активных тестов
- `GET /api/tests/{test_id}` - Получить тест
- `POST /api/submissions` - Отправить ответы
- `GET /api/results/{result_id}` - Получить результат

### ÆON Интервью
- `POST /api/aeon/start_interview` - Начать интервью
- `POST /api/aeon/answer` - Отправить ответ
- `GET /api/aeon/download_report/{session_id}` - Скачать отчет
- `GET /api/aeon/session/{session_id}/status` - Статус сессии
- `GET /api/aeon/session/{session_id}/report` - Получить отчет

## 🧪 Тестирование ÆON системы

```bash
# Запустите сервер
uvicorn app.main:app --reload

# В другом терминале запустите тесты
python scripts/test_aeon.py
```

## 🎯 ÆON Interview Process

### 1. Начало интервью
```json
POST /api/aeon/start_interview
{
  "user_id": null
}
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "question": "Qu'est-ce qui est vraiment important pour toi...",
    "question_number": 1,
    "total_questions": 5,
    "message": "Bonjour, je suis ÆON..."
  }
}
```

### 2. Отправка ответов
```json
POST /api/aeon/answer
{
  "session_id": "uuid",
  "answer": "Je suis passionné par l'innovation..."
}
```

### 3. Финальный отчет
После 5 вопросов система генерирует детальный отчет:

```json
{
  "archetype": "Стратег-Вдохновитель",
  "consciousness_vector": "Эволюционный",
  "motivation_score": 0.85,
  "growth_zone": "Работа с ошибками и кризисными ситуациями",
  "genius_zone": "Стратегическое видение и инновации",
  "synergy_score": 0.78,
  "flexibility_score": 0.72,
  "independence_score": 0.81,
  "adaptability_score": 0.76,
  "overall_assessment": "Кандидат демонстрирует высокий потенциал...",
  "recommendations": {
    "immediate_actions": ["Тренировка адаптивного мышления"],
    "development_plan": ["Фокус на зоне роста..."],
    "team_integration": ["Быстрая интеграция в проектную команду"]
  }
}
```

## 🔧 Конфигурация

### Переменные окружения (.env)
```env
DATABASE_URL=sqlite:///./quantum_insight.db
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
SECRET_KEY=your-secret-key
```

## 🚀 Развертывание

### Heroku
```bash
# Настройка Heroku
python scripts/heroku_init.py

# Развертывание
git push heroku main
```

### Docker
```bash
docker build -t quantum-insight-api .
docker run -p 8000:8000 quantum-insight-api
```

## 📊 Мониторинг

- `GET /health` - Проверка здоровья API
- `GET /docs` - Swagger документация
- `GET /redoc` - ReDoc документация

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи сервера
2. Убедитесь, что база данных инициализирована
3. Проверьте конфигурацию в .env файле
4. Создайте Issue в репозитории

---

**Quantum Insight** - Инновационные решения для будущего 🚀 