"""
Fake News Detection Agent to orchestrate detection process
"""
import logging
import asyncio
from typing import Dict, Any, List
import time

from ..services.reddit_service import RedditService
from ..services.wikipedia_service import WikipediaService
from ..services.news_service import NewsAPIService
from ..services.ai_service import AIAnalysisService
from ..models.database import NewsArticle, VerificationSource, get_db

logger = logging.getLogger(__name__)

class FakeNewsAgent:
    """Agent for detecting fake news by orchestrating multiple services"""
    
    def __init__(self):
        """Initialize the fake news detection agent"""
        self.reddit_service = RedditService()
        self.wikipedia_service = WikipediaService()
        self.news_service = NewsAPIService()
        self.ai_service = AIAnalysisService()
        
        logger.info("Fake News Detection Agent initialized")
    
    async def analyze_news(self, title: str, content: str) -> Dict[str, Any]:
        """
        Analyze news article for authenticity
        
        Args:
            title: News article title
            content: News article content
            
        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()
        logger.info(f"Starting analysis for: {title}")
        
        # Create tasks for parallel execution
        tasks = [
            self.reddit_service.analyze_credibility(title),
            self.wikipedia_service.find_relevant_articles(title),
            self.news_service.search_news(title),
            self.ai_service.analyze_sentiment(content)
        ]
        
        # Execute tasks in parallel
        reddit_data, wiki_articles, news_data, sentiment_analysis = await asyncio.gather(*tasks)
        
        # Extract articles from news_data
        news_articles = news_data.get("articles", [])
        
        # Use RAG to analyze news with context from Wikipedia and other news sources
        rag_analysis = await self.ai_service.analyze_news_with_rag(
            title, content, wiki_articles, news_articles
        )
        
        # Calculate verification score
        verification_result = self.calculate_verification_score(
            title, content, reddit_data, wiki_articles, news_data, rag_analysis
        )
        
        # Combine all results
        result = {
            "title": title,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "verification_result": verification_result,
            "reddit_data": reddit_data,
            "wikipedia_articles": [
                {"title": article["title"], "summary": article["summary"]} 
                for article in wiki_articles[:3]
            ],
            "news_data": {
                "articles_count": news_data.get("articles_count", 0),
                "sources_count": news_data.get("sources_count", 0),
                "sample_articles": [
                    {
                        "title": article["title"],
                        "source": article["source"],
                        "url": article["url"]
                    }
                    for article in news_articles[:3]
                ]
            },
            "sentiment_analysis": sentiment_analysis,
            "rag_analysis": rag_analysis,
            "processing_time": round(time.time() - start_time, 2)
        }
        
        logger.info(f"Analysis completed in {result['processing_time']} seconds")
        return result
    
    def calculate_verification_score(
        self,
        title: str,
        content: str,
        reddit_data: Dict[str, Any],
        wiki_articles: List[Dict[str, Any]],
        news_data: Dict[str, Any],
        rag_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate verification score based on all data sources
        
        Args:
            title: News article title
            content: News article content
            reddit_data: Data from Reddit analysis
            wiki_articles: Wikipedia articles data
            news_data: News articles data
            rag_analysis: Results from RAG analysis
            
        Returns:
            Dictionary with verification score and details
        """
        # Initialize scores
        source_credibility = 0
        content_consistency = 0
        fact_verification = 0
        
        # 1. Source Credibility (based on Reddit and news sources)
        reddit_discussion_score = 0
        if reddit_data.get("reddit_results"):
            discussion_count = reddit_data.get("discussion_count", 0)
            if discussion_count > 20:
                reddit_discussion_score = 30  # High discussion
            elif discussion_count > 10:
                reddit_discussion_score = 20  # Medium discussion
            elif discussion_count > 0:
                reddit_discussion_score = 10  # Low discussion
        
        news_sources_score = min(25, news_data.get("sources_count", 0) * 5)
        source_credibility = reddit_discussion_score + news_sources_score
        
        # 2. Content Consistency (based on news article consistency)
        articles_count = news_data.get("articles_count", 0)
        content_consistency = min(30, articles_count * 3)
        
        # 3. Fact Verification (based on RAG analysis and Wikipedia)
        rag_score = 0
        if rag_analysis.get("factual_score"):
            rag_score = min(30, int(rag_analysis.get("factual_score") * 0.3))
        
        wiki_score = min(15, len(wiki_articles) * 5)
        fact_verification = rag_score + wiki_score
        
        # Calculate total score (0-100)
        total_score = source_credibility + content_consistency + fact_verification
        
        # Determine if the news is fake based on the score
        is_fake = total_score < 50 or rag_analysis.get("is_fake", False)
        
        # Confidence level based on various factors
        confidence = min(100, max(50, rag_analysis.get("confidence", 70)))
        
        return {
            "verdict": "FAKE" if is_fake else "REAL",
            "is_fake": is_fake,
            "score": total_score,
            "confidence": confidence,
            "source_credibility": source_credibility,
            "content_consistency": content_consistency,
            "fact_verification": fact_verification
        }
    
    async def save_analysis(self, title: str, content: str, result: Dict[str, Any]) -> int:
        """
        Save analysis result to database
        
        Args:
            title: News article title
            content: News article content
            result: Analysis result
            
        Returns:
            ID of the saved news article
        """
        try:
            # Get verification result
            verification = result["verification_result"]
            
            # Create database session
            db = next(get_db())
            
            # Create news article
            article = NewsArticle(
                title=title,
                content=content,
                fake_probability=100 - verification["score"],
                is_fake=verification["is_fake"],
                verification_method="combined-rag"
            )
            
            # Add to database
            db.add(article)
            db.commit()
            db.refresh(article)
            
            # Save verification sources
            
            # Reddit sources
            if result.get("reddit_data", {}).get("reddit_results"):
                for post in result["reddit_data"].get("sample_posts", []):
                    source = VerificationSource(
                        article_id=article.id,
                        source_type="reddit",
                        source_url=post.get("url", ""),
                        source_text=post.get("title", ""),
                        relevance_score=float(post.get("score", 0)) / 100
                    )
                    db.add(source)
            
            # Wikipedia sources
            for wiki_article in result.get("wikipedia_articles", []):
                source = VerificationSource(
                    article_id=article.id,
                    source_type="wikipedia",
                    source_url="",  # Wikipedia URL not returned in sample articles
                    source_text=wiki_article.get("title", "") + ": " + wiki_article.get("summary", ""),
                    relevance_score=0.8  # Assume high relevance
                )
                db.add(source)
            
            # News API sources
            for article_data in result.get("news_data", {}).get("sample_articles", []):
                source = VerificationSource(
                    article_id=article.id,
                    source_type="news_api",
                    source_url=article_data.get("url", ""),
                    source_text=article_data.get("title", ""),
                    relevance_score=0.7  # Assume medium-high relevance
                )
                db.add(source)
            
            # Commit all sources
            db.commit()
            
            logger.info(f"Analysis saved to database for article ID: {article.id}")
            return article.id
            
        except Exception as e:
            logger.error(f"Error saving analysis to database: {e}")
            return None
