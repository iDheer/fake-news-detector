"""
Reddit service for retrieving and analyzing content from Reddit
"""
import praw
import asyncio
import logging
from typing import List, Dict, Any
from ..utils.config import (
    REDDIT_CLIENT_ID, 
    REDDIT_CLIENT_SECRET,
    REDDIT_USERNAME,
    REDDIT_USER_AGENT
)

logger = logging.getLogger(__name__)

class RedditService:
    """Service for interacting with Reddit API"""
    
    def __init__(self):
        """Initialize the Reddit client using API credentials"""
        self.client = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=REDDIT_USERNAME,
            user_agent=REDDIT_USER_AGENT,
            check_for_async=False
        )
        logger.info("Reddit client initialized successfully")
    
    async def search_reddit(self, query: str, limit: int = 20) -> List[Dict[Any, Any]]:
        """
        Search Reddit for posts matching the given query
        
        Args:
            query: Search term
            limit: Maximum number of results to return
            
        Returns:
            List of dictionaries containing post information
        """
        try:
            # Using a thread pool to run synchronous Reddit API calls
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                lambda: list(self.client.subreddit("all").search(query, limit=limit))
            )
            
            # Format the results
            formatted_results = []
            for post in results:
                formatted_results.append({
                    "title": post.title,
                    "author": str(post.author),
                    "subreddit": post.subreddit.display_name,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "url": post.url,
                    "permalink": f"https://www.reddit.com{post.permalink}",
                    "created_utc": post.created_utc,
                    "selftext": post.selftext[:1000] if hasattr(post, 'selftext') else "",
                    "is_self": post.is_self if hasattr(post, 'is_self') else False
                })
            
            logger.info(f"Retrieved {len(formatted_results)} results from Reddit for '{query}'")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error retrieving Reddit search results: {e}")
            return []
    
    async def get_post_comments(self, post_id: str, limit: int = 20) -> List[Dict[Any, Any]]:
        """
        Get comments for a specific Reddit post
        
        Args:
            post_id: The ID of the Reddit post
            limit: Maximum number of comments to return
            
        Returns:
            List of dictionaries containing comment information
        """
        try:
            # Using a thread pool for synchronous Reddit API call
            loop = asyncio.get_event_loop()
            submission = await loop.run_in_executor(
                None,
                lambda: self.client.submission(id=post_id)
            )
            
            # Get top-level comments
            submission.comment_sort = "top"
            submission.comment_limit = limit
            
            # Ensure comments are loaded
            await loop.run_in_executor(None, lambda: submission.comments.replace_more(limit=0))
            
            comments = []
            for comment in submission.comments[:limit]:
                comments.append({
                    "author": str(comment.author),
                    "body": comment.body,
                    "score": comment.score,
                    "created_utc": comment.created_utc
                })
            
            logger.info(f"Retrieved {len(comments)} comments for post {post_id}")
            return comments
            
        except Exception as e:
            logger.error(f"Error retrieving comments for post {post_id}: {e}")
            return []
        
    async def analyze_credibility(self, query: str) -> Dict[str, Any]:
        """
        Analyze the credibility of news based on Reddit discussions
        
        Args:
            query: The news headline or topic to analyze
            
        Returns:
            Dictionary containing credibility analysis results
        """
        results = await self.search_reddit(query)
        
        if not results:
            return {
                "reddit_results": False,
                "discussion_count": 0,
                "top_sources": [],
                "sentiment_summary": "No Reddit discussions found"
            }
        
        # Calculate metrics
        discussion_count = len(results)
        avg_score = sum(post["score"] for post in results) / max(discussion_count, 1)
        avg_comments = sum(post["num_comments"] for post in results) / max(discussion_count, 1)
        
        # Get top subreddits
        subreddits = {}
        for post in results:
            subreddit = post["subreddit"]
            if subreddit in subreddits:
                subreddits[subreddit] += 1
            else:
                subreddits[subreddit] = 1
        
        top_sources = sorted(
            [{"subreddit": sr, "count": count} for sr, count in subreddits.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]
        
        return {
            "reddit_results": True,
            "discussion_count": discussion_count,
            "average_score": avg_score,
            "average_comments": avg_comments,
            "top_sources": top_sources,
            "sample_posts": [
                {
                    "title": post["title"],
                    "subreddit": post["subreddit"],
                    "score": post["score"],
                    "comments": post["num_comments"],
                    "url": post["permalink"]
                }
                for post in sorted(results, key=lambda x: x["score"], reverse=True)[:3]
            ]
        }
