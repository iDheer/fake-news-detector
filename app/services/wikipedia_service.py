"""
Wikipedia service for retrieving and analyzing content from Wikipedia
"""
import wikipedia
import logging
import asyncio
import time
from typing import List, Dict, Any, Optional
from ..utils.config import WIKIPEDIA_LANGUAGE, MAX_WIKIPEDIA_RETRIES, WIKIPEDIA_ROBUST

logger = logging.getLogger(__name__)

class WikipediaService:
    """Service for interacting with Wikipedia API"""
    
    def __init__(self):
        """Initialize the Wikipedia client"""
        wikipedia.set_lang(WIKIPEDIA_LANGUAGE)
        logger.info(f"Wikipedia service initialized with language: {WIKIPEDIA_LANGUAGE}")
    
    async def search_wikipedia(self, query: str, max_results: int = 5) -> List[str]:
        """
        Search Wikipedia for articles matching the query
        
        Args:
            query: Search term
            max_results: Maximum number of results to return
            
        Returns:
            List of article titles
        """
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: wikipedia.search(query, results=max_results)
            )
            logger.info(f"Wikipedia search for '{query}' returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
            return []
    
    async def get_article_content(self, title: str, sentences: int = 5) -> Optional[Dict[str, Any]]:
        """
        Get summary and content of a Wikipedia article
        
        Args:
            title: The title of the Wikipedia article
            sentences: Number of sentences for the summary
            
        Returns:
            Dictionary with article summary and content
        """
        retry_count = 0
        while retry_count < MAX_WIKIPEDIA_RETRIES:
            try:
                loop = asyncio.get_event_loop()
                page = await loop.run_in_executor(
                    None,
                    lambda: wikipedia.page(title)
                )
                
                summary = await loop.run_in_executor(
                    None,
                    lambda: wikipedia.summary(title, sentences=sentences)
                )
                
                return {
                    "title": page.title,
                    "summary": summary,
                    "content": page.content,
                    "url": page.url,
                    "last_edited": page.revision_id
                }
            
            except wikipedia.DisambiguationError as e:
                # If disambiguation error, try with the first option
                if WIKIPEDIA_ROBUST and e.options:
                    logger.info(f"Disambiguation for '{title}', trying '{e.options[0]}'")
                    title = e.options[0]
                else:
                    logger.warning(f"Wikipedia disambiguation error for '{title}'")
                    return None
                
            except wikipedia.PageError:
                logger.warning(f"Wikipedia page not found for '{title}'")
                return None
                
            except Exception as e:
                logger.error(f"Error retrieving Wikipedia article '{title}': {e}")
                retry_count += 1
                if retry_count < MAX_WIKIPEDIA_RETRIES:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    return None
        
        return None
    
    async def find_relevant_articles(self, query: str) -> List[Dict[str, Any]]:
        """
        Find and retrieve relevant Wikipedia articles for fact-checking
        
        Args:
            query: The news headline or topic to analyze
            
        Returns:
            List of relevant articles with summary and content
        """
        article_titles = await self.search_wikipedia(query)
        articles = []
        
        for title in article_titles:
            article = await self.get_article_content(title)
            if article:
                articles.append(article)
        
        logger.info(f"Found {len(articles)} relevant Wikipedia articles for '{query}'")
        return articles
