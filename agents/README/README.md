# Stock Analyst AI Agent

A multi-agent AI system for comprehensive stock analysis and investment decision making.

## Overview

This system uses four specialized data collection agents and two debate agents to provide thorough stock analysis:

### Data Collection Agents
1. **Financial Market Agent**: Analyzes stock price data, technical indicators, and market trends
2. **Social Media Agent**: Monitors sentiment from Twitter, Reddit, and other social platforms
3. **News Agent**: Gathers and analyzes recent news and macroeconomic indicators
4. **Fundamental Agent**: Examines company financials, earnings, and fundamental metrics

### Debate Agents
- **Bull Agent**: Advocates for investment, highlighting growth potential and positive indicators
- **Bear Agent**: Presents risks and challenges, emphasizing potential downsides

## Features

- Real-time data collection from multiple sources
- Multi-round debate between bull and bear perspectives
- Comprehensive analysis reports in plain language
- Configurable analysis depth and debate rounds
- Support for multiple data sources and APIs

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see `.env.example`)
4. Run the main script: `python main.py`

## Usage

```python
from stock_analyst import StockAnalyst

analyst = StockAnalyst()
report = analyst.analyze_stock("AAPL", debate_rounds=3)
print(report)
```

## Configuration

Create a `.env` file with your API keys:
```
OPENAI_API_KEY=your_openai_key
YAHOO_FINANCE_API_KEY=your_yahoo_key
NEWS_API_KEY=your_news_api_key
TWITTER_API_KEY=your_twitter_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key
```

## Disclaimer

This system is for educational and research purposes only. It is not intended as financial advice. Always conduct your own research and consult with financial professionals before making investment decisions. 