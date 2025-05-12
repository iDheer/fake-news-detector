"""
Tests for the Wikipedia service
"""
import pytest
import sys
from pathlib import Path
import asyncio

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.wikipedia_service import WikipediaService


@pytest.mark.asyncio
async def test_wikipedia_service_initialization():
    """Test initialization of Wikipedia service"""
    wiki_service = WikipediaService()
    assert wiki_service is not None


@pytest.mark.asyncio
async def test_wikipedia_search():
    """Test Wikipedia search functionality"""
    wiki_service = WikipediaService()
    results = await wiki_service.search_wikipedia("Python programming")
    
    assert isinstance(results, list)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_get_article_content():
    """Test retrieving Wikipedia article content"""
    wiki_service = WikipediaService()
    article = await wiki_service.get_article_content("Python (programming language)")
    
    assert isinstance(article, dict)
    assert "title" in article
    assert "summary" in article
    assert "content" in article
    assert "url" in article
    
    # Check that the content is related to Python programming
    assert "programming" in article["content"].lower()


@pytest.mark.asyncio
async def test_find_relevant_articles():
    """Test finding relevant Wikipedia articles"""
    wiki_service = WikipediaService()
    articles = await wiki_service.find_relevant_articles("Python programming language")
    
    assert isinstance(articles, list)
    assert len(articles) > 0
