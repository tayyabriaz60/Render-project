from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import relationship
from app.db import Base


class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), unique=True, nullable=False)
    
    # Sentiment analysis
    sentiment = Column(String(50), nullable=False)  # positive/negative/neutral/mixed
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Emotions (stored as JSON array)
    emotions = Column(JSON, nullable=True)  # ["angry", "grateful", "worried", "frustrated", "satisfied"]
    
    # Urgency
    urgency = Column(String(50), nullable=False)  # critical/high/medium/low
    urgency_reason = Column(Text, nullable=True)
    urgency_flags = Column(JSON, nullable=True)  # ["medical_complications", "severe_pain", "safety_concerns", "harassment"]
    
    # Categories
    primary_category = Column(String(100), nullable=True)
    subcategories = Column(JSON, nullable=True)  # ["Doctor Behavior", "Nursing Staff", "Wait Time", etc.]
    
    # Medical concerns
    medical_concerns = Column(JSON, nullable=True)  # symptoms, complications, side effects, medication issues
    
    # Insights
    actionable_insights = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)  # 2-3 bullet points
    
    # Timestamp
    analyzed_at = Column(String(50), nullable=True)  # ISO format string from Gemini
    
    # Relationship
    feedback = relationship("Feedback", back_populates="analysis")

