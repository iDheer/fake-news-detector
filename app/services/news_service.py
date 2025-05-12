"""
News API service for retrieving and analyzing content from news sources
"""
import requests
import asyncio
import logging
from typing import List, Dict, Any, Optional
from ..utils.config import NEWSAPI_KEY, NEWS_DATA_API_KEY, GNEWS_API_KEY

logger = logging.getLogger(__name__)

class NewsAPIService:
    """Service for interacting with multiple News APIs"""
    
    def __init__(self):
        """Initialize the News API service with available API keys"""
        self.newsapi_key = NEWSAPI_KEY
        self.newsdata_key = NEWS_DATA_API_KEY
        self.gnews_key = GNEWS_API_KEY
        
        self.available_apis = []
        if self.newsapi_key:
            self.available_apis.append("newsapi")
        if self.newsdata_key:
            self.available_apis.append("newsdata")
        if self.gnews_key:
            self.available_apis.append("gnews")
        
        logger.info(f"News API service initialized with {len(self.available_apis)} available APIs")
    
    async def search_newsapi(self, query: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Search NewsAPI for articles matching the query
        
        Args:
            query: Search term
            days: Number of days in the past to search
            
        Returns:
            List of article dictionaries
        """
        if not self.newsapi_key:
            logger.warning("NewsAPI key not available")
            return []
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "sortBy": "relevancy",
                "language": "en",
                "apiKey": self.newsapi_key
            }
            
            async with asyncio.timeout(10):
                response = await asyncio.to_thread(
                    lambda: requests.get(url, params=params)
                )
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                logger.info(f"NewsAPI returned {len(articles)} articles for '{query}'")
                
                # Format the articles
                formatted_articles = []
                for article in articles:
                    formatted_articles.append({
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "source": article.get("source", {}).get("name", "Unknown"),
                        "url": article.get("url", ""),
                        "published_at": article.get("publishedAt", ""),
                        "content": article.get("content", ""),
                        "api_source": "newsapi"
                    })
                
                return formatted_articles
            else:
                logger.error(f"NewsAPI error: {response.status_code}, {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching NewsAPI: {e}")
            return []
    
    async def search_newsdata(self, query: str) -> List[Dict[str, Any]]:
        """
        Search NewsData API for articles matching the query
        
        Args:
            query: Search term
            
        Returns:
            List of article dictionaries
        """
        if not self.newsdata_key:
            logger.warning("NewsData API key not available")
            return []
        
        try:
            url = "https://newsdata.io/api/1/news"
            params = {
                "q": query,
                "language": "en",
                "apikey": self.newsdata_key
            }
            
            async with asyncio.timeout(10):
                response = await asyncio.to_thread(
                    lambda: requests.get(url, params=params)
                )
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("results", [])
                logger.info(f"NewsData API returned {len(articles)} articles for '{query}'")
                
                # Format the articles
                formatted_articles = []
                for article in articles:
                    formatted_articles.append({
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "source": article.get("source_id", "Unknown"),
                        "url": article.get("link", ""),
                        "published_at": article.get("pubDate", ""),
                        "content": article.get("content", ""),
                        "api_source": "newsdata"
                    })
                
                return formatted_articles
            else:
                logger.error(f"NewsData API error: {response.status_code}, {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching NewsData API: {e}")
            return []
    
    async def search_gnews(self, query: str) -> List[Dict[str, Any]]:
        """
        Search GNews API for articles matching the query
        
        Args:
            query: Search term
            
        Returns:
            List of article dictionaries
        """
        if not self.gnews_key:
            logger.warning("GNews API key not available")
            return []
        
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": query,
                "lang": "en",
                "token": self.gnews_key
            }
            
            async with asyncio.timeout(10):
                response = await asyncio.to_thread(
                    lambda: requests.get(url, params=params)
                )
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                logger.info(f"GNews API returned {len(articles)} articles for '{query}'")
                
                # Format the articles
                formatted_articles = []
                for article in articles:
                    formatted_articles.append({
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "source": article.get("source", {}).get("name", "Unknown"),
                        "url": article.get("url", ""),
                        "published_at": article.get("publishedAt", ""),
                        "content": article.get("content", ""),
                        "api_source": "gnews"
                    })
                
                return formatted_articles
            else:
                logger.error(f"GNews API error: {response.status_code}, {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching GNews API: {e}")
            return []
    
    async def search_news(self, query: str) -> Dict[str, Any]:
        """
        Search all available news APIs for articles matching the query
        
        Args:
            query: Search term
            
        Returns:
            Dictionary with combined results from all news APIs
        """
        tasks = []
        
        if "newsapi" in self.available_apis:
            tasks.append(self.search_newsapi(query))
        
        if "newsdata" in self.available_apis:
            tasks.append(self.search_newsdata(query))
        
        if "gnews" in self.available_apis:
            tasks.append(self.search_gnews(query))
        
        results = await asyncio.gather(*tasks)
        
        # Combine all results
        all_articles = []
        for result in results:
            all_articles.extend(result)
        
        # Sort by relevance (if we had relevance scores)
        # For now, just return all articles
        return {
            "articles_count": len(all_articles),
            "sources_count": len(set(article["source"] for article in all_articles)),
            "articles": all_articles[:20]  # Limit to top 20 articles
        }
