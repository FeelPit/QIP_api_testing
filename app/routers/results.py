from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.schemas import TestResult as TestResultSchema, ExportRequest, ExportResponse
from app.services import ExportService

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/", response_model=List[TestResultSchema])
def get_results(
    db: Session = Depends(get_db),
    test_id: Optional[int] = None,
    include_suspicious: bool = True
):
    """Получить результаты тестов (для админов)"""
    # В реальном проекте здесь должна быть проверка авторизации
    
    query = db.query(TestResultSchema)
    
    if test_id:
        query = query.filter(TestResultSchema.test_id == test_id)
    
    if not include_suspicious:
        query = query.filter(TestResultSchema.is_suspicious == False)
    
    results = query.all()
    return results


@router.get("/{result_id}", response_model=TestResultSchema)
def get_result(result_id: int, db: Session = Depends(get_db)):
    """Получить конкретный результат теста"""
    result = db.query(TestResultSchema).filter(TestResultSchema.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.post("/export", response_model=ExportResponse)
def export_results(
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Экспорт результатов в JSON или Markdown"""
    try:
        export_data = ExportService.export_results(
            db=db,
            format=export_request.format,
            test_id=export_request.test_id,
            date_from=export_request.date_from,
            date_to=export_request.date_to,
            include_suspicious=export_request.include_suspicious
        )
        
        if export_request.format == "markdown":
            return ExportResponse(
                data={"content": export_data["content"]},
                format="markdown",
                filename=export_data["filename"]
            )
        else:
            return ExportResponse(
                data=export_data,
                format="json",
                filename=f"quantum_insight_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Export failed")


@router.get("/export/download/{format}")
def download_export(
    format: str,
    test_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Скачать экспорт результатов"""
    if format not in ["json", "markdown"]:
        raise HTTPException(status_code=400, detail="Unsupported format")
    
    try:
        export_data = ExportService.export_results(
            db=db,
            format=format,
            test_id=test_id
        )
        
        if format == "markdown":
            content = export_data["content"]
            filename = export_data["filename"]
            media_type = "text/markdown"
        else:
            import json
            content = json.dumps(export_data, indent=2, ensure_ascii=False)
            filename = f"quantum_insight_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            media_type = "application/json"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Export failed") 