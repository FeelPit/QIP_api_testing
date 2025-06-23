from fastapi import APIRouter, HTTPException, Request, Response, Depends
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    APIResponse, AeonInterviewStartRequest, AeonInterviewStartResponse,
    AeonInterviewAnswerRequest, AeonInterviewAnswerResponse,
    AeonInterviewDownloadRequest
)
from app.services import AeonInterviewService

router = APIRouter(prefix="/api/aeon", tags=["aeon_interview"])

@router.post("/start_interview", response_model=APIResponse)
def start_interview(request: AeonInterviewStartRequest, db: Session = Depends(get_db)):
    """Начать интервью ÆON, получить первый вопрос (на французском)"""
    try:
        result = AeonInterviewService.start_interview(
            db, 
            request.user_id, 
            request.user_name, 
            request.user_email
        )
        return APIResponse(
            success=True, 
            message="Interview started successfully", 
            data=AeonInterviewStartResponse(
                session_id=result["session_id"],
                question=result["question"],
                question_number=result["question_number"],
                total_questions=result["total_questions"],
                message=result["message"]
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

@router.post("/answer", response_model=APIResponse)
def answer(request: AeonInterviewAnswerRequest, db: Session = Depends(get_db)):
    """Отправить ответ, получить следующий вопрос или финальный отчёт"""
    try:
        result = AeonInterviewService.process_answer(db, request.session_id, request.answer)
        
        if result.get("is_completed"):
            return APIResponse(
                success=True, 
                message="Interview completed", 
                data=AeonInterviewAnswerResponse(
                    session_id=result["session_id"],
                    total_questions=result["total_questions"],
                    is_completed=True,
                    report=result["report"],
                    message=result["message"]
                )
            )
        else:
            return APIResponse(
                success=True, 
                message="Next question", 
                data=AeonInterviewAnswerResponse(
                    session_id=result["session_id"],
                    next_question=result["next_question"],
                    question_number=result["question_number"],
                    total_questions=result["total_questions"],
                    is_completed=False,
                    message=result["message"]
                )
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process answer: {str(e)}")

@router.get("/download_report/{session_id}")
def download_report(session_id: str, db: Session = Depends(get_db)):
    """Скачать итоговый отчёт интервью ÆON в формате JSON (на русском)"""
    try:
        report_json, filename = AeonInterviewService.get_report_json(db, session_id)
        if not report_json:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return Response(
            content=report_json,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download report: {str(e)}")

@router.get("/session/{session_id}/status")
def get_session_status(session_id: str, db: Session = Depends(get_db)):
    """Получить статус сессии интервью"""
    try:
        from app.models import AeonSession
        session = db.query(AeonSession).filter(AeonSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return APIResponse(
            success=True,
            message="Session status retrieved",
            data={
                "session_id": session.session_id,
                "status": session.status,
                "current_question": session.current_question,
                "total_questions": session.total_questions,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at is not None else None
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

@router.get("/session/{session_id}/report")
def get_session_report(session_id: str, db: Session = Depends(get_db)):
    """Получить отчет сессии (если завершена)"""
    try:
        from app.models import AeonSession, AeonReport
        session = db.query(AeonSession).filter(AeonSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.status != "completed":
            raise HTTPException(status_code=400, detail="Session is not completed")
        
        report = db.query(AeonReport).filter(AeonReport.session_id == session.id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return APIResponse(
            success=True,
            message="Report retrieved successfully",
            data={
                "archetype": report.archetype,
                "consciousness_vector": report.consciousness_vector,
                "motivation_score": report.motivation_score,
                "growth_zone": report.growth_zone,
                "genius_zone": report.genius_zone,
                "synergy_score": report.synergy_score,
                "flexibility_score": report.flexibility_score,
                "independence_score": report.independence_score,
                "adaptability_score": report.adaptability_score,
                "overall_assessment": report.overall_assessment,
                "recommendations": report.recommendations
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}") 