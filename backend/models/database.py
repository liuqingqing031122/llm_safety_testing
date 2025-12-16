from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    prompt_type = Column(String, default="indirect")  # direct, indirect, conversational
    runs_per_model = Column(Integer, default=25)  # ✨ 改为 3（原来是 25）
    
    # Relationships
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
    
    # ✨ 添加评分字段
    scored = Column(Boolean, default=False, index=True)
    score_data = Column(JSON, nullable=True)  # 存储完整评分结果 {"raw_scores": {...}, "weighted_score": 95.5}
    weighted_score = Column(Float, nullable=True, index=True)  # 加权总分，用于快速查询
    
    # Relationships
    turn = relationship("ConversationTurn", back_populates="model_responses")


# Database setup
DATABASE_URL = "sqlite:///./medical_llm_benchmark.db"
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