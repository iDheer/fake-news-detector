"""
Tests for the AI analysis service
"""
import pytest
import sys
from pathlib import Path
import os

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.ai_service import AIAnalysisService


def test_ai_service_initialization():
    """Test initialization of AI service"""
    ai_service = AIAnalysisService()
    assert ai_service is not None
    assert hasattr(ai_service, 'device')


@pytest.mark.asyncio
async def test_sentiment_analysis():
    """Test sentiment analysis functionality"""
    ai_service = AIAnalysisService()
    
    # Check if sentiment analyzer was initialized
    if ai_service.sentiment_analyzer:
        # Test positive sentiment
        positive_result = await ai_service.analyze_sentiment("This is wonderful news and everyone is happy about it.")
        assert "sentiment" in positive_result
        assert positive_result["sentiment"] in ["positive", "neutral", "negative"]
        assert "score" in positive_result
        
        # Test negative sentiment
        negative_result = await ai_service.analyze_sentiment("This is terrible news and everyone is upset about it.")
        assert "sentiment" in negative_result
        assert negative_result["sentiment"] in ["positive", "neutral", "negative"]
        assert "score" in negative_result
    else:
        pytest.skip("Sentiment analyzer not initialized, skipping test")


@pytest.mark.asyncio
async def test_factuality_classification():
    """Test factuality classification functionality"""
    ai_service = AIAnalysisService()
    
    # Check if fact model was initialized
    if ai_service.fact_model and ai_service.tokenizer:
        result = await ai_service.classify_factuality(
            "Python is a programming language.", 
            "Python is a high-level, interpreted programming language known for its readability."
        )
        assert "prediction" in result
        assert result["prediction"] in ["contradiction", "neutral", "entailment"]
    else:
        pytest.skip("Factuality classifier not initialized, skipping test")
