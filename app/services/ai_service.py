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
                input_variables=["news_title", "news_content", "sources"],
                template="""
                As an AI fact-checker, analyze the following news article for credibility.
                
                ARTICLE TITLE: {news_title}
                
                ARTICLE CONTENT: {news_content}
                
                REFERENCE SOURCES:
                {sources}
                
                Please provide:
                1. A factual accuracy score (0-100%)
                2. Identification of any misleading claims
                3. Assessment of source credibility
                4. Overall verdict (REAL NEWS or FAKE/MISLEADING NEWS)
                5. Confidence in your assessment (0-100%)
                
                Format your response as a structured analysis with clear headings.
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
        news_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze news using Retrieval Augmented Generation
        
        Args:
            title: News article title
            content: News article content
            wiki_data: Wikipedia articles data
            news_data: News articles data
            
        Returns:
            Dictionary with analysis results
        """
        # Check if either OpenAI or Gemini is available
        if not (self.openai_available or self.gemini_available):
            return {"error": "Neither OpenAI nor Gemini API is available"}
        
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
                    "sources": sources_text
                }).content
            )
            
            # Extract key information from the result
            lines = result.split('\n')
            
            # Parse the result to extract structured information
            factual_score = None
            verdict = None
            confidence = None
            
            for line in lines:
                if "accuracy score" in line.lower():
                    try:
                        # Extract percentage
                        factual_score = int(line.split('%')[0].split()[-1])
                    except:
                        pass
                elif "verdict" in line.lower():
                    if "fake" in line.lower() or "misleading" in line.lower():
                        verdict = "FAKE"
                    elif "real" in line.lower():
                        verdict = "REAL"
                elif "confidence" in line.lower():
                    try:
                        # Extract percentage
                        confidence = int(line.split('%')[0].split()[-1])
                    except:
                        pass
            
            # If we couldn't extract structured information, use default values
            if factual_score is None:
                factual_score = 50
            
            if verdict is None:
                verdict = "UNCERTAIN"
                
            if confidence is None:
                confidence = 70
            
            return {
                "factual_score": factual_score,
                "verdict": verdict,
                "confidence": confidence,
                "detailed_analysis": result,
                "is_fake": verdict == "FAKE"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news with RAG: {e}")
            return {"error": str(e)}