from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String(255), nullable=True)
    visit_date = Column(DateTime, nullable=False)
    department = Column(String(100), nullable=False)
    doctor_name = Column(String(255), nullable=True)
    feedback_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    status = Column(String(50), default="pending_analysis")  # pending_analysis, reviewed, in_progress, resolved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    analysis = relationship("Analysis", back_populates="feedback", uselist=False, cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="feedback", cascade="all, delete-orphan")

