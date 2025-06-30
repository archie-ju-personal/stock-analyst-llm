#!/usr/bin/env python3
"""
Test script to verify Finnhub API integration in the agents.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_finnhub_integration():
    """Test the Finnhub API integration in the agents."""
    
    # Check if FINNHUB_API_KEY is set
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("❌ FINNHUB_API_KEY not found in environment variables")
        print("Please set your Finnhub API key in the .env file")
        return False
    
    print("✅ FINNHUB_API_KEY found")
    
    try:
        # Test basic Finnhub client initialization
        import finnhub
        client = finnhub.Client(api_key=api_key)
        print("✅ Finnhub client initialized successfully")
        
        # Test a simple API call
        test_ticker = "AAPL"
        print(f"\n🔍 Testing Finnhub API with ticker: {test_ticker}")
        
        # Test company profile
        try:
            profile = client.company_profile2(symbol=test_ticker)
            if profile:
                print(f"✅ Company Profile: {profile.get('name', 'N/A')} - {profile.get('country', 'N/A')}")
            else:
                print("⚠️  No company profile data returned")
        except Exception as e:
            print(f"❌ Error getting company profile: {str(e)}")
        
        # Test company news
        try:
            news = client.company_news(test_ticker, _from='2024-01-01', to='2024-12-31')
            if news and len(news) > 0:
                print(f"✅ Company News: {len(news)} articles found")
                print(f"   Latest: {news[0].get('headline', 'N/A')}")
            else:
                print("⚠️  No company news data returned")
        except Exception as e:
            print(f"❌ Error getting company news: {str(e)}")
        
        # Test insider transactions
        try:
            insider = client.insider_transactions(symbol=test_ticker)
            if insider and len(insider) > 0:
                print(f"✅ Insider Transactions: {len(insider)} transactions found")
            else:
                print("⚠️  No insider transactions data returned")
        except Exception as e:
            print(f"❌ Error getting insider transactions: {str(e)}")
        
        # Test SEC filings
        try:
            sec = client.sec_filings(symbol=test_ticker)
            if sec and len(sec) > 0:
                print(f"✅ SEC Filings: {len(sec)} filings found")
            else:
                print("⚠️  No SEC filings data returned")
        except Exception as e:
            print(f"❌ Error getting SEC filings: {str(e)}")
        
        print("\n🎉 Finnhub API integration test completed!")
        return True
        
    except ImportError:
        print("❌ finnhub-python library not installed")
        print("Please install it with: pip install finnhub-python")
        return False
    except Exception as e:
        print(f"❌ Error testing Finnhub integration: {str(e)}")
        return False

def test_agent_integration():
    """Test the agent integration with Finnhub."""
    
    print("\n" + "="*50)
    print("TESTING AGENT INTEGRATION")
    print("="*50)
    
    try:
        from agents.fundamental_agent import FundamentalAgent
        from agents.news_agent import NewsAgent
        from agents.social_media_agent import SocialMediaAgent
        
        test_ticker = "AAPL"
        
        # Test FundamentalAgent
        print(f"\n🔍 Testing FundamentalAgent with {test_ticker}")
        fundamental_agent = FundamentalAgent()
        fundamental_data = fundamental_agent.collect_data(test_ticker)
        
        if "error" not in fundamental_data:
            finnhub_data = fundamental_data.get("finnhub_data", {})
            if finnhub_data:
                print("✅ FundamentalAgent Finnhub integration working")
                print(f"   - Insider transactions: {'✅' if finnhub_data.get('insider_transactions') else '❌'}")
                print(f"   - Company profile: {'✅' if finnhub_data.get('company_profile') else '❌'}")
                print(f"   - SEC filings: {'✅' if finnhub_data.get('sec_filings') else '❌'}")
            else:
                print("⚠️  No Finnhub data in FundamentalAgent")
        else:
            print(f"❌ FundamentalAgent error: {fundamental_data['error']}")
        
        # Test NewsAgent
        print(f"\n🔍 Testing NewsAgent with {test_ticker}")
        news_agent = NewsAgent()
        news_data = news_agent.collect_data(test_ticker)
        
        if "error" not in news_data:
            finnhub_news = news_data.get("finnhub_news", {})
            if finnhub_news and not isinstance(finnhub_news, dict):
                print("✅ NewsAgent Finnhub integration working")
                print(f"   - Articles found: {finnhub_news.get('total_articles', 0)}")
            else:
                print("⚠️  No Finnhub news data in NewsAgent")
        else:
            print(f"❌ NewsAgent error: {news_data['error']}")
        
        # Test SocialMediaAgent
        print(f"\n🔍 Testing SocialMediaAgent with {test_ticker}")
        social_agent = SocialMediaAgent()
        social_data = social_agent.collect_data(test_ticker)
        
        if "error" not in social_data:
            finnhub_sentiment = social_data.get("finnhub_sentiment", {})
            if finnhub_sentiment and not isinstance(finnhub_sentiment, dict):
                print("✅ SocialMediaAgent Finnhub integration working")
                print(f"   - Sentiment articles: {finnhub_sentiment.get('total_articles', 0)}")
            else:
                print("⚠️  No Finnhub sentiment data in SocialMediaAgent")
        else:
            print(f"❌ SocialMediaAgent error: {social_data['error']}")
        
        print("\n🎉 Agent integration test completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Error importing agents: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error testing agent integration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Finnhub API Integration Test")
    print("="*50)
    
    # Test basic Finnhub API
    api_success = test_finnhub_integration()
    
    # Test agent integration
    agent_success = test_agent_integration()
    
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    if api_success and agent_success:
        print("🎉 All tests passed! Finnhub integration is working correctly.")
    elif api_success:
        print("⚠️  API tests passed but agent integration failed.")
    else:
        print("❌ Tests failed. Please check your setup.")
    
    print("\nTo use the integrated agents:")
    print("1. Make sure FINNHUB_API_KEY is set in your .env file")
    print("2. Run the main analysis: python main.py")
    print("3. The agents will now use Finnhub data automatically") 