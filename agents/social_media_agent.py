"""
Social Media Agent - Collects and analyzes sentiment from social media platforms.
"""

import requests
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import os
import finnhub
from .base_agent import BaseAgent

class SocialMediaAgent(BaseAgent):
    """Agent responsible for collecting and analyzing social media sentiment."""
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.1):
        super().__init__(model_name, temperature)
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT", "StockAnalystBot/1.0")
        # Initialize Finnhub client
        self.finnhub_client = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))
    
    def collect_data(self, ticker: str) -> Dict[str, Any]:
        """
        Collect social media data for the given ticker.
        
        Args:
            ticker: The stock ticker symbol
            
        Returns:
            Dictionary containing social media sentiment and analysis
        """
        try:
            data = {
                "ticker": ticker,
                "finnhub_sentiment": self._collect_finnhub_sentiment(ticker),
                "web_sentiment": self._collect_web_sentiment(ticker),
                "sentiment_summary": {}
            }
            
            # Aggregate sentiment data
            data["sentiment_summary"] = self._aggregate_sentiment(data)
            
            return data
            
        except Exception as e:
            return {"error": f"Error collecting social media data: {str(e)}"}
    
    def _collect_web_sentiment(self, ticker: str) -> Dict[str, Any]:
        """Collect sentiment data from web search."""
        try:
            # Search for recent social media mentions and discussions
            search_queries = [
                f"{ticker} stock reddit discussion",
                f"{ticker} twitter sentiment",
                f"{ticker} social media buzz",
                f"{ticker} investor sentiment"
            ]
            
            web_posts = []
            for query in search_queries:
                try:
                    search_results = self._perform_web_search(query)
                    if search_results:
                        web_posts.extend(search_results[:2])  # Limit to 2 results per query
                except Exception as e:
                    print(f"Error searching for '{query}': {str(e)}")
                    continue
            
            if web_posts:
                return {
                    "posts": web_posts[:8],  # Limit to 8 total posts
                    "total_posts": len(web_posts),
                    "source": "Web Search",
                    "sentiment_distribution": self._calculate_sentiment_distribution(web_posts),
                    "note": "Data collected from public web search. Limited to recent, publicly available social media discussions."
                }
            else:
                return {
                    "posts": [],
                    "total_posts": 0,
                    "source": "Web Search",
                    "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                    "note": "No recent social media discussions found via web search. Consider using paid social media APIs for comprehensive coverage."
                }
                
        except Exception as e:
            return {"error": f"Error collecting web sentiment: {str(e)}"}
    
    def _perform_web_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform a web search and return results."""
        try:
            # Google Custom Search API implementation
            google_api_key = os.getenv("GOOGLE_API_KEY")
            google_cse_id = os.getenv("GOOGLE_CSE_ID")
            
            if not google_api_key or not google_cse_id:
                print(f"Google search attempted for: {query}")
                print("Note: Google Custom Search API not configured. Set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables.")
                print("To set up Google Custom Search API:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Enable Custom Search API")
                print("3. Create API key")
                print("4. Go to https://cse.google.com/ to create Custom Search Engine")
                print("5. Set environment variables: GOOGLE_API_KEY and GOOGLE_CSE_ID")
                return []
            
            # Google Custom Search API endpoint
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': google_api_key,
                'cx': google_cse_id,
                'q': query,
                'num': 5,  # Number of results (max 10)
                'dateRestrict': 'd7',  # Restrict to last 7 days
                'sort': 'date'  # Sort by date
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Extract search results
                if 'items' in data:
                    for item in data['items']:
                        results.append({
                            "title": item.get('title', 'No title'),
                            "content": item.get('snippet', 'No content'),
                            "source": item.get('displayLink', 'Unknown'),
                            "url": item.get('link', ''),
                            "sentiment": self._analyze_news_sentiment(item.get('snippet', '')),
                            "date": datetime.now().isoformat()  # Google doesn't always provide exact dates
                        })
                
                return results
            else:
                print(f"Google search failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"Google search error: {str(e)}")
            return []
    
    def _calculate_sentiment_distribution(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate sentiment distribution from posts."""
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        
        for post in posts:
            sentiment = post.get("sentiment", "neutral")
            sentiment_counts[sentiment] += 1
        
        return sentiment_counts
    
    def _collect_finnhub_sentiment(self, ticker: str) -> Dict[str, Any]:
        """Collect sentiment data from Finnhub news."""
        try:
            # Get news sentiment from the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Get company news from Finnhub
            news = self.finnhub_client.company_news(
                ticker, 
                _from=start_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d')
            )
            
            if news and len(news) > 0:
                # Analyze sentiment for each news article
                sentiments = []
                for article in news:
                    sentiment_score = self._analyze_news_sentiment(article.get("summary", ""))
                    sentiments.append({
                        "headline": article.get("headline", ""),
                        "sentiment": sentiment_score,
                        "date": datetime.fromtimestamp(article.get("datetime", 0)).isoformat(),
                        "source": article.get("source", "Unknown")
                    })
                
                # Calculate sentiment statistics
                positive_count = sum(1 for s in sentiments if s["sentiment"] == "positive")
                negative_count = sum(1 for s in sentiments if s["sentiment"] == "negative")
                neutral_count = sum(1 for s in sentiments if s["sentiment"] == "neutral")
                total_count = len(sentiments)
                
                return {
                    "sentiments": sentiments,
                    "total_articles": total_count,
                    "sentiment_distribution": {
                        "positive": positive_count,
                        "negative": negative_count,
                        "neutral": neutral_count
                    },
                    "sentiment_percentages": {
                        "positive": (positive_count / total_count * 100) if total_count > 0 else 0,
                        "negative": (negative_count / total_count * 100) if total_count > 0 else 0,
                        "neutral": (neutral_count / total_count * 100) if total_count > 0 else 0
                    },
                    "source": "Finnhub News Sentiment"
                }
            else:
                return {
                    "sentiments": [],
                    "total_articles": 0,
                    "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                    "sentiment_percentages": {"positive": 0, "negative": 0, "neutral": 0},
                    "source": "Finnhub News Sentiment"
                }
                
        except Exception as e:
            return {"error": f"Error collecting Finnhub sentiment: {str(e)}"}
    
    def _analyze_news_sentiment(self, text: str) -> str:
        """Analyze sentiment of news text."""
        if not text:
            return "neutral"
        
        text_lower = text.lower()
        
        # Enhanced sentiment keywords
        positive_words = [
            "positive", "growth", "increase", "profit", "success", "strong", "beat", "exceed", 
            "up", "rise", "gain", "surge", "jump", "soar", "rally", "boost", "improve", "expand",
            "record", "high", "outperform", "bullish", "optimistic", "favorable", "robust"
        ]
        
        negative_words = [
            "negative", "decline", "decrease", "loss", "weak", "miss", "down", "fall", "drop", 
            "risk", "concern", "worry", "fear", "crash", "plunge", "tumble", "slump", "downturn",
            "bearish", "pessimistic", "unfavorable", "struggle", "challenge", "pressure"
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _aggregate_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate sentiment data from all sources."""
        try:
            finnhub_sentiment = data.get("finnhub_sentiment", {})
            web_sentiment = data.get("web_sentiment", {})
            
            # Count sentiments
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
            
            # Count Finnhub sentiments
            if "sentiments" in finnhub_sentiment:
                for sentiment_item in finnhub_sentiment["sentiments"]:
                    sentiment = sentiment_item.get("sentiment", "neutral")
                    sentiment_counts[sentiment] += 1
            
            # Count web sentiment posts
            if "posts" in web_sentiment:
                for post in web_sentiment["posts"]:
                    sentiment = post.get("sentiment", "neutral")
                    sentiment_counts[sentiment] += 1
            
            total_posts = sum(sentiment_counts.values())
            
            if total_posts > 0:
                # Calculate sentiment percentages
                sentiment_percentages = {
                    sentiment: (count / total_posts) * 100 
                    for sentiment, count in sentiment_counts.items()
                }
                
                # Determine overall sentiment
                if sentiment_percentages["positive"] > sentiment_percentages["negative"]:
                    overall_sentiment = "positive"
                elif sentiment_percentages["negative"] > sentiment_percentages["positive"]:
                    overall_sentiment = "negative"
                else:
                    overall_sentiment = "neutral"
            else:
                sentiment_percentages = {"positive": 0, "negative": 0, "neutral": 0}
                overall_sentiment = "neutral"
            
            return {
                "counts": sentiment_counts,
                "percentages": sentiment_percentages,
                "overall_sentiment": overall_sentiment,
                "total_posts": total_posts,
                "finnhub_sentiment": finnhub_sentiment.get("sentiment_distribution", {}),
                "finnhub_percentages": finnhub_sentiment.get("sentiment_percentages", {}),
                "web_sentiment": web_sentiment.get("sentiment_distribution", {}),
                "note": web_sentiment.get("note", "No additional notes")
            }
            
        except Exception as e:
            return {"error": f"Error aggregating sentiment: {str(e)}"}
    
    def analyze_data(self, data: Dict[str, Any]) -> str:
        """
        Analyze the social media data and provide insights.
        
        Args:
            data: The collected social media data
            
        Returns:
            String containing the analysis and insights
        """
        if "error" in data:
            return f"Error in social media analysis: {data['error']}"
        
        # Prepare data for LLM analysis
        analysis_prompt = self._create_analysis_prompt(data)
        
        # Get LLM analysis
        response = self.llm.invoke(analysis_prompt)
        
        return response.content
    
    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create the analysis prompt for the LLM."""
        
        ticker = data.get("ticker", "N/A")
        finnhub_sentiment = data.get("finnhub_sentiment", {})
        web_sentiment = data.get("web_sentiment", {})
        sentiment_summary = data.get("sentiment_summary", {})
        
        # Format Finnhub sentiment data
        finnhub_sentiments = finnhub_sentiment.get("sentiments", [])
        finnhub_text = ""
        for i, sentiment_item in enumerate(finnhub_sentiments[:5], 1):  # Limit to 5 articles
            finnhub_text += f"{i}. {sentiment_item.get('headline', 'N/A')} - Sentiment: {sentiment_item.get('sentiment', 'N/A')}\n"
        
        # Format web sentiment data
        web_posts = web_sentiment.get("posts", [])
        web_text = ""
        for i, post in enumerate(web_posts[:5], 1):  # Limit to 5 posts
            web_text += f"{i}. {post.get('title', 'N/A')} - Sentiment: {post.get('sentiment', 'N/A')}\n"
        
        # Format sentiment summary
        sentiment_counts = sentiment_summary.get("counts", {})
        sentiment_percentages = sentiment_summary.get("percentages", {})
        overall_sentiment = sentiment_summary.get("overall_sentiment", "N/A")
        finnhub_distribution = sentiment_summary.get("finnhub_sentiment", {})
        finnhub_percentages = sentiment_summary.get("finnhub_percentages", {})
        web_distribution = sentiment_summary.get("web_sentiment", {})
        
        prompt = f"""
You are a social media sentiment analyst. Analyze the following social media data for {ticker} and provide insights about public sentiment and market perception.

Ticker: {ticker}

Finnhub News Sentiment (Top 5) (Source: Finnhub API):
{finnhub_text if finnhub_text else "No Finnhub news sentiment available"}

Web Social Media Sentiment (Top 5) (Source: Google Custom Search):
{web_text if web_text else "No web social media sentiment available"}

Overall Sentiment Analysis:
- Positive: {sentiment_counts.get('positive', 0)} posts ({sentiment_percentages.get('positive', 0):.1f}%)
- Negative: {sentiment_counts.get('negative', 0)} posts ({sentiment_percentages.get('negative', 0):.1f}%)
- Neutral: {sentiment_counts.get('neutral', 0)} posts ({sentiment_percentages.get('neutral', 0):.1f}%)
- Overall Sentiment: {overall_sentiment}

Finnhub News Sentiment Breakdown (Source: Finnhub API):
- Positive: {finnhub_distribution.get('positive', 0)} articles ({finnhub_percentages.get('positive', 0):.1f}%)
- Negative: {finnhub_distribution.get('negative', 0)} articles ({finnhub_percentages.get('negative', 0):.1f}%)
- Neutral: {finnhub_distribution.get('neutral', 0)} articles ({finnhub_percentages.get('neutral', 0):.1f}%)

Web Social Media Sentiment Breakdown (Source: Google Custom Search):
- Positive: {web_distribution.get('positive', 0)} posts
- Negative: {web_distribution.get('negative', 0)} posts
- Neutral: {web_distribution.get('neutral', 0)} posts

Please provide a detailed analysis covering:
1. Overall social media sentiment and its implications
2. Key themes and topics being discussed across platforms
3. Sentiment trends and changes over time
4. News sentiment analysis and its impact on market perception
5. Potential impact on stock price based on sentiment
6. Notable mentions or influencers
7. Risk factors based on social media and news sentiment
8. Comparison between news sentiment and social media sentiment

IMPORTANT CITATION REQUIREMENTS:
- Cite the data source for EVERY sentiment statistic, post, or metric you mention
- Use format: "According to Finnhub API, X% of news articles show positive sentiment" or "Google Custom Search found Y social media posts with negative sentiment"
- Include specific post content and sources when referencing social media
- If data is not available, clearly state "No data available from [source]"
- Be specific about which API provided which piece of information

Examples of proper citations:
- "According to Finnhub API, 49.7% of news articles show positive sentiment"
- "Google Custom Search found 2 social media posts discussing {ticker} stock"
- "Finnhub API reports 38.7% neutral sentiment in news coverage"
- "Web search results show growing interest in {ticker} on social platforms (Google Custom Search)"

Write in clear, professional language suitable for investment decision-making.

Additional Notes:
{web_sentiment.get('note', 'No additional notes')}
"""
        return prompt 