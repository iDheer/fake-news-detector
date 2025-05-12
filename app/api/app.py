"""
FastAPI backend for the Fake News Detection system
"""
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..agents.fake_news_agent import FakeNewsAgent
from ..models.database import create_tables, get_db, NewsArticle, UserFeedback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Fake News Detection API",
    description="API for detecting fake news using AI and multiple data sources",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables
create_tables()

# Initialize fake news detection agent
fake_news_agent = FakeNewsAgent()

# Request and response models
class NewsRequest(BaseModel):
    """Model for news verification request"""
    title: str = Field(..., min_length=3, max_length=300)
    content: str = Field(..., min_length=10, max_length=5000)


class VerificationResponse(BaseModel):
    """Model for news verification response"""
    article_id: Optional[int] = None
    verdict: str
    is_fake: bool
    score: int
    confidence: int
    processing_time: float
    details: Dict[str, Any]


class FeedbackRequest(BaseModel):
    """Model for user feedback on verification results"""
    article_id: int
    is_correct: bool
    feedback_text: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint that returns a welcome message"""
    return {
        "message": "Welcome to the Fake News Detection API",
        "version": "1.0.0",
        "status": "online"
    }


@app.post("/verify", response_model=VerificationResponse)
async def verify_news(
    news: NewsRequest, 
    background_tasks: BackgroundTasks
):
    """
    Verify if a news article is fake or not
    
    Args:
        news: News article to verify
        background_tasks: FastAPI background tasks
        
    Returns:
        Verification result
    """
    try:
        # Analyze the news
        result = await fake_news_agent.analyze_news(news.title, news.content)
        
        # Save the analysis in background
        background_tasks.add_task(
            fake_news_agent.save_analysis,
            news.title,
            news.content,
            result
        )
        
        # Extract verification result
        verification = result["verification_result"]
        
        return VerificationResponse(
            article_id=None,  # Will be set by background task
            verdict=verification["verdict"],
            is_fake=verification["is_fake"],
            score=verification["score"],
            confidence=verification["confidence"],
            processing_time=result["processing_time"],
            details=result
        )
    
    except Exception as e:
        logger.error(f"Error verifying news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Submit user feedback on verification results
    
    Args:
        feedback: User feedback
        db: Database session
        
    Returns:
        Confirmation message
    """
    try:
        # Check if article exists
        article = db.query(NewsArticle).filter(NewsArticle.id == feedback.article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Create user feedback
        user_feedback = UserFeedback(
            article_id=feedback.article_id,
            is_correct=feedback.is_correct,
            feedback_text=feedback.feedback_text
        )
        
        # Add to database
        db.add(user_feedback)
        db.commit()
        
        return {"message": "Feedback submitted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_history(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get history of verified news articles
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
        db: Database session
        
    Returns:
        List of verified news articles
    """
    try:
        articles = db.query(NewsArticle).order_by(
            NewsArticle.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "total": db.query(NewsArticle).count(),
            "offset": offset,
            "limit": limit,
            "articles": [
                {
                    "id": article.id,
                    "title": article.title,
                    "content": article.content[:100] + "..." if len(article.content) > 100 else article.content,
                    "is_fake": article.is_fake,
                    "fake_probability": article.fake_probability,
                    "created_at": article.created_at
                }
                for article in articles
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
