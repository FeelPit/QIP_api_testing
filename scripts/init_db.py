#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных с тестовыми данными
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, Test, Question
from app.config import settings


def init_database():
    """Инициализация базы данных"""
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже тесты
        existing_tests = db.query(Test).count()
        if existing_tests > 0:
            print("База данных уже содержит тесты. Пропускаем инициализацию.")
            return
        
        # Создаем тест для Frontend
        frontend_test = Test(
            name="Frontend Development Test",
            description="Тест на знание Frontend технологий",
            test_type="frontend",
            time_limit_per_question=90
        )
        db.add(frontend_test)
        db.commit()
        db.refresh(frontend_test)
        
        # Вопросы для Frontend теста
        frontend_questions = [
            {
                "question_text": "Quelle est la différence entre `null`, `undefined`, et `NaN` en JavaScript ?",
                "question_type": "text",
                "correct_answer": "null est une valeur assignée, undefined est une variable non initialisée, NaN signifie 'Not a Number'",
                "order": 1
            },
            {
                "question_text": "À quoi sert la méthode `useEffect` dans React ?",
                "question_type": "text",
                "correct_answer": "useEffect permet d'effectuer des effets de bord dans les composants fonctionnels",
                "order": 2
            },
            {
                "question_text": "Expliquez la différence entre `state` et `props`.",
                "question_type": "text",
                "correct_answer": "state est interne au composant et peut être modifié, props sont passées de l'extérieur et sont en lecture seule",
                "order": 3
            },
            {
                "question_text": "Qu'est-ce que le Virtual DOM ?",
                "question_type": "text",
                "correct_answer": "Une représentation en mémoire de l'interface utilisateur qui permet d'optimiser les mises à jour",
                "order": 4
            },
            {
                "question_text": "Comment fonctionne le système de 'lifting state up' ?",
                "question_type": "text",
                "correct_answer": "Déplacer l'état vers le composant parent le plus proche pour le partager entre composants enfants",
                "order": 5
            },
            {
                "question_text": "Que signifie SPA (Single Page Application) ?",
                "question_type": "text",
                "correct_answer": "Une application web qui charge une seule page HTML et met à jour le contenu dynamiquement",
                "order": 6
            },
            {
                "question_text": "Comment assurer l'accessibilité (a11y) d'un composant ?",
                "question_type": "text",
                "correct_answer": "Utiliser des attributs ARIA, des balises sémantiques, et tester avec des lecteurs d'écran",
                "order": 7
            },
            {
                "question_text": "Quelle est la différence entre CSS Grid et Flexbox ?",
                "question_type": "text",
                "correct_answer": "Grid est pour les layouts 2D, Flexbox pour les layouts 1D (ligne ou colonne)",
                "order": 8
            },
            {
                "question_text": "À quoi sert un custom hook ?",
                "question_type": "text",
                "correct_answer": "Réutiliser la logique d'état et d'effets entre composants",
                "order": 9
            },
            {
                "question_text": "Quelle est votre approche pour optimiser le chargement initial d'une page React ?",
                "question_type": "text",
                "correct_answer": "Code splitting, lazy loading, optimisation des bundles, et mise en cache",
                "order": 10
            }
        ]
        
        for q_data in frontend_questions:
            question = Question(
                test_id=frontend_test.id,
                **q_data
            )
            db.add(question)
        
        # Создаем тест для Backend
        backend_test = Test(
            name="Backend Development Test",
            description="Тест на знание Backend технологий",
            test_type="backend",
            time_limit_per_question=90
        )
        db.add(backend_test)
        db.commit()
        db.refresh(backend_test)
        
        # Вопросы для Backend теста
        backend_questions = [
            {
                "question_text": "Quelle est la différence entre une API REST et une API GraphQL ?",
                "question_type": "text",
                "correct_answer": "REST utilise plusieurs endpoints, GraphQL utilise un seul endpoint avec des requêtes flexibles",
                "order": 1
            },
            {
                "question_text": "À quoi sert le middleware dans Express.js ?",
                "question_type": "text",
                "correct_answer": "Fonctions qui s'exécutent entre la requête et la réponse pour traiter, modifier ou valider les données",
                "order": 2
            },
            {
                "question_text": "Comment gérer les erreurs globales dans une API FastAPI ?",
                "question_type": "text",
                "correct_answer": "Utiliser des exception handlers et des middleware pour capturer et traiter les exceptions",
                "order": 3
            },
            {
                "question_text": "Expliquez le concept de JWT (JSON Web Token).",
                "question_type": "text",
                "correct_answer": "Un standard pour créer des tokens d'accès sécurisés contenant des informations encodées",
                "order": 4
            },
            {
                "question_text": "Quelle est la différence entre PUT et PATCH ?",
                "question_type": "text",
                "correct_answer": "PUT remplace complètement une ressource, PATCH met à jour partiellement une ressource",
                "order": 5
            },
            {
                "question_text": "Comment protéger une API contre les attaques par injection SQL ?",
                "question_type": "text",
                "correct_answer": "Utiliser des requêtes préparées, des ORM, et valider/sanitiser toutes les entrées",
                "order": 6
            },
            {
                "question_text": "Que signifie le terme ORM ? Citez-en un.",
                "question_type": "text",
                "correct_answer": "Object-Relational Mapping, exemples: SQLAlchemy, Prisma, TypeORM",
                "order": 7
            },
            {
                "question_text": "Quelle est la structure d'une relation many-to-many en SQL ?",
                "question_type": "text",
                "correct_answer": "Une table de jointure avec des clés étrangères vers les deux tables principales",
                "order": 8
            },
            {
                "question_text": "À quoi sert la commande docker-compose ?",
                "question_type": "text",
                "correct_answer": "Définir et exécuter des applications multi-conteneurs avec des services interdépendants",
                "order": 9
            },
            {
                "question_text": "Comment organiser une architecture MVC sur un backend web ?",
                "question_type": "text",
                "correct_answer": "Séparer les modèles (données), vues (présentation) et contrôleurs (logique métier)",
                "order": 10
            }
        ]
        
        for q_data in backend_questions:
            question = Question(
                test_id=backend_test.id,
                **q_data
            )
            db.add(question)
        
        db.commit()
        print("База данных успешно инициализирована!")
        print(f"Создано тестов: {db.query(Test).count()}")
        print(f"Создано вопросов: {db.query(Question).count()}")
        
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database() 