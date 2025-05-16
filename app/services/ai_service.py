"""
AI service for analyzing news content and detecting fake news
"""
import logging
import asyncio
from typing import Dict, Any, List, Tuple
import torch
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

# Import both OpenAI and Gemini
from langchain_openai import ChatOpenAI, OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI  
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

from ..utils.config import OPENAI_API_KEY, GOOGLE_API_KEY, AI_PROVIDER, USE_GPU

logger = logging.getLogger(__name__)

class AIAnalysisService:
    """Service for AI-powered news analysis and fake news detection"""
    
    def __init__(self):
        """Initialize the AI analysis service"""
        self.ai_provider = AI_PROVIDER
        self.openai_available = self.ai_provider == "openai" and bool(OPENAI_API_KEY)
        self.gemini_available = self.ai_provider == "gemini" and bool(GOOGLE_API_KEY)
        self.device = "cuda" if USE_GPU and torch.cuda.is_available() else "cpu"
        
        # Initialize models
        self.initialize_models()
        
        logger.info(f"AI Analysis Service initialized with device: {self.device}")
        logger.info(f"AI provider: {self.ai_provider}")
        logger.info(f"OpenAI API available: {self.openai_available}")
        logger.info(f"Gemini API available: {self.gemini_available}")
    
    def initialize_models(self):
        """Initialize AI models for analysis"""
        try:
            # For sentiment analysis
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=0 if self.device == "cuda" else -1
            )
            
            # For news classification
            model_name = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.fact_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            if self.device == "cuda":
                self.fact_model = self.fact_model.to(self.device)
                
            # Define the prompt template (used by both OpenAI and Gemini)
            self.fact_check_template = PromptTemplate(
                input_variables=["news_title", "news_content", "sources", "subcategory_info"],
                template="""
                As an AI fact-checker, analyze the following news article for credibility.
                
                ARTICLE TITLE: {news_title}
                
                ARTICLE CONTENT: {news_content}
                
                ADDITIONAL CONTEXT:
                {sources}

                PRE-ANALYSIS (if available, from a specialized model):
                {subcategory_info}
                
                Please provide:
                1. A factual accuracy score (0-100%)
                2. Identification of any misleading claims
                3. Assessment of source credibility (considering both provided sources and your general knowledge)
                4. Overall verdict (REAL NEWS or FAKE/MISLEADING NEWS)
                5. Confidence in your assessment (0-100%)
                
                Format your response as a structured analysis with clear headings.
                """
            )

            self.summarization_template = PromptTemplate(
                input_variables=["news_title", "news_content", "verification_verdict", "verification_score", "key_points"],
                template="""
                Based on the following news article and its verification analysis, provide a concise summary.

                ARTICLE TITLE: {news_title}
                ARTICLE CONTENT:
                {news_content}

                VERIFICATION RESULT:
                Verdict: {verification_verdict}
                Score: {verification_score}/100
                Key Supporting Points/Reasons: {key_points}

                Your task is to:
                1. Generate a neutral, brief summary of the news article itself (2-3 sentences).
                2. Briefly state the overall verification outcome and the main reason(s) for it.
                Ensure the summary is objective and clearly distinguishes between the news content and its assessment.
                """
            )
              # Initialize OpenAI if configured and available
            if self.openai_available:
                try:
                    self.llm = ChatOpenAI(
                        api_key=OPENAI_API_KEY,
                        temperature=0.1,
                        model="gpt-3.5-turbo"
                    )
                    
                    self.embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
                    
                    # Create a chain using the newer API (replacing deprecated LLMChain)
                    self.fact_check_chain = self.fact_check_template | self.llm
                    self.summarization_chain = self.summarization_template | self.llm
                    logger.info("OpenAI LLM initialized successfully")
                except Exception as e:
                    logger.error(f"Error initializing OpenAI: {e}")
                    logger.warning("Falling back to local models only - LLM features will be limited")
                    self.openai_available = False
                    
            # Initialize Gemini if configured and available
            elif self.gemini_available:
                try:
                    self.llm = ChatGoogleGenerativeAI(
                        google_api_key=GOOGLE_API_KEY,
                        temperature=0.1,
                        model="gemini-1.5-flash"
                    )
                    
                    self.embeddings = GoogleGenerativeAIEmbeddings(
                        google_api_key=GOOGLE_API_KEY,
                        model="models/embedding-001"
                    )
                      # Create a chain using the newer API (replacing deprecated LLMChain)
                    self.fact_check_chain = self.fact_check_template | self.llm
                    self.summarization_chain = self.summarization_template | self.llm
                    logger.info("Gemini LLM initialized successfully")
                except Exception as e:
                    logger.error(f"Error initializing Gemini: {e}")
                    logger.warning("Falling back to local models only - LLM features will be limited")
                    self.gemini_available = False
            
            logger.info("AI models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")
            self.sentiment_analyzer = None
            self.fact_model = None
            self.tokenizer = None
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not self.sentiment_analyzer:
            return {"error": "Sentiment analyzer not initialized"}
        
        try:
            # Limit text length to avoid errors
            truncated_text = text[:512]
            
            result = await asyncio.to_thread(
                lambda: self.sentiment_analyzer(truncated_text)[0]
            )
            
            sentiment = result["label"].lower()
            score = result["score"]
            
            return {
                "sentiment": sentiment,
                "score": score,
                "analysis": f"{sentiment.capitalize()} sentiment with {score:.2f} confidence"
            }
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"error": str(e)}
            
    async def classify_factuality(self, claim: str, evidence: str) -> Dict[str, Any]:
        """
        Classify if a claim is supported by evidence
        
        Args:
            claim: The claim to check
            evidence: Evidence text
            
        Returns:
            Dictionary with factuality classification results
        """
        if not self.fact_model or not self.tokenizer:
            return {"error": "Factuality classifier not initialized"}
        
        try:
            # Prepare input for the model
            input_text = f"claim: {claim} context: {evidence[:1000]}"
            
            # Tokenize and prepare for inference
            tokenized_input = await asyncio.to_thread(
                lambda: self.tokenizer(
                    input_text,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                )
            )
            
            # Move to device if using GPU
            if self.device == "cuda":
                tokenized_input = {k: v.to(self.device) for k, v in tokenized_input.items()}
            
            # Get model prediction
            with torch.no_grad():
                output = await asyncio.to_thread(
                    lambda: self.fact_model(**tokenized_input)
                )
            
            # Process results
            scores = torch.nn.functional.softmax(output.logits, dim=1).cpu().numpy()[0]
            predictions = [
                {"label": "contradiction", "score": float(scores[0])},
                {"label": "neutral", "score": float(scores[1])},
                {"label": "entailment", "score": float(scores[2])}
            ]
            
            # Sort by score
            predictions = sorted(predictions, key=lambda x: x["score"], reverse=True)
            
            return {
                "prediction": predictions[0]["label"],
                "score": predictions[0]["score"],
                "detailed_scores": predictions
            }
        
        except Exception as e:
            logger.error(f"Error classifying factuality: {e}")
            return {"error": str(e)}
            
    async def create_document_embeddings(self, texts: List[str]) -> Any:
        """
        Create embeddings for text documents
        
        Args:
            texts: List of text documents
            
        Returns:
            FAISS vector store with document embeddings
        """
        # Check if either OpenAI or Gemini is available
        if not (self.openai_available or self.gemini_available):
            return None
        
        try:
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            docs = []
            
            for text in texts:
                if not text:
                    continue
                    
                chunks = text_splitter.split_text(text)
                docs.extend(chunks)
            
            # Create vector store using the selected embedding provider
            vectorstore = await asyncio.to_thread(
                lambda: FAISS.from_texts(docs, self.embeddings)
            )
            
            return vectorstore
        
        except Exception as e:
            logger.error(f"Error creating document embeddings: {e}")
            return None
            
    async def analyze_news_with_rag(
        self, 
        title: str, 
        content: str, 
        wiki_data: List[Dict[str, Any]], 
        news_data: List[Dict[str, Any]],
        subcategory_info: str = "Not available" # New parameter
    ) -> Dict[str, Any]:
        """
        Analyze news using Retrieval Augmented Generation
        
        Args:
            title: News article title
            content: News article content
            wiki_data: Wikipedia articles data
            news_data: News articles data
            subcategory_info: Optional information from a subcategory classification model.
            
        Returns:
            Dictionary with analysis results
        """
        # Check if either OpenAI or Gemini is available
        if not (self.openai_available or self.gemini_available) or not self.fact_check_chain:
            return {"error": "LLM (OpenAI or Gemini) API is not available or chain not initialized"}
        
        try:
            # Prepare reference sources text
            sources_text = ""
            
            # Add Wikipedia data
            for i, wiki in enumerate(wiki_data[:3]):
                sources_text += f"\nWIKIPEDIA SOURCE {i+1}: {wiki['title']}\n"
                sources_text += f"Summary: {wiki['summary'][:500]}...\n"
            
            # Add News data
            for i, article in enumerate(news_data[:5]):
                sources_text += f"\nNEWS SOURCE {i+1}: {article['title']}\n"
                sources_text += f"Source: {article['source']}\n"
                sources_text += f"Description: {article['description'][:300]}...\n"
              # Run the fact-checking chain (updated to use new LangChain API)
            result = await asyncio.to_thread(
                lambda: self.fact_check_chain.invoke({
                    "news_title": title,
                    "news_content": content,
                    "sources": sources_text,
                    "subcategory_info": subcategory_info # Pass new info
                })
            )
            
            # Parse the structured response (this might need adjustment based on actual LLM output)
            # For now, returning raw text, but ideally, parse into a dict
            response_text = result.content # Assuming result is an AIMessage or similar with a content attribute
            
            # Basic parsing attempt (highly dependent on LLM's consistency)
            parsed_result = {"raw_analysis": response_text}
            try:
                # Example: Extract factual score if "Factual Accuracy Score: XX%" is present
                if "factual accuracy score" in response_text.lower():
                    score_str = response_text.lower().split("factual accuracy score:")[1].split("%")[0].strip()
                    parsed_result["factual_score"] = int(float(score_str))
                if "overall verdict" in response_text.lower():
                    verdict_str = response_text.lower().split("overall verdict:")[1].split("\n")[0].strip()
                    parsed_result["verdict"] = verdict_str
                    parsed_result["is_fake"] = "fake" in verdict_str.lower() or "misleading" in verdict_str.lower()
                if "confidence in your assessment" in response_text.lower():
                    confidence_str = response_text.lower().split("confidence in your assessment:")[1].split("%")[0].strip()
                    parsed_result["confidence"] = int(float(confidence_str))
            except Exception as e:
                logger.warning(f"Could not parse RAG analysis: {e}. Returning raw text.")

            return parsed_result
            
        except Exception as e:
            logger.error(f"Error in RAG analysis: {e}")
            return {"error": str(e)}

    async def classify_news_subcategories_hf(self, text_content: str) -> Dict[str, Any]:
        """
        Placeholder for Hugging Face model to classify news into subcategories.
        This should be replaced with actual model loading and inference.
        Args:
            text_content: The news article content.
        Returns:
            A dictionary with classification results.
        """
        logger.info(f"Simulating HF subcategory classification for content (first 50 chars): {text_content[:50]}...")
        # Simulate some processing delay
        await asyncio.sleep(0.1)
        
        # Mock response - replace with actual model output
        # Example:
        if "election" in text_content.lower() or "politics" in text_content.lower():
            return {
                "primary_subcategory": "Politics",
                "secondary_subcategory": "Domestic Elections",
                "confidence": 0.85,
                "keywords_detected": ["election", "candidate"],
                "model_used": "placeholder_hf_political_news_v1"
            }
        elif "market" in text_content.lower() or "economy" in text_content.lower():
            return {
                "primary_subcategory": "Economics",
                "secondary_subcategory": "Stock Market",
                "confidence": 0.90,
                "keywords_detected": ["market", "stocks", "trade"],
                "model_used": "placeholder_hf_economic_news_v1"
            }
        else:
            return {
                "primary_subcategory": "General News",
                "secondary_subcategory": None,
                "confidence": 0.70,
                "keywords_detected": [],
                "model_used": "placeholder_hf_general_news_v1"
            }

    async def generate_news_summary(
        self,
        title: str,
        content: str,
        verification_verdict: str,
        verification_score: int,
        key_points: str # Key reasons/points from the verification
    ) -> Dict[str, Any]:
        """
        Generate a summary of the news and its verification using an LLM.
        Args:
            title: News article title.
            content: News article content.
            verification_verdict: The final verdict (e.g., "REAL", "FAKE").
            verification_score: The verification score (0-100).
            key_points: Key points or reasons supporting the verdict.
        Returns:
            Dictionary with the generated summary.
        """
        if not (self.openai_available or self.gemini_available) or not self.summarization_chain:
            logger.warning("Summarization LLM not available or chain not initialized.")
            return {"summary_text": "Summarization service not available."}

        try:
            logger.info(f"Generating summary for: {title}")
            response = await asyncio.to_thread(
                lambda: self.summarization_chain.invoke({
                    "news_title": title,
                    "news_content": content,
                    "verification_verdict": verification_verdict,
                    "verification_score": verification_score,
                    "key_points": key_points
                })
            )
            summary_text = response.content # Assuming AIMessage like object
            return {"summary_text": summary_text}
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {"summary_text": f"Error generating summary: {str(e)}"}