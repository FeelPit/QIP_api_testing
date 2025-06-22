from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json
import re

from app.models import User, Test, Question, TestResult, Answer, SuspiciousActivity
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