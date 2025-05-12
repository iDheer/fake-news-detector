"""
Streamlit frontend for Fake News Detection system
"""
import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import json

# Set page configuration
st.set_page_config(
    page_title="Fake News Detector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API URL - change this when deploying to cloud
API_URL = "http://localhost:8000"

# Custom CSS with improved color scheme and readability
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1e3a8a;
    }
    p, li, div {
        color: #333333;
    }
    .verdict-fake {
        font-size: 24px;
        color: #dc2626;
        font-weight: bold;
        background-color: #fee2e2;
        padding: 8px 16px;
        border-radius: 4px;
        display: inline-block;
    }
    .verdict-real {
        font-size: 24px;
        color: #059669;
        font-weight: bold;
        background-color: #d1fae5;
        padding: 8px 16px;
        border-radius: 4px;
        display: inline-block;
    }
    .source-item {
        border-left: 3px solid #3b82f6;
        padding: 10px;
        margin-bottom: 15px;
        background-color: #ffffff;
        border-radius: 0 4px 4px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .feedback-box {
        background-color: #eff6ff;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
        border: 1px solid #bfdbfe;
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2563eb;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
    }
    .st-bb {
        background-color: #3b82f6;
    }
    .st-at {
        background-color: #bfdbfe;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f1f5f9;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #dbeafe;
        color: #1e40af;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

def create_gauge_chart(value, title):
    """Create a gauge chart for visualization"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, 30], 'color': "#d9534f"},
                {'range': [30, 70], 'color': "#f0ad4e"},
                {'range': [70, 100], 'color': "#5cb85c"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=50, b=10))
    return fig

def analyze_news(title, content):
    """Send news to API for analysis"""
    try:
        response = requests.post(
            f"{API_URL}/api/verify",
            json={"title": title, "content": content}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        return None

def submit_feedback(article_id, is_correct, feedback_text=""):
    """Submit user feedback on verification results"""
    try:
        response = requests.post(
            f"{API_URL}/api/feedback",
            json={
                "article_id": article_id,
                "is_correct": is_correct,
                "feedback_text": feedback_text
            }
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error submitting feedback: {e}")
        return False

def get_history():
    """Retrieve verification history"""
    try:
        response = requests.get(f"{API_URL}/api/history")
        if response.status_code == 200:
            return response.json()
        return {"articles": []}
    except:
        return {"articles": []}

def save_result_locally(result):
    """Save result locally for demo purposes (when API is not available)"""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    history_file = data_dir / "local_history.json"
    
    try:
        if history_file.exists():
            with open(history_file, "r") as f:
                history = json.load(f)
        else:
            history = {"results": []}
        
        # Add timestamp
        result["saved_at"] = datetime.now().isoformat()
        
        # Add to history
        history["results"].append(result)
        
        # Save
        with open(history_file, "w") as f:
            json.dump(history, f)
            
    except Exception as e:
        st.error(f"Error saving result locally: {e}")

def display_analysis_result(result):
    """Display analysis result"""
    if not result:
        return
    
    # Extract verification result
    verification = result.get("verification_result", {})
    verdict = verification.get("verdict", "UNKNOWN")
    score = verification.get("score", 0)
    confidence = verification.get("confidence", 0)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.subheader("Verdict")
        if verdict == "FAKE":
            st.markdown(f"<p class='verdict-fake'>{verdict}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p class='verdict-real'>{verdict}</p>", unsafe_allow_html=True)
        
        st.metric("Confidence", f"{confidence}%")
        st.metric("Processing Time", f"{result.get('processing_time', 0):.2f} seconds")
    
    with col2:
        st.subheader("Credibility Score")
        st.plotly_chart(create_gauge_chart(score, "Overall Score"), use_container_width=True)
    
    with col3:
        st.subheader("Score Breakdown")
        source_cred = verification.get("source_credibility", 0)
        content_cons = verification.get("content_consistency", 0)
        fact_verif = verification.get("fact_verification", 0)
        
        # Create a bar chart
        data = pd.DataFrame({
            'Category': ['Source Credibility', 'Content Consistency', 'Fact Verification'],
            'Score': [source_cred, content_cons, fact_verif]
        })
        
        fig = px.bar(data, y='Category', x='Score', orientation='h',
                    labels={'Score': 'Score (out of 100)'}, 
                    color='Score',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    range_color=[0, 50])
        fig.update_layout(height=200)
        st.plotly_chart(fig, use_container_width=True)
    
    # Display detailed information in tabs
    st.subheader("Detailed Analysis")
    tab1, tab2, tab3, tab4 = st.tabs(["Source Analysis", "News Consistency", "RAG Analysis", "Sentiment"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Reddit Analysis")
            reddit_data = result.get("reddit_data", {})
            
            if reddit_data.get("reddit_results", False):
                st.metric("Discussion Count", reddit_data.get("discussion_count", 0))
                st.write("**Top Sources:**")
                for source in reddit_data.get("top_sources", [])[:3]:
                    st.markdown(f"- r/{source.get('subreddit', '')} ({source.get('count', 0)} posts)")
                
                st.write("**Sample Posts:**")
                for post in reddit_data.get("sample_posts", []):
                    st.markdown(f"<div class='source-item'>"
                            f"<b>{post.get('title', '')}</b><br>"
                            f"r/{post.get('subreddit', '')} | Score: {post.get('score', 0)} | "
                            f"Comments: {post.get('comments', 0)}"
                            f"</div>", unsafe_allow_html=True)
            else:
                st.info("No Reddit discussions found")
        
        with col2:
            st.write("### Wikipedia References")
            wiki_articles = result.get("wikipedia_articles", [])
            
            if wiki_articles:
                for article in wiki_articles:
                    st.markdown(f"<div class='source-item'>"
                               f"<b>{article.get('title', '')}</b><br>"
                               f"{article.get('summary', '')[:200]}..."
                               f"</div>", unsafe_allow_html=True)
            else:
                st.info("No Wikipedia articles found")
    
    with tab2:
        st.write("### News Articles")
        news_data = result.get("news_data", {})
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Articles", news_data.get("articles_count", 0))
        col2.metric("Unique Sources", news_data.get("sources_count", 0))
        
        st.write("**Sample Articles:**")
        for article in news_data.get("sample_articles", []):
            st.markdown(f"<div class='source-item'>"
                       f"<b>{article.get('title', '')}</b><br>"
                       f"Source: {article.get('source', 'Unknown')}"
                       f"</div>", unsafe_allow_html=True)
            if article.get("url"):
                st.markdown(f"[Read Article]({article.get('url')})")
    
    with tab3:
        st.write("### AI Analysis")
        rag_analysis = result.get("rag_analysis", {})
        
        if "error" not in rag_analysis:
            col1, col2, col3 = st.columns(3)
            col1.metric("Factual Score", f"{rag_analysis.get('factual_score', 0)}%")
            col2.metric("Verdict", rag_analysis.get("verdict", "UNKNOWN"))
            col3.metric("Confidence", f"{rag_analysis.get('confidence', 0)}%")
            
            st.write("**Detailed AI Analysis:**")
            st.write(rag_analysis.get("detailed_analysis", "No detailed analysis available"))
        else:
            st.error(f"AI Analysis Error: {rag_analysis.get('error')}")
    
    with tab4:
        st.write("### Sentiment Analysis")
        sentiment_analysis = result.get("sentiment_analysis", {})
        
        if "error" not in sentiment_analysis:
            sentiment = sentiment_analysis.get("sentiment", "neutral")
            score = sentiment_analysis.get("score", 0.5)
            
            # Create a gauge chart for sentiment
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score * 100,  # Convert to percentage
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Sentiment: {sentiment.capitalize()}"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#1f77b4" if sentiment == "neutral" else 
                                    "#d9534f" if sentiment == "negative" else "#5cb85c"},
                    'steps': [
                        {'range': [0, 33], 'color': "#d9534f"},
                        {'range': [33, 67], 'color': "#f0ad4e"},
                        {'range': [67, 100], 'color': "#5cb85c"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': score * 100
                    }
                }
            ))
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            st.write(sentiment_analysis.get("analysis", ""))
        else:
            st.error(f"Sentiment Analysis Error: {sentiment_analysis.get('error')}")
    
    # User feedback section
    st.subheader("Feedback")
    st.markdown("<div class='feedback-box'>", unsafe_allow_html=True)
    st.write("Was this analysis helpful?")
    
    col1, col2, col3 = st.columns([1, 1, 3])
    
    article_id = result.get("article_id")
    
    with col1:
        if st.button("👍 Yes"):
            if article_id:
                if submit_feedback(article_id, True):
                    st.success("Thank you for your feedback!")
            else:
                st.info("Thank you for your feedback! (Demo mode - feedback not saved)")
    
    with col2:
        if st.button("👎 No"):
            if article_id:
                feedback_text = st.text_area("Please tell us why", "")
                if st.button("Submit"):
                    if submit_feedback(article_id, False, feedback_text):
                        st.success("Thank you for your feedback!")
            else:
                st.info("Thank you for your feedback! (Demo mode - feedback not saved)")
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    """Main function for the Streamlit app"""
    st.title("🔍 Fake News Detector")
    st.markdown("""
    <div style="background-color: #e0f2fe; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #0284c7;">
        <h4 style="color: #0369a1; margin-top: 0;">About this tool</h4>
        <p style="color: #333333;">This AI-powered tool analyzes news content across multiple sources to detect misinformation and fake news.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation with improved sidebar
    with st.sidebar:
        st.markdown("## Navigation")
        page = st.radio("", ["Verify News", "History"], index=0)
        
        st.markdown("---")
        st.markdown("### How it works")
        st.markdown("""
        1. Enter a news headline and content
        2. Our AI analyzes it using multiple sources
        3. Get a detailed report on authenticity
        """)
        
        st.markdown("---")
        st.markdown("### Data sources")
        st.markdown("- News APIs")
        st.markdown("- Wikipedia")
        st.markdown("- Reddit discussions")
        st.markdown("- AI analysis")
    
    if page == "Verify News":
        st.header("Verify News Content")
        st.markdown("<p style='color: #4b5563; margin-bottom: 20px;'>Enter a news headline and content to verify its authenticity</p>", unsafe_allow_html=True)
        
        with st.form("news_form"):
            st.markdown("<p style='font-weight: 600; color: #111827;'>News Information</p>", unsafe_allow_html=True)
            title = st.text_input("News Headline", max_chars=300, placeholder="Enter the headline of the news article...")
            content = st.text_area("News Content", height=200, max_chars=5000, placeholder="Paste the full article content here...")
            
            # Submit button with better styling
            submitted = st.form_submit_button("Verify News")
            
        if submitted:
            if len(title) < 3:
                st.markdown("""
                <div style="background-color: #fee2e2; padding: 15px; border-radius: 8px; border-left: 5px solid #dc2626;">
                    <p style="margin: 0; color: #7f1d1d;">Please enter a longer headline (at least 3 characters)</p>
                </div>
                """, unsafe_allow_html=True)
            elif len(content) < 10:
                st.markdown("""
                <div style="background-color: #fee2e2; padding: 15px; border-radius: 8px; border-left: 5px solid #dc2626;">
                    <p style="margin: 0; color: #7f1d1d;">Please enter more content (at least 10 characters)</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                with st.spinner("Analyzing news content... This may take a moment"):
                    try:
                        # Call API to analyze news
                        result = analyze_news(title, content)
                        
                        if not result:
                            st.markdown("""
                            <div style="background-color: #fee2e2; padding: 15px; border-radius: 8px; border-left: 5px solid #dc2626;">
                                <p style="margin: 0; color: #7f1d1d;">Failed to analyze news. Please try again or check if the API server is running.</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Show success message
                            st.markdown("""
                            <div style="background-color: #d1fae5; padding: 15px; border-radius: 8px; border-left: 5px solid #059669; margin-bottom: 20px;">
                                <p style="margin: 0; color: #065f46;">✅ Analysis complete! See results below.</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Display the analysis result
                            display_analysis_result(result)
                            
                            # Save result locally if no article ID (demo mode)
                            if not result.get("article_id"):
                                save_result_locally(result)
                    except Exception as e:
                        st.markdown(f"""
                        <div style="background-color: #fee2e2; padding: 15px; border-radius: 8px; border-left: 5px solid #dc2626;">
                            <p style="margin: 0; color: #7f1d1d;">Error: {e}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("""
                        <div style="background-color: #eff6ff; padding: 15px; border-radius: 8px; margin-top: 10px;">
                            <p style="margin: 0; color: #1e40af;">Using demo mode since API might not be available. Some features may be limited.</p>
                        </div>
                        """, unsafe_allow_html=True)
        elif page == "History":
            st.header("Verification History")
            st.markdown("<p style='color: #4b5563; margin-bottom: 20px;'>View your past news verification results</p>", unsafe_allow_html=True)
        
        try:
            history = get_history()
            
            if not history or not history.get("articles"):
                st.markdown("""
                <div style="background-color: #f3f4f6; padding: 30px; border-radius: 8px; text-align: center; margin-top: 30px;">
                    <img src="https://img.icons8.com/fluency/96/000000/empty-box.png" style="width: 60px; margin-bottom: 10px;">
                    <h3 style="color: #4b5563;">No History Found</h3>
                    <p style="color: #6b7280;">You haven't analyzed any news articles yet.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                articles = history.get("articles", [])
                
                # Create a DataFrame with improved formatting
                df = pd.DataFrame({
                    "ID": [a.get("id") for a in articles],
                    "Title": [a.get("title") for a in articles],
                    "Verdict": ["FAKE" if a.get("is_fake") else "REAL" for a in articles],
                    "Probability": [f"{a.get('fake_probability', 0):.1f}%" for a in articles],
                    "Date": [a.get("created_at") for a in articles]
                })
                
                # Apply styling to the dataframe
                st.markdown("""
                <style>
                .dataframe {
                    border-collapse: collapse;
                    margin: 25px 0;
                    font-size: 0.9em;
                    font-family: sans-serif;
                    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
                    border-radius: 6px;
                    overflow: hidden;
                }
                .dataframe thead tr {
                    background-color: #1e40af;
                    color: #ffffff;
                    text-align: left;
                }
                .dataframe th,
                .dataframe td {
                    padding: 12px 15px;
                }
                .dataframe tbody tr {
                    border-bottom: 1px solid #dddddd;
                }
                .dataframe tbody tr:nth-of-type(even) {
                    background-color: #f3f4f6;
                }
                .dataframe tbody tr:last-of-type {
                    border-bottom: 2px solid #1e40af;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Display as table
                st.dataframe(df)
                
                # Create chart for fake vs real news
                fake_count = sum(1 for a in articles if a.get("is_fake"))
                real_count = len(articles) - fake_count
                
                fig = px.pie(
                    values=[fake_count, real_count],
                    names=["Fake News", "Real News"],
                    title="Fake vs Real News Distribution"
                )
                
                st.plotly_chart(fig)
                
        except Exception as e:
            st.error(f"Error loading history: {e}")
    
    # Sidebar
    st.sidebar.header("About")
    st.sidebar.info(
        "This app uses AI and multiple data sources to detect fake news. "
        "It analyzes the news content, checks it against reliable sources, "
        "and provides a credibility score and detailed analysis."
    )
    
    st.sidebar.header("Data Sources")
    st.sidebar.markdown("""
    - Reddit discussions
    - Wikipedia articles
    - News API
    - AI analysis (LLM + RAG)
    """)

if __name__ == "__main__":
    main()
