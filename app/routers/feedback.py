"""
Feedback API routes
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.feedback import Feedback
from app.models.analysis import Analysis
from app.services.feedback_service import FeedbackService
from app.utils.helpers import validate_rating
from app.deps import require_role
from app.sockets.events import emit_new_feedback, emit_urgent_alert, emit_analysis_complete

router = APIRouter(prefix="/feedback", tags=["feedback"])


# Pydantic models
class FeedbackCreate(BaseModel):
    patient_name: Optional[str] = None
    visit_date: datetime
    department: str
    doctor_name: Optional[str] = None
    feedback_text: str = Field(..., min_length=10)
    rating: int = Field(..., ge=1, le=5)
    
    @validator('rating')
    def validate_rating(cls, v):
        if not validate_rating(v):
            raise ValueError('Rating must be between 1 and 5')
        return v


class FeedbackUpdate(BaseModel):
    status: str = Field(..., pattern="^(reviewed|in_progress|resolved)$")
    staff_note: Optional[str] = None
    assigned_department: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    patient_name: Optional[str]
    visit_date: datetime
    department: str
    doctor_name: Optional[str]
    feedback_text: str
    rating: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    id: int
    feedback_id: int
    sentiment: str
    confidence_score: float
    emotions: Optional[List[str]]
    urgency: str
    urgency_reason: Optional[str]
    urgency_flags: Optional[List[str]]
    primary_category: Optional[str]
    subcategories: Optional[List[str]]
    medical_concerns: Optional[dict]
    actionable_insights: Optional[str]
    key_points: Optional[List[str]]
    
    class Config:
        from_attributes = True


class FeedbackDetailResponse(FeedbackResponse):
    analysis: Optional[AnalysisResponse] = None
    actions: Optional[List[dict]] = None


@router.post("", response_model=FeedbackResponse, status_code=201)
async def create_feedback(
    feedback_data: FeedbackCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Submit new feedback"""
    try:
        feedback = await FeedbackService.create_feedback(
            db=db,
            patient_name=feedback_data.patient_name,
            visit_date=feedback_data.visit_date,
            department=feedback_data.department,
            doctor_name=feedback_data.doctor_name,
            feedback_text=feedback_data.feedback_text,
            rating=feedback_data.rating
        )
        
        # Emit new feedback event
        await emit_new_feedback(feedback)
        
        # Trigger background analysis
        background_tasks.add_task(
            analyze_feedback_background,
            feedback_id=feedback.id,
            db=db
        )
        
        return feedback
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating feedback: {str(e)}")


async def analyze_feedback_background(feedback_id: int, db: AsyncSession):
    """Background task for analyzing feedback"""
    try:
        print(f"🔄 Starting AI analysis for feedback {feedback_id}...")
        analysis = await FeedbackService.analyze_feedback_async(db, feedback_id)
        
        if analysis:
            print(f"✅ Analysis saved for feedback {feedback_id}")
            print(f"   Sentiment: {analysis.sentiment}, Urgency: {analysis.urgency}")
            
            # Emit analysis complete event
            await emit_analysis_complete(feedback_id, analysis)
            
            # Check if urgent and emit alert
            if analysis.urgency == "critical":
                print(f"🚨 CRITICAL feedback detected: {feedback_id}")
                feedback = await FeedbackService.get_feedback_by_id(db, feedback_id)
                if feedback:
                    await emit_urgent_alert(feedback, analysis)
        else:
            print(f"⚠️ Analysis failed or returned None for feedback {feedback_id}")
    except Exception as e:
        print(f"❌ Error in background analysis for feedback {feedback_id}: {e}")
        import traceback
        traceback.print_exc()


@router.get("/all", response_model=dict, dependencies=[Depends(require_role("admin", "staff"))])
async def get_all_feedback(
    department: Optional[str] = Query(None, description="Filter by department"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    priority: Optional[str] = Query(None, description="Filter by urgency (critical/high/medium/low)"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    format: str = Query("json", pattern="^(json|csv)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get all feedback with filters"""
    try:
        feedbacks, total = await FeedbackService.get_all_feedback(
            db=db,
            department=department,
            start_date=start_date,
            end_date=end_date,
            priority=priority,
            sentiment=sentiment,
            category=category,
            status=status,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        feedback_list = []
        for feedback in feedbacks:
            try:
                feedback_dict = {
                    "id": feedback.id,
                    "patient_name": feedback.patient_name,
                    "visit_date": feedback.visit_date.isoformat() if feedback.visit_date else None,
                    "department": feedback.department,
                    "doctor_name": feedback.doctor_name,
                    "feedback_text": feedback.feedback_text,
                    "rating": feedback.rating,
                    "status": feedback.status,
                    "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
                    "urgency": feedback.analysis.urgency if feedback.analysis else None,
                    "sentiment": feedback.analysis.sentiment if feedback.analysis else None,
                    "primary_category": feedback.analysis.primary_category if feedback.analysis else None,
                    "analysis_status": "completed" if feedback.analysis else "pending"
                }
                feedback_list.append(feedback_dict)
            except Exception as e:
                # Skip problematic feedback items
                print(f"Error processing feedback {feedback.id}: {e}")
                continue
        
        response = {
            "total": total,
            "limit": limit,
            "offset": offset,
            "feedbacks": feedback_list
        }
        
        # CSV export
        if format == "csv":
            from fastapi.responses import Response
            import csv
            import io
            
            output = io.StringIO()
            if feedback_list:
                # Flatten nested data for CSV
                csv_data = []
                for item in feedback_list:
                    csv_row = {
                        "id": item.get("id"),
                        "patient_name": item.get("patient_name") or "",
                        "visit_date": item.get("visit_date") or "",
                        "department": item.get("department") or "",
                        "doctor_name": item.get("doctor_name") or "",
                        "feedback_text": item.get("feedback_text") or "",
                        "rating": item.get("rating"),
                        "status": item.get("status") or "",
                        "sentiment": item.get("sentiment") or "",
                        "urgency": item.get("urgency") or "",
                        "primary_category": item.get("primary_category") or "",
                        "created_at": item.get("created_at") or ""
                    }
                    csv_data.append(csv_row)
                
                if csv_data:
                    writer = csv.DictWriter(output, fieldnames=csv_data[0].keys())
                    writer.writeheader()
                    writer.writerows(csv_data)
            
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=feedback_export.csv"}
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching feedback: {str(e)}")


@router.get("/urgent", response_model=dict, dependencies=[Depends(require_role("admin", "staff"))])
async def get_urgent_feedback(
    limit: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get all urgent/critical feedback"""
    try:
        feedbacks, total = await FeedbackService.get_all_feedback(
            db=db,
            priority="critical",
            limit=limit,
            offset=0
        )
        
        feedback_list = []
        for feedback in feedbacks:
            try:
                feedback_dict = {
                    "id": feedback.id,
                    "patient_name": feedback.patient_name,
                    "visit_date": feedback.visit_date.isoformat() if feedback.visit_date else None,
                    "department": feedback.department,
                    "doctor_name": feedback.doctor_name,
                    "feedback_text": feedback.feedback_text,
                    "rating": feedback.rating,
                    "status": feedback.status,
                    "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
                    "urgency": feedback.analysis.urgency if feedback.analysis else None,
                    "urgency_reason": feedback.analysis.urgency_reason if feedback.analysis else None,
                    "urgency_flags": feedback.analysis.urgency_flags if feedback.analysis else None,
                    "sentiment": feedback.analysis.sentiment if feedback.analysis else None,
                    "primary_category": feedback.analysis.primary_category if feedback.analysis else None,
                    "actionable_insights": feedback.analysis.actionable_insights if feedback.analysis else None
                }
                feedback_list.append(feedback_dict)
            except Exception as e:
                print(f"Error processing feedback {feedback.id}: {e}")
                continue
        
        return {
            "total": total,
            "urgent_feedbacks": feedback_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching urgent feedback: {str(e)}")


@router.get("/{feedback_id}", response_model=FeedbackDetailResponse, dependencies=[Depends(require_role("admin", "staff"))])
async def get_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get single feedback with full analysis"""
    feedback = await FeedbackService.get_feedback_by_id(db, feedback_id)
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    # Convert to response
    response_data = {
        "id": feedback.id,
        "patient_name": feedback.patient_name,
        "visit_date": feedback.visit_date,
        "department": feedback.department,
        "doctor_name": feedback.doctor_name,
        "feedback_text": feedback.feedback_text,
        "rating": feedback.rating,
        "status": feedback.status,
        "created_at": feedback.created_at,
        "analysis": None,
        "actions": None
    }
    
    if feedback.analysis:
        response_data["analysis"] = {
            "id": feedback.analysis.id,
            "feedback_id": feedback.analysis.feedback_id,
            "sentiment": feedback.analysis.sentiment,
            "confidence_score": feedback.analysis.confidence_score,
            "emotions": feedback.analysis.emotions,
            "urgency": feedback.analysis.urgency,
            "urgency_reason": feedback.analysis.urgency_reason,
            "urgency_flags": feedback.analysis.urgency_flags,
            "primary_category": feedback.analysis.primary_category,
            "subcategories": feedback.analysis.subcategories,
            "medical_concerns": feedback.analysis.medical_concerns,
            "actionable_insights": feedback.analysis.actionable_insights,
            "key_points": feedback.analysis.key_points
        }
    
    if feedback.actions:
        response_data["actions"] = [
            {
                "id": action.id,
                "status": action.status,
                "staff_note": action.staff_note,
                "assigned_department": action.assigned_department,
                "created_at": action.created_at.isoformat() if action.created_at else None
            }
            for action in feedback.actions
        ]
    
    return response_data


@router.post("/{feedback_id}/update", response_model=FeedbackResponse, dependencies=[Depends(require_role("admin", "staff"))])
async def update_feedback(
    feedback_id: int,
    update_data: FeedbackUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update feedback status and add staff notes"""
    feedback = await FeedbackService.update_feedback_status(
        db=db,
        feedback_id=feedback_id,
        status=update_data.status,
        staff_note=update_data.staff_note,
        assigned_department=update_data.assigned_department
    )
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return feedback

