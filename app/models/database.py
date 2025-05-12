"""
Database models for the fake news detection system
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime
from pathlib import Path
from ..utils.config import DATABASE_URL

# Create the database directory if it doesn't exist
db_path = Path(__file__).resolve().parent.parent / "data"
db_path.mkdir(exist_ok=True)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for our models
Base = declarative_base()

class NewsArticle(Base):
    """Model for storing news articles and their verification results"""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    fake_probability = Column(Float, nullable=True)
    is_fake = Column(Boolean, nullable=True)
    verification_method = Column(String(50), nullable=True)
    
    # Relationship with verification sources
    verification_sources = relationship("VerificationSource", back_populates="article")
    
    # Relationship with user feedback
    feedback = relationship("UserFeedback", back_populates="article")


class VerificationSource(Base):
    """Model for storing verification sources for news articles"""
    __tablename__ = "verification_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"))
    source_type = Column(String(50))  # e.g., "reddit", "wikipedia", "news_api"
    source_url = Column(String(500), nullable=True)
    source_text = Column(Text, nullable=True)
    relevance_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship with news article
    article = relationship("NewsArticle", back_populates="verification_sources")


class UserFeedback(Base):
    """Model for storing user feedback on verification results"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"))
    is_correct = Column(Boolean, nullable=False)
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship with news article
    article = relationship("NewsArticle", back_populates="feedback")


# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
