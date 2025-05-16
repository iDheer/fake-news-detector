"""
Fake News Detection Agent to orchestrate detection process
"""
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
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
    
    async def analyze_news(self, title: str, content: str, publication_date_str: str = None) -> Dict[str, Any]:
        """
        Analyze news article for authenticity
        
        Args:
            title: News article title
            content: News article content
            publication_date_str: Optional publication date as string (e.g., YYYY-MM-DD)
            
        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()
        logger.info(f"Starting analysis for: {title}")

        # Determine if news is old or recent
        is_old_news = False
        news_age_days = None
        if publication_date_str:
            try:
                pub_date = datetime.strptime(publication_date_str, "%Y-%m-%d")
                news_age_days = (datetime.now() - pub_date).days
                if news_age_days > 180: # Consider news older than 6 months as "old"
                    is_old_news = True
                logger.info(f"News item is {news_age_days} days old. Classified as {'OLD' if is_old_news else 'RECENT'}.")
            except ValueError:
                logger.warning(f"Invalid publication date format: {publication_date_str}. Assuming recent news.")
        else:
            logger.info("No publication date provided. Assuming recent news.")

        subcategory_analysis = None
        if is_old_news:
            # For old news, first get subcategory classification from HF model
            subcategory_analysis = await self.ai_service.classify_news_subcategories_hf(content)
            logger.info(f"Old news subcategory analysis: {subcategory_analysis}")
            # Prepare subcategory info string for RAG
            subcategory_info_for_rag = f"Primary: {subcategory_analysis.get('primary_subcategory', 'N/A')}, Secondary: {subcategory_analysis.get('secondary_subcategory', 'N/A')}, Confidence: {subcategory_analysis.get('confidence', 'N/A')}"
        else:
            subcategory_info_for_rag = "News classified as recent; no pre-analysis for subcategory performed."
        
        # Create tasks for parallel execution
        tasks = [
            self.reddit_service.analyze_credibility(title),
            self.wikipedia_service.find_relevant_articles(title),
            self.news_service.search_news(title), # This gathers recent articles
            self.ai_service.analyze_sentiment(content)
        ]
        
        # Execute tasks in parallel
        reddit_data, wiki_articles, news_data, sentiment_analysis = await asyncio.gather(*tasks)
        
        # Extract articles from news_data
        news_articles = news_data.get("articles", [])
        
        # Use RAG to analyze news with context from Wikipedia and other news sources
        # Pass subcategory_info_for_rag to the RAG analysis
        rag_analysis = await self.ai_service.analyze_news_with_rag(
            title, content, wiki_articles, news_articles, subcategory_info=subcategory_info_for_rag
        )
        
        # Calculate verification score
        verification_result = self.calculate_verification_score(
            title, content, reddit_data, wiki_articles, news_data, rag_analysis
        )

        # Generate summary
        summary_key_points = f"RAG Analysis Verdict: {rag_analysis.get('verdict', 'N/A')}, Factual Score: {rag_analysis.get('factual_score', 'N/A')}%, Confidence: {rag_analysis.get('confidence', 'N/A')}%. Reddit discussions: {reddit_data.get('discussion_count', 0)}. Related news articles found: {news_data.get('articles_count', 0)}."
        news_summary_obj = await self.ai_service.generate_news_summary(
            title,
            content,
            verification_result["verdict"],
            verification_result["score"],
            summary_key_points
        )
        
        # Combine all results
        result = {
            "title": title,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "publication_date_provided": publication_date_str,
            "news_age_days": news_age_days,
            "is_classified_old": is_old_news,
            "subcategory_analysis": subcategory_analysis, # Will be None for recent news
            "verification_result": verification_result,
            "news_summary": news_summary_obj.get("summary_text", "Summary not available."),
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
        
        # Recalculating with new targets:
        # 1. Source Credibility (max 30)
        reddit_discussion_score = 0
        if reddit_data.get("reddit_results"):
            discussion_count = reddit_data.get("discussion_count", 0)
            if discussion_count > 20:
                reddit_discussion_score = 15
            elif discussion_count > 10:
                reddit_discussion_score = 10
            elif discussion_count > 0:
                reddit_discussion_score = 5
            else:
                reddit_discussion_score = 0
        
        news_sources_score = min(15, news_data.get("sources_count", 0) * 3)
        source_credibility = reddit_discussion_score + news_sources_score # Max 30
        
        # 2. Content Consistency (max 30)
        articles_count = news_data.get("articles_count", 0)
        # More articles suggest consistency, up to a point.
        if articles_count >= 5:
            content_consistency = 30
        elif articles_count >= 3:
            content_consistency = 20
        elif articles_count >= 1:
            content_consistency = 10
        else:
            content_consistency = 0
            
        # 3. Fact Verification (max 40)
        rag_factual_score_from_llm = rag_analysis.get("factual_score", 0) # This is 0-100 from LLM
        rag_is_fake_from_llm = rag_analysis.get("is_fake", False)

        # If LLM directly says it's fake, this is a strong signal.
        # Let rag_score reflect the LLM's confidence in factuality.
        rag_score = int(rag_factual_score_from_llm * 0.3) # Max 30 points from factual_score (0-100 scale)
        
        wiki_related_articles_count = len(wiki_articles)
        if wiki_related_articles_count >= 3:
            wiki_score = 10
        elif wiki_related_articles_count >= 1:
            wiki_score = 5
        else:
            wiki_score = 0
        fact_verification = rag_score + wiki_score # Max 40
        
        # Calculate total score (0-100)
        total_score = source_credibility + content_consistency + fact_verification # Max 30+30+40 = 100
        
        # Determine if the news is fake based on the score and LLM direct output
        # If LLM is very confident it's fake, OR if the total score is very low.
        # Let's make the threshold for total_score lower, e.g., 40.
        # And consider the LLM's direct "is_fake" output more strongly.
        
        is_fake_final = False
        if rag_is_fake_from_llm: # If LLM says it's fake
            if total_score < 60: # And our score isn't strongly contradicting
                is_fake_final = True
        elif total_score < 40: # If LLM doesn't say fake, but our score is very low
            is_fake_final = True
            
        # Confidence level based on various factors
        # If LLM verdict aligns with score, confidence is higher.
        # Use LLM confidence primarily, but adjust if our score is very different.
        llm_confidence = rag_analysis.get("confidence", 70) # 0-100 from LLM
        
        # Adjust confidence based on agreement between score and LLM verdict
        if (is_fake_final and rag_is_fake_from_llm) or (not is_fake_final and not rag_is_fake_from_llm):
            confidence = max(llm_confidence, 75) # Agreement, so at least 75 or LLM's confidence
        elif total_score > 70 and not is_fake_final: # High score, not fake
             confidence = max(total_score, llm_confidence)
        elif total_score < 30 and is_fake_final: # Low score, fake
             confidence = max(100 - total_score, llm_confidence) # Higher confidence in "fake"
        else: # Disagreement or mid-range scores
            confidence = min(llm_confidence, 60) # Lower confidence due to conflicting signals

        confidence = min(100, max(0, int(confidence))) # Ensure it's 0-100
        
        return {
            "verdict": "FAKE" if is_fake_final else "REAL",
            "is_fake": is_fake_final,
            "score": total_score,
            "confidence": confidence,
            "source_credibility": source_credibility,
            "content_consistency": content_consistency,
            "fact_verification": fact_verification,
            "debug_rag_is_fake": rag_is_fake_from_llm, # For debugging
            "debug_rag_factual_score": rag_factual_score_from_llm # For debugging
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
