"""
Simple test script to verify the Stock Analyst AI Agent system components.
"""

import os
from dotenv import load_dotenv
from rich.console import Console

# Import our agents
from agents.financial_market_agent import FinancialMarketAgent
from agents.social_media_agent import SocialMediaAgent
from agents.news_agent import NewsAgent
from agents.fundamental_agent import FundamentalAgent

load_dotenv()

def test_agents():
    """Test individual agents to ensure they work correctly."""
    console = Console()
    
    console.print("[bold blue]Testing Stock Analyst AI Agent Components[/bold blue]\n")
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[bold red]Warning: OPENAI_API_KEY not found. Some tests may fail.[/bold red]\n")
    
    # Test ticker
    test_ticker = "AAPL"
    
    # Test Financial Market Agent
    console.print("[cyan]Testing Financial Market Agent...[/cyan]")
    try:
        financial_agent = FinancialMarketAgent()
        financial_data = financial_agent.collect_data(test_ticker)
        if "error" not in financial_data:
            console.print("✓ Financial Market Agent: Data collection successful")
            console.print(f"  - Current price: ${financial_data.get('current_price', 'N/A')}")
            console.print(f"  - 30-day change: {financial_data.get('price_change_30d', 'N/A')}%")
        else:
            console.print(f"✗ Financial Market Agent: {financial_data['error']}")
    except Exception as e:
        console.print(f"✗ Financial Market Agent: {str(e)}")
    
    # Test Social Media Agent
    console.print("\n[cyan]Testing Social Media Agent...[/cyan]")
    try:
        social_agent = SocialMediaAgent()
        social_data = social_agent.collect_data(test_ticker)
        if "error" not in social_data:
            console.print("✓ Social Media Agent: Data collection successful")
            sentiment = social_data.get("sentiment_summary", {}).get("overall_sentiment", "N/A")
            console.print(f"  - Overall sentiment: {sentiment}")
        else:
            console.print(f"✗ Social Media Agent: {social_data['error']}")
    except Exception as e:
        console.print(f"✗ Social Media Agent: {str(e)}")
    
    # Test News Agent
    console.print("\n[cyan]Testing News Agent...[/cyan]")
    try:
        news_agent = NewsAgent()
        news_data = news_agent.collect_data(test_ticker)
        if "error" not in news_data:
            console.print("✓ News Agent: Data collection successful")
            total_articles = news_data.get("news_summary", {}).get("total_articles", 0)
            console.print(f"  - Total articles: {total_articles}")
        else:
            console.print(f"✗ News Agent: {news_data['error']}")
    except Exception as e:
        console.print(f"✗ News Agent: {str(e)}")
    
    # Test Fundamental Agent
    console.print("\n[cyan]Testing Fundamental Agent...[/cyan]")
    try:
        fundamental_agent = FundamentalAgent()
        fundamental_data = fundamental_agent.collect_data(test_ticker)
        if "error" not in fundamental_data:
            console.print("✓ Fundamental Agent: Data collection successful")
            company_name = fundamental_data.get("company_info", {}).get("longName", "N/A")
            console.print(f"  - Company: {company_name}")
        else:
            console.print(f"✗ Fundamental Agent: {fundamental_data['error']}")
    except Exception as e:
        console.print(f"✗ Fundamental Agent: {str(e)}")
    
    console.print("\n[bold green]Component testing complete![/bold green]")

if __name__ == "__main__":
    test_agents() 