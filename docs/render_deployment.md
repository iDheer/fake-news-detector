# Deploying to Render.com

This guide provides step-by-step instructions for deploying the Fake News Detector application to Render.com.

## Prerequisites

- A Render.com account (free tier is sufficient for initial deployment)
- Your project code pushed to a GitHub repository
- All API keys ready (Reddit, News APIs, OpenAI)

## Deployment Steps

### Step 1: Deploy the Backend API

1. Log in to your Render.com dashboard
2. Click "New" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `fake-news-detector-api` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `sh render_build.sh`
   - **Start Command**: `cd $RENDER_PROJECT_DIR && uvicorn app.api.app:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or select paid plan for better performance)

5. Add environment variables (copy from your `.env` file):
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USERNAME`
   - `REDDIT_USER_AGENT`
   - `NEWSAPI_KEY`
   - `NEWS_DATA_API_KEY` (if available)
   - `GNEWS_API_KEY` (if available)
   - `OPENAI_API_KEY` (required for LLM features)
   - `DATABASE_URL` (For SQLite: `sqlite:///app/data/fakenews.db`)
   - `USE_GPU` (set to `False` on Render free tier)
   - `CLOUD_READY` (set to `True`)

6. Click "Create Web Service"
7. Wait for the deployment to complete
8. Note the URL of your deployed API (e.g., `https://fake-news-detector-api.onrender.com`)

### Step 2: Deploy the Streamlit Frontend

1. In Render.com dashboard, click "New" and select "Web Service"
2. Connect the same GitHub repository
3. Configure the service:
   - **Name**: `fake-news-detector-ui` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `streamlit run app/frontend/streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
   - **Plan**: Free (or select paid plan for better performance)

4. Add environment variables:
   - `API_URL`: Set this to the URL of your deployed API (from Step 1)

5. Click "Create Web Service"
6. Wait for the deployment to complete
7. Access your Streamlit frontend using the provided URL

### Step 3: Update the API URL in the Frontend Code

Before deploying the frontend, you need to update the API URL in the Streamlit app:

1. Open `app/frontend/streamlit_app.py`
2. Find the line defining `API_URL` (near the beginning)
3. Update it with your deployed API URL:
   ```python
   # API URL - change this when deploying to cloud
   API_URL = "https://fake-news-detector-api.onrender.com"  # Replace with your actual API URL
   ```

4. Commit and push this change to your GitHub repository
5. Redeploy the Streamlit frontend

### Step 4: Verify the Deployment

1. Access your Streamlit frontend using the Render.com URL
2. Try analyzing a news article to verify that the system is working correctly
3. Check for any errors in the Render.com logs if needed

## Troubleshooting

### Common Issues

- **API Connection Errors**: Make sure the API URL is correct in the frontend app
- **Dependencies Installation**: Check Render.com build logs for any errors
- **API Key Issues**: Verify that all environment variables are correctly set
- **Database Issues**: For persistent storage, consider upgrading to PostgreSQL

### Checking Logs

1. Go to your Web Service in Render.com dashboard
2. Click on the "Logs" tab
3. Review the logs for any errors or warnings

## Performance Considerations

- Free tier has limited resources and may be slower
- For better performance, consider upgrading to a paid plan
- The free tier may experience cold starts after periods of inactivity
