from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json
import re
import uuid
import traceback
from collections import defaultdict

from app.models import User, Test, Question, TestResult, Answer, SuspiciousActivity, AeonSession, AeonQuestion, AeonAnswer, AeonReport
from app.schemas import UserCreate, TestSubmission, TestResultCreate


class UserService:
    @staticmethod
    def get_or_create_user(db: Session, telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> User:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user


class TestService:
    @staticmethod
    def get_active_tests(db: Session) -> List[Test]:
        return db.query(Test).filter(Test.is_active == True).all()
    
    @staticmethod
    def get_test_by_id(db: Session, test_id: int) -> Optional[Test]:
        return db.query(Test).filter(Test.id == test_id, Test.is_active == True).first()
    
    @staticmethod
    def get_test_questions(db: Session, test_id: int) -> List[Question]:
        return db.query(Question).filter(
            Question.test_id == test_id
        ).order_by(Question.order).all()


class TestResultService:
    @staticmethod
    def create_test_result(db: Session, user_id: int, test_id: int) -> TestResult:
        test_result = TestResult(
            user_id=user_id,
            test_id=test_id,
            started_at=datetime.utcnow()
        )
        db.add(test_result)
        db.commit()
        db.refresh(test_result)
        return test_result
    
    @staticmethod
    def submit_test(db: Session, test_submission: TestSubmission, user_id: int) -> TestResult:
        # Получаем тест
        test = TestService.get_test_by_id(db, test_submission.test_id)
        if not test:
            raise ValueError("Test not found")
        
        # Создаем результат теста
        test_result = TestResult(
            user_id=user_id,
            test_id=test_submission.test_id,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(test_result)
        db.commit()
        db.refresh(test_result)
        
        # Обрабатываем ответы
        total_score = 0.0
        max_score = 0.0
        
        for answer_data in test_submission.answers:
            question = db.query(Question).filter(Question.id == answer_data.question_id).first()
            if not question:
                continue
            
            max_score += question.points
            
            # Проверяем правильность ответа
            is_correct = TestResultService._check_answer_correctness(question, answer_data.answer_text)
            points_earned = question.points if is_correct else 0.0
            total_score += points_earned
            
            # Сохраняем ответ
            answer = Answer(
                test_result_id=test_result.id,
                question_id=answer_data.question_id,
                answer_text=answer_data.answer_text,
                is_correct=is_correct,
                points_earned=points_earned,
                time_spent=answer_data.time_spent
            )
            db.add(answer)
        
        # Вычисляем процент
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Обновляем результат
        test_result.total_score = total_score
        test_result.max_score = max_score
        test_result.percentage = percentage
        
        # Анализируем подозрительную активность
        suspicious_reasons = TestResultService._analyze_suspicious_activity(
            db, test_result, test_submission
        )
        test_result.is_suspicious = len(suspicious_reasons) > 0
        test_result.suspicious_reasons = suspicious_reasons
        
        db.commit()
        db.refresh(test_result)
        
        return test_result
    
    @staticmethod
    def _check_answer_correctness(question: Question, answer_text: str) -> bool:
        if question.question_type == "multiple_choice":
            return answer_text.strip().lower() == question.correct_answer.strip().lower()
        else:
            # Для текстовых ответов - простая проверка на совпадение
            return answer_text.strip().lower() == question.correct_answer.strip().lower()
    
    @staticmethod
    def _analyze_suspicious_activity(db: Session, test_result: TestResult, 
                                   submission: TestSubmission) -> List[str]:
        reasons = []
        
        # Проверка на слишком быстрое прохождение
        if submission.total_time and submission.total_time < 30:
            reasons.append("too_fast_completion")
            
            suspicious = SuspiciousActivity(
                test_result_id=test_result.id,
                activity_type="too_fast",
                description=f"Test completed in {submission.total_time} seconds",
                confidence_score=0.8,
                details={"total_time": submission.total_time}
            )
            db.add(suspicious)
        
        # Проверка на одинаковые ответы
        identical_answers = TestResultService._check_identical_answers(db, test_result)
        if identical_answers:
            reasons.append("identical_answers")
            
            suspicious = SuspiciousActivity(
                test_result_id=test_result.id,
                activity_type="identical_answers",
                description=f"Found {len(identical_answers)} identical answers",
                confidence_score=0.7,
                details={"identical_answers": identical_answers}
            )
            db.add(suspicious)
        
        return reasons
    
    @staticmethod
    def _check_identical_answers(db: Session, test_result: TestResult) -> List[Dict]:
        identical = []
        
        current_answers = db.query(Answer).filter(
            Answer.test_result_id == test_result.id
        ).all()
        
        for current_answer in current_answers:
            similar_answers = db.query(Answer).filter(
                and_(
                    Answer.test_result_id != test_result.id,
                    Answer.question_id == current_answer.question_id,
                    Answer.answer_text == current_answer.answer_text
                )
            ).all()
            
            if similar_answers:
                identical.append({
                    "question_id": current_answer.question_id,
                    "answer_text": current_answer.answer_text,
                    "similar_count": len(similar_answers)
                })
        
        return identical


class ExportService:
    @staticmethod
    def export_results(db: Session, format: str, test_id: Optional[int] = None,
                      date_from: Optional[datetime] = None, 
                      date_to: Optional[datetime] = None,
                      include_suspicious: bool = True) -> Dict[str, Any]:
        
        query = db.query(TestResult)
        
        if test_id:
            query = query.filter(TestResult.test_id == test_id)
        
        if date_from:
            query = query.filter(TestResult.created_at >= date_from)
        
        if date_to:
            query = query.filter(TestResult.created_at <= date_to)
        
        if not include_suspicious:
            query = query.filter(TestResult.is_suspicious == False)
        
        results = query.all()
        
        if format == "json":
            return ExportService._export_to_json(db, results)
        elif format == "markdown":
            return ExportService._export_to_markdown(db, results)
        else:
            raise ValueError("Unsupported format")
    
    @staticmethod
    def _export_to_json(db: Session, results: List[TestResult]) -> Dict[str, Any]:
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "total_results": len(results),
            "results": []
        }
        
        for result in results:
            user = db.query(User).filter(User.id == result.user_id).first()
            test = db.query(Test).filter(Test.id == result.test_id).first()
            
            # Получаем все вопросы теста
            questions = db.query(Question).filter(
                Question.test_id == result.test_id
            ).order_by(Question.order).all()
            
            # Получаем все ответы пользователя
            answers = db.query(Answer).filter(
                Answer.test_result_id == result.id
            ).all()
            
            # Создаем словарь ответов для быстрого поиска
            answers_dict = {answer.question_id: answer for answer in answers}
            
            # Формируем детальную информацию о вопросах и ответах
            questions_answers = []
            for question in questions:
                answer = answers_dict.get(question.id)
                question_data = {
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "question_type": question.question_type,
                    "order": question.order,
                    "points": question.points,
                    "correct_answer": question.correct_answer,
                    "candidate_answer": {
                        "answer_text": answer.answer_text if answer else None,
                        "is_correct": answer.is_correct if answer else None,
                        "points_earned": answer.points_earned if answer else 0.0,
                        "time_spent": answer.time_spent if answer else None
                    } if answer else None
                }
                questions_answers.append(question_data)
            
            result_data = {
                "id": result.id,
                "user": {
                    "telegram_id": user.telegram_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip() or f"User {user.telegram_id}"
                },
                "test": {
                    "id": test.id,
                    "name": test.name,
                    "type": test.test_type,
                    "description": test.description
                },
                "score": {
                    "total": result.total_score,
                    "max": result.max_score,
                    "percentage": result.percentage
                },
                "timing": {
                    "started_at": result.started_at.isoformat(),
                    "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                    "total_duration": (result.completed_at - result.started_at).total_seconds() if result.completed_at else None
                },
                "suspicious": {
                    "is_suspicious": result.is_suspicious,
                    "reasons": result.suspicious_reasons or []
                },
                "questions_and_answers": questions_answers
            }
            
            export_data["results"].append(result_data)
        
        return export_data
    
    @staticmethod
    def _export_to_markdown(db: Session, results: List[TestResult]) -> Dict[str, Any]:
        markdown_content = f"""# Quantum Insight - Результаты тестирования

**Дата экспорта:** {datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')}
**Всего результатов:** {len(results)}

---

"""
        
        for result in results:
            user = db.query(User).filter(User.id == result.user_id).first()
            test = db.query(Test).filter(Test.id == result.test_id).first()
            
            # Получаем вопросы и ответы
            questions = db.query(Question).filter(
                Question.test_id == result.test_id
            ).order_by(Question.order).all()
            
            answers = db.query(Answer).filter(
                Answer.test_result_id == result.id
            ).all()
            
            answers_dict = {answer.question_id: answer for answer in answers}
            
            markdown_content += f"""## Результат #{result.id}

**Пользователь:** {user.first_name or ''} {user.last_name or ''} (@{user.username or 'None'})
**Telegram ID:** {user.telegram_id}
**Тест:** {test.name} ({test.test_type})

**Результаты:**
- Общий балл: {result.total_score}/{result.max_score}
- Процент: {result.percentage:.1f}%
- Время начала: {result.started_at.strftime('%d.%m.%Y %H:%M:%S')}
- Время завершения: {result.completed_at.strftime('%d.%m.%Y %H:%M:%S') if result.completed_at else 'Не завершен'}

**Подозрительная активность:** {'Да' if result.is_suspicious else 'Нет'}
"""
            
            if result.suspicious_reasons:
                markdown_content += f"**Причины:** {', '.join(result.suspicious_reasons)}\n"
            
            markdown_content += "\n**Вопросы и ответы:**\n\n"
            
            for question in questions:
                answer = answers_dict.get(question.id)
                markdown_content += f"**{question.order}. {question.question_text}**\n"
                markdown_content += f"- **Правильный ответ:** {question.correct_answer}\n"
                if answer:
                    markdown_content += f"- **Ответ кандидата:** {answer.answer_text}\n"
                    markdown_content += f"- **Правильно:** {'Да' if answer.is_correct else 'Нет'}\n"
                    markdown_content += f"- **Баллы:** {answer.points_earned}/{question.points}\n"
                    if answer.time_spent:
                        markdown_content += f"- **Время ответа:** {answer.time_spent} сек\n"
                else:
                    markdown_content += "- **Ответ кандидата:** Не отвечен\n"
                markdown_content += "\n"
            
            markdown_content += "---\n\n"
        
        return {
            "content": markdown_content,
            "filename": f"quantum_insight_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        }


class AeonInterviewService:
    """Сервис для проведения ÆON интервью с генерацией вопросов на лету"""
    
    # Базовые шаблоны вопросов на французском языке
    QUESTION_TEMPLATES = {
        "personality": [
            "Qu'est-ce qui est vraiment important pour toi dans le travail et dans la vie ? Qu'est-ce qui te motive profondément ?",
            "Comment décrirais-tu ton approche face aux défis ? Qu'est-ce qui te pousse à avancer ?",
            "Quelles sont tes valeurs fondamentales et comment elles influencent tes décisions ?"
        ],
        "thinking": [
            "Rappelle-toi d'une situation complexe où tu n'avais pas d'instructions claires. Comment as-tu procédé ?",
            "Es-tu plutôt stratège ou improvisateur ? Peux-tu me donner un exemple concret ?",
            "Comment gères-tu l'incertitude et les situations ambiguës ?"
        ],
        "potential": [
            "Que veux-tu laisser comme héritage dans une équipe ? Quel impact souhaites-tu avoir ?",
            "Si tu avais une liberté totale, quel projet créerais-tu ? Décris-le en détail.",
            "Comment vois-tu ton évolution professionnelle dans les 5 prochaines années ?"
        ],
        "behavior": [
            "Quand as-tu fait une erreur importante pour la dernière fois ? Qu'as-tu appris de cette expérience ?",
            "Peux-tu me parler d'un moment où tu as agi à la limite de tes capacités ? Comment l'as-tu vécu ?",
            "Comment réagis-tu face à la critique et aux feedbacks négatifs ?"
        ],
        "integration": [
            "Comment imagines-tu ta place dans l'écosystème Quantum Insight ?",
            "Si tu devenais partie intégrante de notre système, qu'est-ce que tu améliorerais en priorité ?",
            "Comment vois-tu ta contribution à notre vision du futur ?"
        ]
    }
    
    @staticmethod
    def start_interview(db: Session, user_id: Optional[int] = None, 
                       candidate_name: Optional[str] = None, 
                       candidate_email: Optional[str] = None) -> Dict[str, Any]:
        """Начать новое интервью ÆON"""
        import uuid
        
        # Создаем новую сессию
        session_id = str(uuid.uuid4())
        session = AeonSession(
            session_id=session_id,
            user_id=user_id,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            current_question=1,  # Начинаем с первого вопроса
            total_questions=5,
            status="active"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Генерируем первый вопрос
        first_question = AeonInterviewService._generate_question(db, session.id, 1, "personality")
        
        return {
            "session_id": session_id,
            "question": first_question.question_text,
            "question_number": 1,
            "total_questions": 5,
            "message": "Bonjour, je suis ÆON — l'intervieweur de Quantum Insight. Ce n'est pas un entretien formel, mais une exploration de qui tu es, comment tu penses, et comment tu pourrais nous renforcer."
        }
    
    @staticmethod
    def process_answer(db: Session, session_id: str, answer: str) -> Dict[str, Any]:
        """Обработать ответ и получить следующий вопрос или финальный отчет"""
        # Находим сессию
        session = db.query(AeonSession).filter(AeonSession.session_id == session_id).first()
        if session.current_question > session.total_questions:
            try:
                session.status = "completed"
                session.completed_at = datetime.utcnow()
                db.commit()
                report = AeonInterviewService._generate_final_report(db, session.id)
            except Exception as e:
                print("ÆON REPORT ERROR:", e)
                print(traceback.format_exc())
                raise
            return {
                "session_id": session_id,
                "is_completed": True,
                "total_questions": session.total_questions,
                "report": report,
                "message": "Merci pour cet entretien profond. Voici ton rapport d'évaluation ÆON."
            }
        if not session:
            raise ValueError("Session not found")
        
        if session.status != "active":
            raise ValueError("Session is not active")
        
        # Получаем текущий вопрос
        current_question = db.query(AeonQuestion).filter(
            AeonQuestion.session_id == session.id,
            AeonQuestion.question_number == session.current_question
        ).first()
        
        if not current_question:
            raise ValueError("Current question not found")
        
        # Сохраняем ответ с анализом
        answer_analysis = AeonInterviewService._analyze_answer(answer, current_question.question_type)
        aeon_answer = AeonAnswer(
            question_id=current_question.id,
            answer_text=answer,
            analysis=answer_analysis,
            sentiment_score=answer_analysis.get("sentiment_score"),
            confidence_score=answer_analysis.get("confidence_score")
        )
        db.add(aeon_answer)
        
        # Переходим к следующему вопросу
        session.current_question += 1
        
        # Проверяем, завершено ли интервью
        if session.current_question > session.total_questions:
            try:
                session.status = "completed"
                session.completed_at = datetime.utcnow()
                db.commit()
                report = AeonInterviewService._generate_final_report(db, session.id)
            except Exception as e:
                print("ÆON REPORT ERROR:", e)
                print(traceback.format_exc())
                raise
            return {
                "session_id": session_id,
                "is_completed": True,
                "total_questions": session.total_questions,
                "report": report,
                "message": "Merci pour cet entretien profond. Voici ton rapport d'évaluation ÆON."
            }
        else:
            # Генерируем следующий вопрос
            next_question = AeonInterviewService._generate_question(
                db, session.id, session.current_question, 
                AeonInterviewService._get_question_type(session.current_question)
            )
            db.commit()
            
            return {
                "session_id": session_id,
                "next_question": next_question.question_text,
                "question_number": session.current_question,
                "total_questions": session.total_questions,
                "is_completed": False,
                "message": "Merci pour ta réponse. Voici la question suivante."
            }
    
    @staticmethod
    def get_report_json(db: Session, session_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Получить отчет в формате JSON для скачивания"""
        session = db.query(AeonSession).filter(AeonSession.session_id == session_id).first()
        if not session:
            return None, None
        
        report = db.query(AeonReport).filter(AeonReport.session_id == session.id).first()
        if not report:
            return None, None
        
        # Формируем полный отчет на русском языке
        full_report = {
            "session_info": {
                "session_id": session_id,
                "candidate_name": session.candidate_name,
                "candidate_email": session.candidate_email,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "total_questions": session.total_questions
            },
            "candidate_assessment": {
                "archetype": report.archetype,
                "consciousness_vector": report.consciousness_vector,
                "motivation_score": report.motivation_score,
                "growth_zone": report.growth_zone,
                "genius_zone": report.genius_zone,
                "synergy_score": report.synergy_score,
                "flexibility_score": report.flexibility_score,
                "independence_score": report.independence_score,
                "adaptability_score": report.adaptability_score
            },
            "overall_assessment": report.overall_assessment,
            "recommendations": report.recommendations,
            "detailed_analysis": report.report_json
        }
        
        report_json = json.dumps(full_report, ensure_ascii=False, indent=2)
        filename = f"aeon_report_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        return report_json, filename
    
    @staticmethod
    def _generate_question(db: Session, session_id: int, question_number: int, question_type: str) -> AeonQuestion:
        """Генерировать вопрос на лету"""
        import random
        
        # Выбираем случайный шаблон для данного типа вопроса
        templates = AeonInterviewService.QUESTION_TEMPLATES.get(question_type, [])
        if not templates:
            # Fallback шаблон
            templates = ["Peux-tu me parler de ton expérience dans ce domaine ?"]
        
        question_text = random.choice(templates)
        
        # Создаем вопрос в базе
        question = AeonQuestion(
            session_id=session_id,
            question_number=question_number,
            question_text=question_text,
            question_type=question_type
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        
        return question
    
    @staticmethod
    def _get_question_type(question_number: int) -> str:
        """Определить тип вопроса по номеру"""
        question_types = ["personality", "thinking", "potential", "behavior", "integration"]
        return question_types[question_number - 1] if 1 <= question_number <= 5 else "personality"
    
    @staticmethod
    def _analyze_answer(answer: str, question_type: str) -> Dict[str, Any]:
        """Анализировать ответ кандидата"""
        # Здесь можно интегрировать более сложный NLP анализ
        # Пока используем простую логику
        
        analysis = {
            "length": len(answer),
            "sentiment_score": AeonInterviewService._calculate_sentiment(answer),
            "confidence_score": AeonInterviewService._calculate_confidence(answer),
            "keywords": AeonInterviewService._extract_keywords(answer),
            "question_type": question_type
        }
        
        # Специфичный анализ по типу вопроса
        if question_type == "personality":
            analysis["motivation_indicators"] = AeonInterviewService._analyze_motivation(answer)
        elif question_type == "thinking":
            analysis["thinking_pattern"] = AeonInterviewService._analyze_thinking_pattern(answer)
        elif question_type == "potential":
            analysis["potential_indicators"] = AeonInterviewService._analyze_potential(answer)
        elif question_type == "behavior":
            analysis["behavior_pattern"] = AeonInterviewService._analyze_behavior(answer)
        elif question_type == "integration":
            analysis["integration_readiness"] = AeonInterviewService._analyze_integration(answer)
        
        return analysis
    
    @staticmethod
    def _calculate_sentiment(text: str) -> float:
        """Простой расчет сентимента"""
        positive_words = ["excellent", "génial", "super", "fantastique", "positif", "bon", "bien", "motivé", "passionné"]
        negative_words = ["difficile", "problème", "négatif", "mauvais", "stress", "anxiété", "peur"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_words
    
    @staticmethod
    def _calculate_confidence(text: str) -> float:
        """Оценка уверенности в ответе"""
        confidence_indicators = ["je pense", "je crois", "peut-être", "probablement", "sûrement", "certainement"]
        uncertainty_indicators = ["je ne sais pas", "je ne suis pas sûr", "peut-être", "probablement"]
        
        text_lower = text.lower()
        confidence_count = sum(1 for indicator in confidence_indicators if indicator in text_lower)
        uncertainty_count = sum(1 for indicator in uncertainty_indicators if indicator in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.5
        
        base_confidence = 0.5
        confidence_bonus = confidence_count * 0.1
        uncertainty_penalty = uncertainty_count * 0.1
        
        return max(0.0, min(1.0, base_confidence + confidence_bonus - uncertainty_penalty))
    
    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """Извлечение ключевых слов"""
        # Простая реализация - можно заменить на более сложную
        stop_words = ["le", "la", "les", "de", "du", "des", "et", "ou", "mais", "je", "tu", "il", "elle", "nous", "vous", "ils", "elles"]
        words = text.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        return keywords[:10]  # Возвращаем топ-10 ключевых слов
    
    @staticmethod
    def _analyze_motivation(text: str) -> Dict[str, Any]:
        """Анализ мотивации"""
        motivation_keywords = ["passion", "motivation", "objectif", "but", "rêve", "ambition", "désir", "envie"]
        text_lower = text.lower()
        
        found_keywords = [word for word in motivation_keywords if word in text_lower]
        
        return {
            "motivation_keywords": found_keywords,
            "motivation_level": len(found_keywords) / len(motivation_keywords)
        }
    
    @staticmethod
    def _analyze_thinking_pattern(text: str) -> Dict[str, Any]:
        """Анализ паттерна мышления"""
        strategic_indicators = ["plan", "stratégie", "méthode", "processus", "analyse", "réflexion"]
        improvisation_indicators = ["intuition", "instinct", "spontanéité", "adaptation", "flexibilité"]
        
        text_lower = text.lower()
        strategic_count = sum(1 for word in strategic_indicators if word in text_lower)
        improvisation_count = sum(1 for word in improvisation_indicators if word in text_lower)
        
        total = strategic_count + improvisation_count
        if total == 0:
            return {"thinking_style": "balanced", "strategic_ratio": 0.5}
        
        strategic_ratio = strategic_count / total
        if strategic_ratio > 0.6:
            thinking_style = "strategic"
        elif strategic_ratio < 0.4:
            thinking_style = "improvisational"
        else:
            thinking_style = "balanced"
        
        return {
            "thinking_style": thinking_style,
            "strategic_ratio": strategic_ratio
        }
    
    @staticmethod
    def _analyze_potential(text: str) -> Dict[str, Any]:
        """Анализ потенциала"""
        potential_indicators = ["créer", "innover", "développer", "construire", "transformer", "améliorer", "contribuer"]
        text_lower = text.lower()
        
        found_indicators = [word for word in potential_indicators if word in text_lower]
        
        return {
            "potential_indicators": found_indicators,
            "potential_score": len(found_indicators) / len(potential_indicators)
        }
    
    @staticmethod
    def _analyze_behavior(text: str) -> Dict[str, Any]:
        """Анализ поведения"""
        learning_indicators = ["appris", "compris", "réalisé", "découvert", "évolué", "changé"]
        resilience_indicators = ["persévéré", "continué", "surmonté", "adapté", "résisté"]
        
        text_lower = text.lower()
        learning_count = sum(1 for word in learning_indicators if word in text_lower)
        resilience_count = sum(1 for word in resilience_indicators if word in text_lower)
        
        return {
            "learning_orientation": learning_count > 0,
            "resilience_level": resilience_count / len(resilience_indicators) if resilience_indicators else 0
        }
    
    @staticmethod
    def _analyze_integration(text: str) -> Dict[str, Any]:
        """Анализ готовности к интеграции"""
        team_indicators = ["équipe", "collaboration", "partage", "ensemble", "collectif"]
        improvement_indicators = ["améliorer", "optimiser", "perfectionner", "développer", "innover"]
        
        text_lower = text.lower()
        team_count = sum(1 for word in team_indicators if word in text_lower)
        improvement_count = sum(1 for word in improvement_indicators if word in text_lower)
        
        return {
            "team_orientation": team_count > 0,
            "improvement_orientation": improvement_count > 0,
            "integration_readiness": (team_count + improvement_count) / (len(team_indicators) + len(improvement_indicators))
        }
    
    @staticmethod
    def _generate_final_report(db: Session, session_id: int) -> Dict[str, Any]:
        """Генерировать финальный отчет на основе всех ответов"""
        # Получаем все ответы с анализом
        session = db.query(AeonSession).filter(AeonSession.id == session_id).first()
        questions = db.query(AeonQuestion).filter(AeonQuestion.session_id == session_id).all()
        
        all_analyses = []
        for question in questions:
            answer = db.query(AeonAnswer).filter(AeonAnswer.question_id == question.id).first()
            if answer and answer.analysis:
                all_analyses.append({
                    "question_type": question.question_type,
                    "analysis": answer.analysis
                })
        
        # Генерируем оценки
        archetype = AeonInterviewService._detect_archetype(all_analyses)
        consciousness_vector = AeonInterviewService._detect_consciousness_vector(all_analyses)
        motivation_score = AeonInterviewService._calculate_motivation_score(all_analyses)
        growth_zone = AeonInterviewService._identify_growth_zone(all_analyses)
        genius_zone = AeonInterviewService._identify_genius_zone(all_analyses)
        synergy_score = AeonInterviewService._calculate_synergy_score(all_analyses)
        flexibility_score = AeonInterviewService._calculate_flexibility_score(all_analyses)
        independence_score = AeonInterviewService._calculate_independence_score(all_analyses)
        adaptability_score = AeonInterviewService._calculate_adaptability_score(all_analyses)
        
        # Формируем общую оценку
        overall_assessment = AeonInterviewService._generate_overall_assessment(
            archetype, consciousness_vector, motivation_score, synergy_score
        )
        
        # Формируем рекомендации
        recommendations = AeonInterviewService._generate_recommendations(
            growth_zone, genius_zone, flexibility_score, independence_score, adaptability_score
        )
        
        # Создаем полный отчет
        full_report = {
            "archetype": archetype,
            "consciousness_vector": consciousness_vector,
            "motivation_score": motivation_score,
            "growth_zone": growth_zone,
            "genius_zone": genius_zone,
            "synergy_score": synergy_score,
            "flexibility_score": flexibility_score,
            "independence_score": independence_score,
            "adaptability_score": adaptability_score,
            "overall_assessment": overall_assessment,
            "recommendations": recommendations,
            "detailed_analyses": all_analyses
        }
        
        # Сохраняем отчет в базу
        report = AeonReport(
            session_id=session_id,
            archetype=archetype,
            consciousness_vector=consciousness_vector,
            motivation_score=motivation_score,
            growth_zone=growth_zone,
            genius_zone=genius_zone,
            synergy_score=synergy_score,
            flexibility_score=flexibility_score,
            independence_score=independence_score,
            adaptability_score=adaptability_score,
            overall_assessment=overall_assessment,
            recommendations=recommendations,
            report_json=full_report
        )
        db.add(report)
        db.commit()
        
        return full_report
    
    @staticmethod
    def _detect_archetype(analyses: List[Dict]) -> str:
        """Определить архетип кандидата"""
        # Анализируем паттерны в ответах
        thinking_styles = []
        motivation_levels = []
        
        for analysis in analyses:
            if "thinking_pattern" in analysis["analysis"]:
                thinking_styles.append(analysis["analysis"]["thinking_pattern"]["thinking_style"])
            if "motivation_indicators" in analysis["analysis"]:
                motivation_levels.append(analysis["analysis"]["motivation_indicators"]["motivation_level"])
        
        # Определяем архетип на основе паттернов
        if thinking_styles.count("strategic") > len(thinking_styles) / 2:
            if any(level > 0.5 for level in motivation_levels):
                return "Стратег-Вдохновитель"
            else:
                return "Аналитик-Планировщик"
        elif thinking_styles.count("improvisational") > len(thinking_styles) / 2:
            if any(level > 0.5 for level in motivation_levels):
                return "Инноватор-Творец"
            else:
                return "Адаптер-Решатель"
        else:
            return "Гармонизатор-Интегратор"
    
    @staticmethod
    def _detect_consciousness_vector(analyses: List[Dict]) -> str:
        """Определить вектор сознания"""
        # Анализируем общие паттерны
        has_learning = any("learning_orientation" in a["analysis"] and a["analysis"]["learning_orientation"] for a in analyses)
        has_resilience = any("resilience_level" in a["analysis"] and a["analysis"]["resilience_level"] > 0.3 for a in analyses)
        has_team_orientation = any("team_orientation" in a["analysis"] and a["analysis"]["team_orientation"] for a in analyses)
        
        if has_learning and has_resilience:
            return "Эволюционный"
        elif has_team_orientation:
            return "Коллективный"
        else:
            return "Индивидуальный"
    
    @staticmethod
    def _calculate_motivation_score(analyses: List[Dict]) -> float:
        """Рассчитать оценку мотивации"""
        motivation_scores = []
        for analysis in analyses:
            if "motivation_indicators" in analysis["analysis"]:
                motivation_scores.append(analysis["analysis"]["motivation_indicators"]["motivation_level"])
        
        return sum(motivation_scores) / len(motivation_scores) if motivation_scores else 0.5
    
    @staticmethod
    def _identify_growth_zone(analyses: List[Dict]) -> str:
        """Определить зону роста"""
        # Анализируем слабые стороны
        low_scores = []
        for analysis in analyses:
            if "sentiment_score" in analysis["analysis"] and analysis["analysis"]["sentiment_score"] < 0:
                low_scores.append(analysis["question_type"])
        
        if "behavior" in low_scores:
            return "Работа с ошибками и кризисными ситуациями"
        elif "thinking" in low_scores:
            return "Стратегическое планирование и анализ"
        elif "integration" in low_scores:
            return "Командная работа и коммуникация"
        else:
            return "Общее развитие soft skills"
    
    @staticmethod
    def _identify_genius_zone(analyses: List[Dict]) -> str:
        """Определить зону гениальности"""
        # Анализируем сильные стороны
        high_scores = []
        for analysis in analyses:
            if "sentiment_score" in analysis["analysis"] and analysis["analysis"]["sentiment_score"] > 0.1:
                high_scores.append(analysis["question_type"])
        
        if "potential" in high_scores:
            return "Стратегическое видение и инновации"
        elif "personality" in high_scores:
            return "Лидерство и мотивация команды"
        elif "thinking" in high_scores:
            return "Аналитическое мышление и решение проблем"
        else:
            return "Адаптивность и быстрая обучаемость"
    
    @staticmethod
    def _calculate_synergy_score(analyses: List[Dict]) -> float:
        """Рассчитать оценку синергии с командой"""
        synergy_scores = []
        for analysis in analyses:
            if "integration_readiness" in analysis["analysis"]:
                score = analysis["analysis"]["integration_readiness"]
                # Проверяем, что это число
                if isinstance(score, (int, float)):
                    synergy_scores.append(score)
        
        return sum(synergy_scores) / len(synergy_scores) if synergy_scores else 0.5
    
    @staticmethod
    def _calculate_flexibility_score(analyses: List[Dict]) -> float:
        """Рассчитать оценку гибкости мышления"""
        flexibility_scores = []
        for analysis in analyses:
            if "thinking_pattern" in analysis["analysis"]:
                # Сбалансированное мышление = высокая гибкость
                if analysis["analysis"]["thinking_pattern"]["thinking_style"] == "balanced":
                    flexibility_scores.append(0.8)
                else:
                    flexibility_scores.append(0.6)
        
        return sum(flexibility_scores) / len(flexibility_scores) if flexibility_scores else 0.6
    
    @staticmethod
    def _calculate_independence_score(analyses: List[Dict]) -> float:
        """Рассчитать оценку самостоятельности"""
        independence_scores = []
        for analysis in analyses:
            if "confidence_score" in analysis["analysis"]:
                independence_scores.append(analysis["analysis"]["confidence_score"])
        
        return sum(independence_scores) / len(independence_scores) if independence_scores else 0.5
    
    @staticmethod
    def _calculate_adaptability_score(analyses: List[Dict]) -> float:
        """Рассчитать оценку адаптивности"""
        adaptability_scores = []
        for analysis in analyses:
            if "resilience_level" in analysis["analysis"]:
                adaptability_scores.append(analysis["analysis"]["resilience_level"])
        
        return sum(adaptability_scores) / len(adaptability_scores) if adaptability_scores else 0.5
    
    @staticmethod
    def _generate_overall_assessment(archetype: str, consciousness_vector: str, 
                                   motivation_score: float, synergy_score: float) -> str:
        """Генерировать общую оценку"""
        if motivation_score > 0.7 and synergy_score > 0.7:
            return f"Кандидат демонстрирует высокий потенциал для интеграции в команду Quantum Insight. Архетип '{archetype}' с вектором сознания '{consciousness_vector}' указывает на сильную мотивацию и готовность к синергии."
        elif motivation_score > 0.5 and synergy_score > 0.5:
            return f"Кандидат показывает хорошие перспективы. Архетип '{archetype}' требует развития в области командной работы, но мотивация на достаточном уровне."
        else:
            return f"Кандидат требует дополнительной оценки. Архетип '{archetype}' может быть подходящим, но необходима работа над мотивацией и командной интеграцией."
    
    @staticmethod
    def _generate_recommendations(growth_zone: str, genius_zone: str, 
                                flexibility_score: float, independence_score: float, 
                                adaptability_score: float) -> Dict[str, Any]:
        """Генерировать рекомендации"""
        recommendations = {
            "immediate_actions": [],
            "development_plan": [],
            "team_integration": []
        }
        
        # Немедленные действия
        if flexibility_score < 0.6:
            recommendations["immediate_actions"].append("Тренировка адаптивного мышления")
        if independence_score < 0.6:
            recommendations["immediate_actions"].append("Развитие уверенности в принятии решений")
        
        # План развития
        recommendations["development_plan"].append(f"Фокус на зоне роста: {growth_zone}")
        recommendations["development_plan"].append(f"Развитие зоны гениальности: {genius_zone}")
        
        # Интеграция в команду
        if adaptability_score > 0.7:
            recommendations["team_integration"].append("Быстрая интеграция в проектную команду")
        else:
            recommendations["team_integration"].append("Постепенная интеграция с менторской поддержкой")
        
        return recommendations 