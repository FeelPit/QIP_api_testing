#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы ÆON интервью
"""

import sys
import os
import requests
import json

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Конфигурация
API_BASE_URL = "http://localhost:8000"
AEON_BASE_URL = f"{API_BASE_URL}/api/aeon"

def test_aeon_interview():
    """Тестирование полного цикла ÆON интервью"""
    print("🧪 Тестирование ÆON интервью")
    print("=" * 50)
    
    # 1. Начинаем интервью
    print("\n1️⃣ Начинаем интервью...")
    start_response = requests.post(
        f"{AEON_BASE_URL}/start_interview",
        json={
            "user_id": None,
            "user_name": "Test User",
            "user_email": "test@example.com"
        }
    )
    
    if start_response.status_code != 200:
        print(f"❌ Ошибка при запуске интервью: {start_response.status_code}")
        return
    
    start_data = start_response.json()
    session_id = start_data["data"]["session_id"]
    question = start_data["data"]["question"]
    
    print(f"✅ Интервью начато")
    print(f"📝 Session ID: {session_id}")
    print(f"❓ Первый вопрос: {question}")
    
    # 2. Отвечаем на вопросы
    test_answers = [
        "Je suis passionné par l'innovation et la création de solutions qui ont un impact positif. Dans le travail, j'aime collaborer avec des équipes talentueuses et résoudre des défis complexes. Dans la vie, mes valeurs fondamentales sont l'intégrité, la croissance personnelle et la contribution à quelque chose de plus grand que moi.",
        
        "Dans une situation complexe sans instructions claires, j'ai d'abord analysé le contexte et identifié les objectifs principaux. J'ai ensuite créé un plan d'action flexible, en restant ouvert aux ajustements. Je suis plutôt stratège, mais j'apprécie aussi l'improvisation quand c'est nécessaire pour s'adapter rapidement.",
        
        "Je veux laisser une culture d'innovation et de collaboration dans l'équipe. Si j'avais une liberté totale, je créerais une plateforme qui utilise l'IA pour démocratiser l'accès à l'éducation et aux opportunités professionnelles, en connectant les talents avec les bonnes opportunités.",
        
        "Ma dernière erreur importante était de ne pas communiquer suffisamment avec l'équipe sur un changement de direction. J'ai appris l'importance de la transparence et de la communication proactive. J'ai agi à la limite de mes capacités lors d'un projet critique où j'ai dû apprendre une nouvelle technologie en une semaine - c'était intense mais très enrichissant.",
        
        "Je m'imagine comme un catalyseur d'innovation chez Quantum Insight, contribuant à développer des solutions qui repoussent les limites de ce qui est possible. J'améliorerais en priorité notre système de feedback et de développement continu, en créant des mécanismes pour identifier et développer les talents cachés."
    ]
    
    for i, answer in enumerate(test_answers, 1):
        print(f"\n{i}️⃣ Отвечаем на вопрос {i}...")
        print(f"💬 Ответ: {answer[:100]}...")
        
        answer_response = requests.post(
            f"{AEON_BASE_URL}/answer",
            json={
                "session_id": session_id,
                "answer": answer
            }
        )
        
        if answer_response.status_code != 200:
            print(f"❌ Ошибка при отправке ответа: {answer_response.status_code}")
            return
        
        answer_data = answer_response.json()
        
        if answer_data["data"]["is_completed"]:
            print("✅ Интервью завершено!")
            print(f"📊 Отчет: {answer_data['data']['report']['archetype']}")
            break
        else:
            next_question = answer_data["data"]["next_question"]
            print(f"❓ Следующий вопрос: {next_question}")
    
    # 3. Получаем статус сессии
    print(f"\n3️⃣ Проверяем статус сессии...")
    status_response = requests.get(f"{AEON_BASE_URL}/session/{session_id}/status")
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"✅ Статус: {status_data['data']['status']}")
        print(f"📊 Прогресс: {status_data['data']['current_question']}/{status_data['data']['total_questions']}")
    
    # 4. Получаем отчет
    print(f"\n4️⃣ Получаем отчет...")
    report_response = requests.get(f"{AEON_BASE_URL}/session/{session_id}/report")
    
    if report_response.status_code == 200:
        report_data = report_response.json()
        print("✅ Отчет получен:")
        print(f"   🎭 Архетип: {report_data['data']['archetype']}")
        print(f"   🧠 Вектор сознания: {report_data['data']['consciousness_vector']}")
        print(f"   💪 Мотивация: {report_data['data']['motivation_score']:.2f}")
        print(f"   🤝 Синергия: {report_data['data']['synergy_score']:.2f}")
        print(f"   🔄 Гибкость: {report_data['data']['flexibility_score']:.2f}")
        print(f"   🎯 Независимость: {report_data['data']['independence_score']:.2f}")
        print(f"   🚀 Адаптивность: {report_data['data']['adaptability_score']:.2f}")
    
    # 5. Скачиваем отчет в JSON
    print(f"\n5️⃣ Скачиваем отчет в JSON...")
    download_response = requests.get(f"{AEON_BASE_URL}/download_report/{session_id}")
    
    if download_response.status_code == 200:
        # Сохраняем отчет в файл
        filename = f"aeon_report_test_{session_id[:8]}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(download_response.text)
        print(f"✅ Отчет сохранен в файл: {filename}")
    else:
        print(f"❌ Ошибка при скачивании отчета: {download_response.status_code}")

def test_api_health():
    """Проверка здоровья API"""
    print("🏥 Проверка здоровья API...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API работает корректно")
            return True
        else:
            print(f"❌ API недоступен: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к API. Убедитесь, что сервер запущен.")
        return False

def main():
    """Основная функция"""
    print("🚀 Тестирование ÆON Interview System")
    print("=" * 50)
    
    # Проверяем здоровье API
    if not test_api_health():
        print("\n💡 Для запуска тестов:")
        print("   1. Запустите сервер: uvicorn app.main:app --reload")
        print("   2. Инициализируйте БД: python scripts/init_db.py")
        print("   3. Запустите тесты: python scripts/test_aeon.py")
        return
    
    # Запускаем тесты
    try:
        test_aeon_interview()
        print("\n🎉 Все тесты завершены успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")

if __name__ == "__main__":
    main() 