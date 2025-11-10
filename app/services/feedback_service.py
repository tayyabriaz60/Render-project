"""
Business logic service for feedback and actions
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload

from app.models.feedback import Feedback
from app.models.analysis import Analysis
from app.models.actions import Action
from app.services.gemini_service import gemini_service
from app.utils.helpers import is_critical_urgency, format_datetime


class FeedbackService:
    """Service for feedback business logic"""
    
    @staticmethod
    async def create_feedback(
        db: AsyncSession,
        patient_name: Optional[str],
        visit_date: datetime,
        department: str,
        doctor_name: Optional[str],
        feedback_text: str,
        rating: int
    ) -> Feedback:
        """Create a new feedback entry"""
        feedback = Feedback(
            patient_name=patient_name,
            visit_date=visit_date,
            department=department,
            doctor_name=doctor_name,
            feedback_text=feedback_text,
            rating=rating,
            status="pending_analysis"
        )
        
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        
        return feedback
    
    @staticmethod
    async def get_feedback_by_id(
        db: AsyncSession,
        feedback_id: int
    ) -> Optional[Feedback]:
        """Get feedback by ID with analysis and actions"""
        result = await db.execute(
            select(Feedback)
            .options(selectinload(Feedback.analysis), selectinload(Feedback.actions))
            .where(Feedback.id == feedback_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_feedback(
        db: AsyncSession,
        department: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        priority: Optional[str] = None,
        sentiment: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Feedback], int]:
        """Get all feedback with filters"""
        
        # Build query
        query = select(Feedback)
        count_query = select(func.count(Feedback.id))
        
        conditions = []
        
        if department:
            conditions.append(Feedback.department == department)
        
        if start_date:
            conditions.append(Feedback.visit_date >= start_date)
        
        if end_date:
            conditions.append(Feedback.visit_date <= end_date)
        
        if status:
            conditions.append(Feedback.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # Always load analysis relationship for easier access
        query = query.options(selectinload(Feedback.analysis))
        
        # Order by created_at desc
        query = query.order_by(Feedback.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        feedbacks = result.scalars().all()
        
        # Apply post-query filters
        filtered_feedbacks = []
        for feedback in feedbacks:
            if priority and feedback.analysis:
                if feedback.analysis.urgency != priority:
                    continue
            
            if sentiment and feedback.analysis:
                if feedback.analysis.sentiment != sentiment:
                    continue
            
            if category and feedback.analysis:
                if (feedback.analysis.primary_category != category and 
                    category not in (feedback.analysis.subcategories or [])):
                    continue
            
            filtered_feedbacks.append(feedback)
        
        # Recalculate total if filters were applied
        if priority or sentiment or category:
            total = len(filtered_feedbacks)
        
        return filtered_feedbacks, total
    
    @staticmethod
    async def analyze_feedback_async(
        db: AsyncSession,
        feedback_id: int
    ) -> Optional[Analysis]:
        """
        Analyze feedback using Gemini AI (async background task)
        """
        # Get feedback
        feedback = await FeedbackService.get_feedback_by_id(db, feedback_id)
        if not feedback:
            return None
        
        # Check if already analyzed
        if feedback.analysis:
            return feedback.analysis
        
        # Call Gemini service
        analysis_result = await gemini_service.analyze_feedback_with_retry(
            feedback_text=feedback.feedback_text,
            department=feedback.department,
            doctor_name=feedback.doctor_name,
            visit_date=format_datetime(feedback.visit_date),
            rating=feedback.rating
        )
        
        # Check for errors
        if "error" in analysis_result:
            # Store error in analysis or handle gracefully
            error_msg = analysis_result.get('error', 'Unknown error')
            print(f"❌ Analysis error for feedback {feedback_id}: {error_msg}")
            print(f"   Full error details: {analysis_result}")
            return None
        
        # Log successful analysis
        print(f"✅ Analysis completed for feedback {feedback_id}")
        print(f"   Sentiment: {analysis_result.get('sentiment')}, Urgency: {analysis_result.get('urgency')}")
        
        # Create analysis record
        analysis = Analysis(
            feedback_id=feedback_id,
            sentiment=analysis_result.get("sentiment", "neutral"),
            confidence_score=analysis_result.get("confidence_score", 0.5),
            emotions=analysis_result.get("emotions", []),
            urgency=analysis_result.get("urgency", "low"),
            urgency_reason=analysis_result.get("urgency_reason"),
            urgency_flags=analysis_result.get("urgency_flags", []),
            primary_category=analysis_result.get("primary_category"),
            subcategories=analysis_result.get("subcategories", []),
            medical_concerns=analysis_result.get("medical_concerns"),
            actionable_insights=analysis_result.get("actionable_insights"),
            key_points=analysis_result.get("key_points", [])
        )
        
        db.add(analysis)
        feedback.status = "reviewed"
        await db.commit()
        await db.refresh(analysis)
        
        return analysis
    
    @staticmethod
    async def update_feedback_status(
        db: AsyncSession,
        feedback_id: int,
        status: str,
        staff_note: Optional[str] = None,
        assigned_department: Optional[str] = None
    ) -> Optional[Feedback]:
        """Update feedback status and create action record"""
        feedback = await FeedbackService.get_feedback_by_id(db, feedback_id)
        if not feedback:
            return None
        
        # Update feedback status
        feedback.status = status
        
        # Create action record
        action = Action(
            feedback_id=feedback_id,
            status=status,
            staff_note=staff_note,
            assigned_department=assigned_department
        )
        
        db.add(action)
        await db.commit()
        await db.refresh(feedback)
        
        return feedback
    
    @staticmethod
    async def get_analytics_summary(db: AsyncSession) -> Dict[str, Any]:
        """Get analytics summary"""
        # Total feedback count
        total_result = await db.execute(select(func.count(Feedback.id)))
        total_feedback = total_result.scalar()
        
        # Sentiment breakdown
        sentiment_query = select(
            Analysis.sentiment,
            func.count(Analysis.id).label("count")
        ).group_by(Analysis.sentiment)
        sentiment_result = await db.execute(sentiment_query)
        sentiment_breakdown = {row.sentiment: row.count for row in sentiment_result}
        
        # Average ratings by department
        rating_query = select(
            Feedback.department,
            func.avg(Feedback.rating).label("avg_rating"),
            func.count(Feedback.id).label("count")
        ).group_by(Feedback.department)
        rating_result = await db.execute(rating_query)
        department_ratings = [
            {
                "department": row.department,
                "average_rating": float(row.avg_rating),
                "feedback_count": row.count
            }
            for row in rating_result
        ]
        
        # Top issues (by category)
        category_query = select(
            Analysis.primary_category,
            func.count(Analysis.id).label("count")
        ).where(Analysis.primary_category.isnot(None)).group_by(Analysis.primary_category).order_by(func.count(Analysis.id).desc()).limit(10)
        category_result = await db.execute(category_query)
        top_issues = [
            {"category": row.primary_category, "count": row.count}
            for row in category_result
        ]
        
        return {
            "total_feedback": total_feedback,
            "sentiment_breakdown": sentiment_breakdown,
            "department_ratings": department_ratings,
            "top_issues": top_issues
        }
    
    @staticmethod
    async def get_analytics_trends(
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics trends"""
        from datetime import timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Sentiment trends over time
        sentiment_trends_query = select(
            func.date(Feedback.created_at).label("date"),
            Analysis.sentiment,
            func.count(Analysis.id).label("count")
        ).join(Analysis).where(
            Feedback.created_at >= start_date
        ).group_by(
            func.date(Feedback.created_at),
            Analysis.sentiment
        ).order_by(func.date(Feedback.created_at))
        
        sentiment_result = await db.execute(sentiment_trends_query)
        sentiment_trends = {}
        for row in sentiment_result:
            date_str = str(row.date)
            if date_str not in sentiment_trends:
                sentiment_trends[date_str] = {}
            sentiment_trends[date_str][row.sentiment] = row.count
        
        # Category trends
        category_trends_query = select(
            func.date(Feedback.created_at).label("date"),
            Analysis.primary_category,
            func.count(Analysis.id).label("count")
        ).join(Analysis).where(
            Feedback.created_at >= start_date,
            Analysis.primary_category.isnot(None)
        ).group_by(
            func.date(Feedback.created_at),
            Analysis.primary_category
        ).order_by(func.date(Feedback.created_at))
        
        category_result = await db.execute(category_trends_query)
        category_trends = {}
        for row in category_result:
            date_str = str(row.date)
            if date_str not in category_trends:
                category_trends[date_str] = {}
            category_trends[date_str][row.primary_category] = row.count
        
        # Department performance
        dept_performance_query = select(
            Feedback.department,
            func.avg(Feedback.rating).label("avg_rating"),
            func.count(Feedback.id).label("total_feedback"),
            func.sum(case((Analysis.urgency == "critical", 1), else_=0)).label("critical_count")
        ).outerjoin(Analysis).where(
            Feedback.created_at >= start_date
        ).group_by(Feedback.department)
        
        dept_result = await db.execute(dept_performance_query)
        department_performance = [
            {
                "department": row.department,
                "average_rating": float(row.avg_rating) if row.avg_rating else 0,
                "total_feedback": row.total_feedback,
                "critical_feedback_count": row.critical_count or 0
            }
            for row in dept_result
        ]
        
        return {
            "sentiment_trends": sentiment_trends,
            "category_trends": category_trends,
            "department_performance": department_performance
        }

