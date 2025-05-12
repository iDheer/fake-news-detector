FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Install spaCy model
RUN python -m spacy download en_core_web_sm

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt')"

# Copy application code
COPY . .

# Set environment variable
ENV PYTHONPATH=/app

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Create an entrypoint script
RUN echo '#!/bin/bash\n\
uvicorn app.api.app:app --host 0.0.0.0 --port 8000 & \n\
streamlit run app/frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0\n\
wait\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
