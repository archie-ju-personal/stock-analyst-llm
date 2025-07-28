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
import requests
from bs4 import BeautifulSoup
from langchain_tavily import TavilySearch
import pytz
from urllib.parse import urlparse

class NewsAgent(BaseAgent):
    """Agent responsible for collecting and analyzing news data."""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1):
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
        """Perform a web search using Tavily and return results."""
        try:
            tavily_search = TavilySearch(max_results=5)
            search_response = tavily_search.invoke(query)
            
            # Tavily returns a dictionary with 'results' key containing the actual search results
            if not isinstance(search_response, dict) or 'results' not in search_response:
                print(f"Unexpected Tavily response format: {type(search_response)}")
                return []
            
            results = search_response['results']
            formatted_results = []
            
            for i, result in enumerate(results):
                if isinstance(result, dict):
                    # Extract structured data from Tavily result
                    title = result.get('title', f"Search Result {i+1}")
                    content = result.get('content', '')
                    url = result.get('url', '')
                    
                    # Determine source from URL using urlparse
                    try:
                        parsed_url = urlparse(url)
                        source = parsed_url.netloc.replace('www.', '')
                    except:
                        source = 'Unknown'
                    
                    # Create a meaningful description from content
                    description = content[:200] + "..." if len(content) > 200 else content
                    
                    formatted_results.append({
                        "title": title,
                        "description": description,
                        "source": source,
                        "url": url if url and url.startswith('http') else "",
                        "sentiment": self._analyze_sentiment(content),
                        "relevance_score": result.get('score', 0.8)
                    })
                else:
                    # Handle non-dict results
                    result_str = str(result)
                    
                    formatted_results.append({
                        "title": f"Search Result {i+1}",
                        "description": result_str[:200] + "..." if len(result_str) > 200 else result_str,
                        "source": "Tavily Search",
                        "url": "",
                        "sentiment": self._analyze_sentiment(result_str),
                        "relevance_score": 0.8
                    })
            
            return formatted_results
        except Exception as e:
            # Fallback for Tavily search
            print(f"Tavily search failed: {e}. No fallback implemented.")
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
        """
        Simple LLM-based sentiment analysis.
        Uses the language model to analyze sentiment and return a score.
        """
        if not text or not text.strip():
            return "neutral"
        
        # Create a simple prompt for sentiment analysis
        prompt = f"""
        Analyze the sentiment of the following text and return ONLY one of these three options: "positive", "negative", or "neutral".
        
        Text: {text[:1000]}  # Limit to first 1000 characters
        
        Consider financial context - words like "earnings beat", "growth", "profit" are positive. Words like "loss", "decline", "miss" are negative.
        
        Response (only one word):
        """
        
        try:
            # Use the LLM to get sentiment
            response = self.llm.invoke(prompt)
            # Extract content from AIMessage object
            sentiment = response.content.strip().lower()
            
            # Validate the response
            if sentiment in ["positive", "negative", "neutral"]:
                return sentiment
            else:
                # Fallback to neutral if response is unexpected
                return "neutral"
                
        except Exception as e:
            print(f"LLM sentiment analysis error: {e}")
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

Web News (Top 3) (Source: Tavily Search):
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