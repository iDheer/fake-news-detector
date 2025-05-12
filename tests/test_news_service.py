"""
Tests for the news service
"""
import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.news_service import NewsAPIService

@pytest.mark.asyncio
async def test_news_service_initialization():
    """Test initialization of news service"""
    news_service = NewsAPIService()
    assert news_service is not None
    assert isinstance(news_service.available_apis, list)

@pytest.mark.asyncio
async def test_news_search_with_empty_keys():
    """Test news search with empty API keys"""
    # Temporarily clear API keys
    news_api_key = os.environ.get("NEWSAPI_KEY")
    news_data_key = os.environ.get("NEWS_DATA_API_KEY")
    gnews_key = os.environ.get("GNEWS_API_KEY")
    
    try:
        os.environ["NEWSAPI_KEY"] = ""
        os.environ["NEWS_DATA_API_KEY"] = ""
        os.environ["GNEWS_API_KEY"] = ""
        
        news_service = NewsAPIService()
        result = await news_service.search_news("test")
        
        assert result["articles_count"] == 0
        assert result["sources_count"] == 0
        assert result["articles"] == []
    
    finally:
        # Restore API keys
        if news_api_key:
            os.environ["NEWSAPI_KEY"] = news_api_key
        if news_data_key:
            os.environ["NEWS_DATA_API_KEY"] = news_data_key
        if gnews_key:
            os.environ["GNEWS_API_KEY"] = gnews_key
