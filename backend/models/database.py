from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from sqlalchemy.sql import func
import os

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    prompt_type = Column(String, default="indirect")
    runs_per_model = Column(Integer, default=5)
    conversation_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    turns = relationship("ConversationTurn", back_populates="conversation", cascade="all, delete-orphan")


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    turn_number = Column(Integer)
    user_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="turns")
    model_responses = relationship("ModelResponse", back_populates="turn", cascade="all, delete-orphan")


class ModelResponse(Base):
    __tablename__ = "model_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_turn_id = Column(Integer, ForeignKey("conversation_turns.id"))
    model_name = Column(String, index=True)
    response_text = Column(Text)
    response_time = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    scored = Column(Boolean, default=False, index=True)
    score_data = Column(JSON, nullable=True)
    weighted_score = Column(Float, nullable=True, index=True)
    
    # Relationships
    turn = relationship("ConversationTurn", back_populates="model_responses")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to conversations
    conversations = relationship("Conversation", back_populates="user")


# ✅ FIX: Use absolute path to root database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "medical_llm_benchmark.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

print(f"📍 Database location: {DATABASE_PATH}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()