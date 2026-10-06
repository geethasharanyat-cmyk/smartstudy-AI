"""
Database models for SmartStudy AI.
Uses SQLAlchemy 2.0+ declarative mappings with SQLite support.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Date,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(120), default="")
    course = Column(String(120), default="")
    year_of_study = Column(String(30), default="")
    preferred_study_hours = Column(Float, default=3.0)
    preferred_study_time = Column(String(60), default="Evening (6:00 PM - 10:00 PM)")
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")
    progress_logs = relationship("ProgressLog", back_populates="user", cascade="all, delete-orphan")
    uploaded_materials = relationship("UploadedMaterial", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(30), default="")
    color = Column(String(20), default="#4F46E5")  # Hex color for UI badges/charts
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="subjects", lazy="joined")
    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan", lazy="selectin")
    materials = relationship("UploadedMaterial", back_populates="subject", lazy="selectin")

    def __repr__(self):
        return f"<Subject {self.name}>"


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    difficulty = Column(String(20), default="Medium")  # Easy, Medium, Hard
    priority = Column(String(20), default="Medium")      # Low, Medium, High
    knowledge_level = Column(String(20), default="Beginner")  # Beginner, Intermediate, Advanced
    status = Column(String(20), default="Not Started")   # Not Started, In Progress, Completed
    estimated_duration_hours = Column(Float, default=1.0)
    exam_date = Column(Date, nullable=True)
    notes = Column(Text, default="")
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    subject = relationship("Subject", back_populates="topics", lazy="joined")
    study_sessions = relationship("StudySession", back_populates="topic", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<Topic {self.name} ({self.difficulty})>"


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    session_date = Column(Date, nullable=False, index=True)
    start_time = Column(String(10), nullable=False)  # e.g., "18:00" or "06:00 PM"
    end_time = Column(String(10), nullable=False)    # e.g., "18:45" or "06:45 PM"
    duration_minutes = Column(Integer, default=45)
    status = Column(String(20), default="Planned")   # Planned, Completed, Missed, Rescheduled
    notes = Column(Text, default="")
    rescheduled_from_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="study_sessions", lazy="joined")
    topic = relationship("Topic", back_populates="study_sessions", lazy="joined")

    def __repr__(self):
        return f"<StudySession {self.session_date} {self.start_time}-{self.end_time} ({self.status})>"


class ProgressLog(Base):
    __tablename__ = "progress_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    log_date = Column(Date, nullable=False, default=date.today, index=True)
    minutes_studied = Column(Integer, default=0)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="progress_logs", lazy="joined")
    topic = relationship("Topic", lazy="joined")

    def __repr__(self):
        return f"<ProgressLog {self.log_date} ({self.minutes_studied}m)>"


class UploadedMaterial(Base):
    __tablename__ = "uploaded_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt, image
    file_size_kb = Column(Float, default=0.0)
    extracted_text = Column(Text, default="")
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="uploaded_materials", lazy="joined")
    subject = relationship("Subject", back_populates="materials", lazy="joined")

    def __repr__(self):
        return f"<UploadedMaterial {self.filename}>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    mode = Column(String(30), default="Simple")  # "Simple", "Teacher", "Exam"
    context_info = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="chat_messages")

    def __repr__(self):
        return f"<ChatMessage {self.role} [{self.mode}] at {self.timestamp}>"
