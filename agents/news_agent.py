"""
News Agent - Collects and analyzes recent news and macroeconomic indicators.
"""

import requests
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import os
import finnhub
from .base_agent import BaseAgent

class NewsAgent(BaseAgent):
    """Agent responsible for collecting and analyzing news data."""
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.1):
        super().__init__(model_name, temperature)
        self.news_api_key = os.getenv("NEWS_API_KEY")
        # Initialize Finnhub client
        self.finnhub_client = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))
    
    def collect_data(self, ticker: str) -> Dict[str, Any]:
        """
        Collect news data for the given ticker.
        
        Args:
            ticker: The stock ticker symbol
            
        Returns:
            Dictionary containing news articles and analysis
        """
        try:
            data = {
                "ticker": ticker,
                "finnhub_news": self._collect_finnhub_news(ticker),
                "web_news": self._collect_web_news(ticker),
                "news_summary": {}
            }
            
            # Aggregate news data
            data["news_summary"] = self._aggregate_news_data(data)
            
            return data
            
        except Exception as e:
            return {"error": f"Error collecting news data: {str(e)}"}
    
    def _collect_web_news(self, ticker: str) -> Dict[str, Any]:
        """Collect news from web search."""
        try:
            # Perform web search for recent news about the company
            search_queries = [
                f"{ticker} stock news today",
                f"{ticker} earnings latest",
                f"{ticker} company news",
                f"{ticker} financial performance"
            ]
            
            articles = []
            for query in search_queries:
                try:
                    # Use a simple web search (you can replace this with a proper search API)
                    search_results = self._perform_web_search(query)
                    if search_results:
                        articles.extend(search_results[:3])  # Limit to 3 results per query
                except Exception as e:
                    print(f"Error searching for '{query}': {str(e)}")
                    continue
            
            if articles:
                return {
                    "articles": articles[:10],  # Limit to 10 total articles
                    "total_articles": len(articles),
                    "source": "Web Search",
                    "sentiment_distribution": self._calculate_sentiment_distribution(articles),
                    "note": "Data collected from public web search. Limited to recent, publicly available information."
                }
            else:
                return {
                    "articles": [],
                    "total_articles": 0,
                    "source": "Web Search",
                    "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                    "note": "No recent news found via web search. Consider using paid news APIs for more comprehensive coverage."
                }
                
        except Exception as e:
            return {"error": f"Error collecting web news: {str(e)}"}
    
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
                            "description": item.get('snippet', 'No description'),
                            "source": item.get('displayLink', 'Unknown'),
                            "url": item.get('link', ''),
                            "published_at": datetime.now().isoformat(),  # Google doesn't always provide exact dates
                            "sentiment": self._analyze_sentiment(item.get('snippet', '')),
                            "relevance_score": 0.8
                        })
                
                return results
            else:
                print(f"Google search failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"Google search error: {str(e)}")
            return []
    
    def _collect_finnhub_news(self, ticker: str) -> Dict[str, Any]:
        """Collect company-specific news from Finnhub."""
        try:
            # Get news from the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Get company news from Finnhub
            news = self.finnhub_client.company_news(
                ticker, 
                _from=start_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d')
            )
            
            if news and len(news) > 0:
                # Process and format news articles
                articles = []
                for article in news[:10]:  # Limit to 10 most recent articles
                    articles.append({
                        "title": article.get("headline", "No title"),
                        "description": article.get("summary", "No summary"),
                        "source": article.get("source", "Unknown"),
                        "url": article.get("url", ""),
                        "published_at": datetime.fromtimestamp(article.get("datetime", 0)).isoformat(),
                        "sentiment": self._analyze_sentiment(article.get("summary", "")),
                        "relevance_score": 0.9  # High relevance since it's company-specific
                    })
                
                return {
                    "articles": articles,
                    "total_articles": len(articles),
                    "source": "Finnhub API",
                    "sentiment_distribution": self._calculate_sentiment_distribution(articles),
                    "note": "Real-time news data from Finnhub API"
                }
            else:
                return {
                    "articles": [],
                    "total_articles": 0,
                    "source": "Finnhub API",
                    "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                    "note": "No recent news found in Finnhub database"
                }
                
        except Exception as e:
            return {"error": f"Error collecting Finnhub news: {str(e)}"}
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis based on keywords."""
        if not text:
            return "neutral"
        
        text_lower = text.lower()
        
        # Positive keywords
        positive_words = ["positive", "growth", "increase", "profit", "success", "strong", "beat", "exceed", "up", "rise", "gain"]
        # Negative keywords
        negative_words = ["negative", "decline", "decrease", "loss", "weak", "miss", "down", "fall", "drop", "risk", "concern"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _calculate_sentiment_distribution(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate sentiment distribution from articles."""
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        
        for article in articles:
            sentiment = article.get("sentiment", "neutral")
            sentiment_counts[sentiment] += 1
        
        return sentiment_counts
    
    def _aggregate_news_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate news data from all sources."""
        try:
            finnhub_news = data.get("finnhub_news", {})
            web_news = data.get("web_news", {})
            
            # Combine all articles
            all_articles = []
            all_articles.extend(finnhub_news.get("articles", []))
            all_articles.extend(web_news.get("articles", []))
            
            # Count sentiments
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
            
            for article in all_articles:
                sentiment = article.get("sentiment", "neutral")
                sentiment_counts[sentiment] += 1
            
            total_articles = sum(sentiment_counts.values())
            
            if total_articles > 0:
                # Calculate sentiment percentages
                sentiment_percentages = {
                    sentiment: (count / total_articles) * 100 
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
                "total_articles": total_articles,
                "sentiment_counts": sentiment_counts,
                "sentiment_percentages": sentiment_percentages,
                "overall_sentiment": overall_sentiment,
                "finnhub_sentiment_distribution": finnhub_news.get("sentiment_distribution", {}),
                "web_sentiment_distribution": web_news.get("sentiment_distribution", {}),
                "note": web_news.get("note", "No additional notes")
            }
            
        except Exception as e:
            return {"error": f"Error aggregating news data: {str(e)}"}
    
    def analyze_data(self, data: Dict[str, Any]) -> str:
        """
        Analyze the news data and provide insights.
        
        Args:
            data: The collected news data
            
        Returns:
            String containing the analysis and insights
        """
        if "error" in data:
            return f"Error in news analysis: {data['error']}"
        
        # Prepare data for LLM analysis
        analysis_prompt = self._create_analysis_prompt(data)
        
        # Get LLM analysis
        response = self.llm.invoke(analysis_prompt)
        
        return response.content
    
    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create the analysis prompt for the LLM."""
        
        ticker = data.get("ticker", "N/A")
        finnhub_news = data.get("finnhub_news", {})
        web_news = data.get("web_news", {})
        news_summary = data.get("news_summary", {})
        
        # Format Finnhub news
        finnhub_articles = finnhub_news.get("articles", [])
        finnhub_text = ""
        for i, article in enumerate(finnhub_articles[:3], 1):
            finnhub_text += f"{i}. {article.get('title', 'N/A')} - {article.get('source', 'N/A')} - Sentiment: {article.get('sentiment', 'N/A')}\n"
        
        # Format web news
        web_articles = web_news.get("articles", [])
        web_text = ""
        for i, article in enumerate(web_articles[:3], 1):
            web_text += f"{i}. {article.get('title', 'N/A')} - {article.get('source', 'N/A')} - Sentiment: {article.get('sentiment', 'N/A')}\n"
        
        # Format sentiment summary
        sentiment_counts = news_summary.get("sentiment_counts", {})
        sentiment_percentages = news_summary.get("sentiment_percentages", {})
        overall_sentiment = news_summary.get("overall_sentiment", "N/A")
        
        prompt = f"""
You are a financial news analyst. Analyze the following news data for {ticker} and provide insights about market sentiment and potential impacts.

Ticker: {ticker}

Finnhub News (Top 3) (Source: Finnhub API):
{finnhub_text if finnhub_text else "No Finnhub news available"}

Web News (Top 3) (Source: Google Custom Search):
{web_text if web_text else "No web news available"}

News Sentiment Analysis:
- Positive: {sentiment_counts.get('positive', 0)} articles ({sentiment_percentages.get('positive', 0):.1f}%)
- Negative: {sentiment_counts.get('negative', 0)} articles ({sentiment_percentages.get('negative', 0):.1f}%)
- Neutral: {sentiment_counts.get('neutral', 0)} articles ({sentiment_percentages.get('neutral', 0):.1f}%)
- Overall Sentiment: {overall_sentiment}

Please provide a detailed analysis covering:
1. Key news themes and their implications for {ticker}
2. Market sentiment analysis and trends
3. Economic environment assessment
4. Potential catalysts or risks
5. Impact on investment thesis
6. Short-term and medium-term outlook based on news flow

IMPORTANT CITATION REQUIREMENTS:
- Cite the data source for EVERY news article, statistic, or sentiment metric you mention
- Use format: "According to Finnhub API, article X shows..." or "Google Custom Search found Y articles with..."
- Include specific article titles and sources when referencing news
- If data is not available, clearly state "No data available from [source]"
- Be specific about which API provided which piece of information

Examples of proper citations:
- "According to Finnhub API, 50% of news articles show positive sentiment"
- "Google Custom Search found 3 recent articles about {ticker} earnings"
- "Article 'UNH Reports Strong Q4' from MarketWatch shows positive sentiment (Finnhub API)"
- "Web search results indicate growing interest in {ticker} stock (Google Custom Search)"

Write in clear, professional language suitable for investment decision-making.

Additional Notes:
{web_news.get('note', 'No additional notes')}
"""
        return prompt 