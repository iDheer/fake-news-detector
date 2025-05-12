# Fake News Detector

A cloud-native, microservices-based system for detecting fake news using GenAI, natural language processing, and multiple data sources.

## Overview

The Fake News Detector is a comprehensive system that analyzes news articles to determine their credibility. It uses a microservices architecture with the following components:

- **FastAPI Backend**: Provides RESTful API endpoints for news verification
- **Streamlit Frontend**: User-friendly interface with visualizations
- **Agent-based Architecture**: Coordinates multiple services for comprehensive analysis
- **Multiple Data Sources**: Reddit, Wikipedia, and various News APIs
- **AI Analysis**: Sentiment analysis, factuality classification, and LLM-based analysis with RAG

## System Architecture

![System Architecture](docs/architecture.png)

### Components

1. **Frontend Service (Streamlit)**
   - User interface for submitting news articles
   - Visualization of analysis results
   - Feedback mechanism

2. **Backend API (FastAPI)**
   - RESTful API endpoints
   - Request handling and validation
   - Database integration

3. **Agent Coordinator**
   - Orchestrates multiple services
   - Aggregates results from different sources

4. **Data Services**
   - Reddit Service: Analyzes discussions on Reddit
   - Wikipedia Service: Retrieves relevant factual information
   - News Service: Checks coverage across news sources

5. **AI Analysis Service**
   - Sentiment Analysis: Detects emotional tone
   - Language Model Analysis: In-depth content assessment
   - Retrieval Augmented Generation (RAG): Enhanced fact-checking

6. **Database**
   - Stores analyzed articles
   - Tracks user feedback for continuous improvement

## Features

- **Multi-source Verification**: Cross-references information from multiple sources
- **AI-powered Analysis**: Uses state-of-the-art language models for content analysis
- **Visualization Dashboard**: Intuitive interface with charts and metrics
- **User Feedback System**: Collects user feedback for model improvement
- **Cloud-Ready Deployment**: Can be deployed on cloud platforms like Render.com
- **Microservices Architecture**: Modular design for scalability and maintainability

## Setup and Installation

### Prerequisites

- Python 3.8+
- API keys for:
  - Reddit API
  - NewsAPI
  - OpenAI API (for GPT-3.5/4)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Hackathon1
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   # For Windows PowerShell (recommended):
   ./quick_setup.ps1

   # OR manually:
   pip install -U pip
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   python -c "import nltk; nltk.download('punkt')"
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your API keys and configuration options

5. Run the application:
   ```bash
   python run.py
   ```
   
   Or run components separately:
   ```bash
   python run.py --mode backend  # Start only the backend
   python run.py --mode frontend  # Start only the frontend
   ```

### Docker Setup

1. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. Access the application:
   - API: http://localhost:8000
   - Frontend: http://localhost:8501

## Cloud Deployment

### Deploying to Render.com

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the service:
   - Build Command: `sh render_build.sh`
   - Start Command: `uvicorn app.api.app:app --host 0.0.0.0 --port $PORT`
4. Add your environment variables from `.env` to Render's environment variables
5. Deploy

### Deploying the Streamlit Frontend

1. Create a new Web Service on Render or Streamlit Cloud
2. Connect your GitHub repository
3. Configure the service:
   - Start Command: `streamlit run app/frontend/streamlit_app.py`
4. Update the `API_URL` in `app/frontend/streamlit_app.py` to point to your deployed backend API

## Usage

1. Access the Streamlit frontend at http://localhost:8501
2. Enter a news headline and content
3. Click "Verify" to analyze the news
4. Review the analysis results and visualizations
5. Provide feedback on the analysis accuracy

## Development

### Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── agents/
│   │   └── fake_news_agent.py
│   ├── api/
│   │   └── app.py
│   ├── data/
│   ├── frontend/
│   │   └── streamlit_app.py
│   ├── models/
│   │   └── database.py
│   ├── services/
│   │   ├── ai_service.py
│   │   ├── news_service.py
│   │   ├── reddit_service.py
│   │   └── wikipedia_service.py
│   └── utils/
│       └── config.py
├── tests/
│   ├── test_ai_service.py
│   ├── test_news_service.py
│   └── test_wikipedia_service.py
├── .env
├── Dockerfile
├── docker-compose.yml
├── render_build.sh
├── requirements.txt
└── run.py
```

### Running Tests

```bash
pytest tests/
```

## GenAI Usage Reflection

This project heavily utilized GenAI tools throughout every stage of development:

### What worked well:
- **Requirements analysis**: GenAI helped define system components and features
- **Architecture design**: Generated a well-structured microservices design
- **Code generation**: Created boilerplate code and standard patterns
- **Integration**: Helped with connecting multiple services into a cohesive system
- **Testing**: Generated unit tests for various components

### Limitations encountered:
- **API-specific details**: GenAI-generated code needed adjustments for specific APIs
- **Performance optimization**: Required human expertise for fine-tuning
- **Edge cases**: Manual handling of unexpected inputs and error conditions
- **Deployment specifics**: Platform-specific deployment details required human intervention

### Overall impact:
GenAI dramatically accelerated development by handling routine coding tasks, allowing human developers to focus on architecture decisions, integration challenges, and quality assurance. It reduced development time while maintaining high code quality.

## Future Improvements

- **Enhanced RAG**: Implement more sophisticated retrieval mechanisms
- **Better Content Extraction**: Improve extraction from news articles with NLP
- **Additional Data Sources**: Integrate fact-checking websites and more news sources
- **User Authentication**: Add user accounts for personalized history
- **Model Fine-tuning**: Use collected feedback to fine-tune the analysis models
- **Real-time Analysis**: Implement streaming for large articles

## License

[MIT License](LICENSE)

## Acknowledgments

- This project was developed as part of the iREL Summer Hackathon 2023
- Thanks to all the open-source libraries that made this project possible
