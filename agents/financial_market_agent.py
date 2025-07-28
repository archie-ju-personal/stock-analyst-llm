"""
Financial Market Agent - Collects and analyzes stock price data and technical indicators.
"""

import yfinance as yf
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import stockstats
from .base_agent import BaseAgent

class FinancialMarketAgent(BaseAgent):
    """Agent responsible for collecting and analyzing financial market data."""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        super().__init__(model_name, temperature)
    
    def collect_data(self, ticker: str) -> Dict[str, Any]:
        """
        Collect financial market data for the given ticker.
        
        Args:
            ticker: The stock ticker symbol
            
        Returns:
            Dictionary containing price data, technical indicators, and market metrics
        """
        try:
            # Get stock data
            stock = yf.Ticker(ticker)
            
            # Get historical data for the last 6 months
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            
            hist_data = stock.history(start=start_date, end=end_date)
            
            if hist_data.empty:
                return {"error": f"No data found for ticker {ticker}"}
            
            # Calculate technical indicators
            stockstats_data = self._calculate_technical_indicators(hist_data)
            
            # Get current market info
            info = stock.info
            
            # Get recent earnings data (Net Income from income statement)
            earnings = None
            try:
                income_stmt = stock.income_stmt
                if income_stmt is not None and not income_stmt.empty:
                    # Get the most recent Net Income
                    if 'Net Income' in income_stmt.columns:
                        earnings = income_stmt['Net Income'].iloc[-1]
                    elif 'Net Income Common Stockholders' in income_stmt.columns:
                        earnings = income_stmt['Net Income Common Stockholders'].iloc[-1]
            except Exception as e:
                print(f"Could not fetch earnings data: {e}")
            
            return {
                "ticker": ticker,
                "historical_data": hist_data,
                "technical_indicators": stockstats_data,
                "market_info": info,
                "earnings": earnings,
                "current_price": hist_data['Close'].iloc[-1] if not hist_data.empty else None,
                "price_change_1d": self._calculate_price_change(hist_data, 1),
                "price_change_5d": self._calculate_price_change(hist_data, 5),
                "price_change_30d": self._calculate_price_change(hist_data, 30),
                "volume_avg_30d": hist_data['Volume'].tail(30).mean() if len(hist_data) >= 30 else hist_data['Volume'].mean(),
                "volatility_30d": hist_data['Close'].tail(30).pct_change().std() * (252 ** 0.5) if len(hist_data) >= 30 else None
            }
            
        except Exception as e:
            return {"error": f"Error collecting financial data: {str(e)}"}
    
    def _calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators from price data."""
        try:
            # Create stockstats object
            stock = stockstats.StockDataFrame.retype(data)
            
            # Calculate various indicators
            indicators = {}
            
            # Moving averages
            if len(data) >= 50:
                indicators['sma_50'] = stock['close_50_sma'].iloc[-1]
            if len(data) >= 200:
                indicators['sma_200'] = stock['close_200_sma'].iloc[-1]
            
            # RSI
            if len(data) >= 14:
                indicators['rsi'] = stock['rsi_14'].iloc[-1]
            
            # MACD
            if len(data) >= 26:
                indicators['macd'] = stock['macd'].iloc[-1]
                indicators['macd_signal'] = stock['macds'].iloc[-1]
                indicators['macd_histogram'] = stock['macdh'].iloc[-1]
            
            # Bollinger Bands
            if len(data) >= 20:
                indicators['bollinger_upper'] = stock['boll_ub'].iloc[-1]
                indicators['bollinger_middle'] = stock['boll'].iloc[-1]
                indicators['bollinger_lower'] = stock['boll_lb'].iloc[-1]
            
            # ATR (Average True Range)
            if len(data) >= 14:
                indicators['atr'] = stock['atr'].iloc[-1]
            
            return indicators
            
        except Exception as e:
            return {"error": f"Error calculating technical indicators: {str(e)}"}
    
    def _calculate_price_change(self, data: pd.DataFrame, days: int) -> float:
        """Calculate price change over specified number of days."""
        if len(data) < days + 1:
            return None
        
        current_price = data['Close'].iloc[-1]
        past_price = data['Close'].iloc[-days-1]
        return ((current_price - past_price) / past_price) * 100
    
    def analyze_data(self, data: Dict[str, Any]) -> str:
        """
        Analyze the financial market data and provide insights.
        
        Args:
            data: The collected financial data
            
        Returns:
            String containing the analysis and insights
        """
        if "error" in data:
            return f"Error in financial market analysis: {data['error']}"
        
        # Prepare data for LLM analysis
        analysis_prompt = self._create_analysis_prompt(data)
        
        # Get LLM analysis
        response = self.llm.invoke(analysis_prompt)
        
        return response.content
    
    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create the analysis prompt for the LLM."""
        
        current_price = data.get('current_price', 'N/A')
        price_changes = {
            '1d': data.get('price_change_1d', 'N/A'),
            '5d': data.get('price_change_5d', 'N/A'),
            '30d': data.get('price_change_30d', 'N/A')
        }
        
        indicators = data.get('technical_indicators', {})
        market_info = data.get('market_info', {})
        
        prompt = f"""
You are a financial market analyst. Analyze the following stock data and provide a comprehensive market analysis report.

Stock: {data.get('ticker', 'N/A')}
Current Price: ${current_price} (Source: Yahoo Finance)

Price Changes (Source: Yahoo Finance):
- 1 Day: {price_changes['1d']}%
- 5 Days: {price_changes['5d']}%
- 30 Days: {price_changes['30d']}%

Technical Indicators (Source: Yahoo Finance):
{self._format_indicators(indicators)}

Market Information (Source: Yahoo Finance):
- Market Cap: {market_info.get('marketCap', 'N/A')}
- P/E Ratio: {market_info.get('trailingPE', 'N/A')}
- 52 Week High: {market_info.get('fiftyTwoWeekHigh', 'N/A')}
- 52 Week Low: {market_info.get('fiftyTwoWeekLow', 'N/A')}
- Volume (30-day avg): {market_info.get('averageVolume', 'N/A')}

Please provide a detailed analysis covering:
1. Current market position and trend
2. Technical analysis insights
3. Key support and resistance levels
4. Volume analysis
5. Risk assessment
6. Short-term and medium-term outlook

IMPORTANT CITATION REQUIREMENTS:
- Cite Yahoo Finance as the source for EVERY statistic, price, or metric you mention
- Use format: "According to Yahoo Finance, the current price is $X" or "Yahoo Finance reports a 1-day change of Y%"
- Include specific data points with their sources
- If data is not available, clearly state "No data available from Yahoo Finance"
- Be specific about which data came from which API call

Examples of proper citations:
- "According to Yahoo Finance, the current price is $309.11"
- "Yahoo Finance reports a 1-day price change of 2.14%"
- "The 50-day SMA stands at 342.98 (Yahoo Finance)"
- "RSI of 44.69 indicates neither overbought nor oversold conditions (Yahoo Finance)"

Write in clear, professional language suitable for investment decision-making.
"""
        return prompt
    
    def _format_indicators(self, indicators: Dict[str, Any]) -> str:
        """Format technical indicators for the prompt."""
        if not indicators:
            return "No technical indicators available"
        
        formatted = []
        for key, value in indicators.items():
            if value is not None:
                formatted.append(f"- {key}: {value:.4f}")
        
        return "\n".join(formatted) if formatted else "No technical indicators available" 