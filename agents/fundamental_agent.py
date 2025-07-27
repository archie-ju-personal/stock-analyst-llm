"""
Fundamental Agent - Examines company financials, earnings, and fundamental metrics.
"""

import yfinance as yf
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import os
import finnhub
from .base_agent import BaseAgent

class FundamentalAgent(BaseAgent):
    """Agent responsible for analyzing fundamental company data."""
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.1):
        super().__init__(model_name, temperature)
        # Initialize Finnhub client
        self.finnhub_client = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))
    
    def collect_data(self, ticker: str) -> Dict[str, Any]:
        """
        Collect fundamental data for the given ticker.
        
        Args:
            ticker: The stock ticker symbol
            
        Returns:
            Dictionary containing fundamental analysis data
        """
        try:
            # Get stock data
            stock = yf.Ticker(ticker)
            
            # Get company info
            info = stock.info
            
            # Get financial statements
            financials = self._get_financial_statements(stock)
            
            # Get earnings data
            earnings = self._get_earnings_data(stock)
            
            # Get analyst recommendations
            recommendations = self._get_analyst_recommendations(stock)
            
            # Get Finnhub data
            finnhub_data = self._get_finnhub_data(ticker)
            
            # Calculate key ratios
            ratios = self._calculate_financial_ratios(info, financials)
            
            return {
                "ticker": ticker,
                "company_info": info,
                "financial_statements": financials,
                "earnings_data": earnings,
                "analyst_recommendations": recommendations,
                "finnhub_data": finnhub_data,
                "financial_ratios": ratios,
                "fundamental_summary": {}
            }
            
        except Exception as e:
            return {"error": f"Error collecting fundamental data: {str(e)}"}
    
    def _get_financial_statements(self, stock: yf.Ticker) -> Dict[str, Any]:
        """Get financial statements data."""
        try:
            # Get balance sheet, income statement, and cash flow
            balance_sheet = stock.balance_sheet
            income_stmt = stock.income_stmt
            cash_flow = stock.cashflow
            
            return {
                "balance_sheet": balance_sheet.to_dict() if balance_sheet is not None else {},
                "income_statement": income_stmt.to_dict() if income_stmt is not None else {},
                "cash_flow": cash_flow.to_dict() if cash_flow is not None else {}
            }
            
        except Exception as e:
            return {"error": f"Error getting financial statements: {str(e)}"}
    
    def _get_earnings_data(self, stock: yf.Ticker) -> Dict[str, Any]:
        """Get earnings data."""
        try:
            # Use income statement instead of deprecated earnings
            income_stmt = stock.income_stmt
            calendar = stock.calendar
            
            # Extract Net Income from income statement
            earnings_data = {}
            if income_stmt is not None and not income_stmt.empty:
                if 'Net Income' in income_stmt.columns:
                    earnings_data = income_stmt['Net Income'].to_dict()
                elif 'Net Income Common Stockholders' in income_stmt.columns:
                    earnings_data = income_stmt['Net Income Common Stockholders'].to_dict()
            
            return {
                "earnings": earnings_data,
                "calendar": calendar.to_dict() if calendar is not None else {}
            }
            
        except Exception as e:
            return {"error": f"Error getting earnings data: {str(e)}"}
    
    def _get_analyst_recommendations(self, stock: yf.Ticker) -> Dict[str, Any]:
        """Get analyst recommendations."""
        try:
            recommendations = stock.recommendations
            
            if recommendations is not None and not recommendations.empty:
                # Calculate recommendation distribution
                rec_counts = recommendations['To Grade'].value_counts()
                total_recs = len(recommendations)
                
                return {
                    "recommendations": recommendations.to_dict(),
                    "distribution": rec_counts.to_dict(),
                    "total_recommendations": total_recs,
                    "latest_recommendations": recommendations.head(5).to_dict()
                }
            else:
                return {
                    "recommendations": {},
                    "distribution": {},
                    "total_recommendations": 0,
                    "latest_recommendations": {}
                }
                
        except Exception as e:
            return {"error": f"Error getting analyst recommendations: {str(e)}"}
    
    def _calculate_financial_ratios(self, info: Dict[str, Any], financials: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key financial ratios."""
        try:
            ratios = {}
            
            # Basic ratios from info
            ratios["pe_ratio"] = info.get("trailingPE", None)
            ratios["forward_pe"] = info.get("forwardPE", None)
            ratios["price_to_book"] = info.get("priceToBook", None)
            ratios["price_to_sales"] = info.get("priceToSalesTrailing12Months", None)
            ratios["debt_to_equity"] = info.get("debtToEquity", None)
            ratios["current_ratio"] = info.get("currentRatio", None)
            ratios["quick_ratio"] = info.get("quickRatio", None)
            ratios["return_on_equity"] = info.get("returnOnEquity", None)
            ratios["return_on_assets"] = info.get("returnOnAssets", None)
            ratios["profit_margin"] = info.get("profitMargins", None)
            ratios["operating_margin"] = info.get("operatingMargins", None)
            
            # Calculate additional ratios if financial data is available
            if financials.get("income_statement"):
                income_stmt = financials["income_statement"]
                if "Total Revenue" in income_stmt and "Net Income" in income_stmt:
                    try:
                        revenue = list(income_stmt["Total Revenue"].values())[0]
                        net_income = list(income_stmt["Net Income"].values())[0]
                        if revenue and net_income and revenue != 0:
                            ratios["net_margin"] = (net_income / revenue) * 100
                    except:
                        pass
            
            return ratios
            
        except Exception as e:
            return {"error": f"Error calculating financial ratios: {str(e)}"}
    
    def analyze_data(self, data: Dict[str, Any]) -> str:
        """
        Analyze the fundamental data and provide insights.
        
        Args:
            data: The collected fundamental data
            
        Returns:
            String containing the analysis and insights
        """
        if "error" in data:
            return f"Error in fundamental analysis: {data['error']}"
        
        # Prepare data for LLM analysis
        analysis_prompt = self._create_analysis_prompt(data)
        
        # Get LLM analysis
        response = self.llm.invoke(analysis_prompt)
        
        return response.content
    
    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create the analysis prompt for the LLM."""
        
        ticker = data.get("ticker", "N/A")
        company_info = data.get("company_info", {})
        financial_ratios = data.get("financial_ratios", {})
        earnings_data = data.get("earnings_data", {})
        analyst_recommendations = data.get("analyst_recommendations", {})
        finnhub_data = data.get("finnhub_data", {})
        
        # Format company information
        market_cap = company_info.get('marketCap')
        enterprise_value = company_info.get('enterpriseValue')
        
        # Format market cap and enterprise value properly
        market_cap_str = f"${market_cap:,.0f}" if market_cap else "N/A"
        enterprise_value_str = f"${enterprise_value:,.0f}" if enterprise_value else "N/A"
        
        company_text = f"""
Company: {company_info.get('longName', 'N/A')}
Sector: {company_info.get('sector', 'N/A')}
Industry: {company_info.get('industry', 'N/A')}
Market Cap: {market_cap_str}
Enterprise Value: {enterprise_value_str}
"""
        
        # Format financial ratios
        ratios_text = ""
        for key, value in financial_ratios.items():
            if value is not None:
                if isinstance(value, float):
                    ratios_text += f"- {key.replace('_', ' ').title()}: {value:.2f}\n"
                else:
                    ratios_text += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        # Format earnings data
        earnings_text = ""
        if earnings_data.get("earnings"):
            earnings = earnings_data["earnings"]
            if "Earnings" in earnings:
                earnings_text = "Recent Earnings:\n"
                for date, value in list(earnings["Earnings"].items())[:4]:  # Last 4 quarters
                    earnings_text += f"- {date}: ${value:,.2f}\n"
        
        # Format analyst recommendations
        rec_text = ""
        if analyst_recommendations.get("distribution"):
            rec_text = "Analyst Recommendations:\n"
            for grade, count in analyst_recommendations["distribution"].items():
                rec_text += f"- {grade}: {count} analysts\n"
        
        # Format Finnhub data
        finnhub_text = ""
        if finnhub_data:
            # Insider transactions
            if finnhub_data.get("insider_transactions") and not isinstance(finnhub_data["insider_transactions"], dict):
                insider_data = finnhub_data["insider_transactions"]
                if insider_data and len(insider_data) > 0:
                    finnhub_text += "Recent Insider Transactions:\n"
                    for transaction in insider_data[:5]:  # Last 5 transactions
                        finnhub_text += f"- {transaction.get('name', 'N/A')}: {transaction.get('change', 0)} shares at ${transaction.get('transactionPrice', 0)}\n"
                    finnhub_text += "\n"
            
            # Insider sentiment
            if finnhub_data.get("insider_sentiment") and not isinstance(finnhub_data["insider_sentiment"], dict):
                sentiment_data = finnhub_data["insider_sentiment"]
                if sentiment_data and len(sentiment_data) > 0:
                    finnhub_text += "Insider Sentiment Analysis:\n"
                    for sentiment in sentiment_data[:3]:  # Last 3 sentiment records
                        finnhub_text += f"- {sentiment.get('year', 'N/A')}-{sentiment.get('month', 'N/A')}: Change: {sentiment.get('change', 0)}, MSPR: {sentiment.get('mspr', 0)}\n"
                    finnhub_text += "\n"
            
            # Company profile
            if finnhub_data.get("company_profile") and not isinstance(finnhub_data["company_profile"], dict):
                profile = finnhub_data["company_profile"]
                if profile:
                    finnhub_text += f"Company Profile:\n"
                    finnhub_text += f"- Country: {profile.get('country', 'N/A')}\n"
                    finnhub_text += f"- Currency: {profile.get('currency', 'N/A')}\n"
                    finnhub_text += f"- Exchange: {profile.get('exchange', 'N/A')}\n"
                    finnhub_text += f"- IPO Date: {profile.get('ipo', 'N/A')}\n"
                    finnhub_text += f"- Market Cap: ${profile.get('marketCapitalization', 0):,.0f}\n"
                    finnhub_text += f"- Share Outstanding: {profile.get('shareOutstanding', 0):,.0f}\n"
                    finnhub_text += "\n"
            
            # SEC filings
            if finnhub_data.get("sec_filings") and not isinstance(finnhub_data["sec_filings"], dict):
                sec_data = finnhub_data["sec_filings"]
                if sec_data and len(sec_data) > 0:
                    finnhub_text += "Recent SEC Filings:\n"
                    for filing in sec_data[:3]:  # Last 3 filings
                        finnhub_text += f"- {filing.get('form', 'N/A')}: {filing.get('filingDate', 'N/A')} - {filing.get('description', 'N/A')}\n"
                    finnhub_text += "\n"
        
        prompt = f"""
You are a fundamental analyst. Analyze the following fundamental data for {ticker} and provide comprehensive insights about the company's financial health and investment potential.

Ticker: {ticker}

Company Information (Source: Yahoo Finance):
{company_text}

Financial Ratios (Source: Yahoo Finance):
{ratios_text if ratios_text else "No financial ratios available"}

Earnings Data (Source: Yahoo Finance):
{earnings_text if earnings_text else "No earnings data available"}

Analyst Recommendations (Source: Yahoo Finance):
{rec_text if rec_text else "No analyst recommendations available"}

Additional Finnhub Data (Source: Finnhub API):
{finnhub_text if finnhub_text else "No additional Finnhub data available"}

Please provide a detailed analysis covering:
1. Company overview and business model assessment
2. Financial health and stability analysis
3. Valuation metrics and comparison to peers
4. Growth prospects and earnings quality
5. Risk factors and red flags
6. Investment attractiveness based on fundamentals
7. Key competitive advantages or disadvantages
8. Long-term investment thesis
9. Insider trading patterns and implications (if available)
10. Recent SEC filings and regulatory compliance (if available)

IMPORTANT CITATION REQUIREMENTS:
- Cite the data source for EVERY statistic, ratio, or metric you mention
- Use format: "According to Yahoo Finance, the P/E ratio is X" or "Finnhub API reports Y insider transactions"
- Include specific URLs or data timestamps when available
- If data is not available, clearly state "No data available from [source]"
- Be specific about which API provided which piece of information

Examples of proper citations:
- "According to Yahoo Finance, UNH's current P/E ratio is 12.94"
- "Yahoo Finance reports a debt-to-equity ratio of 77.28"
- "Finnhub API shows X insider transactions in the last 30 days"
- "Market capitalization of $280.4 billion (Yahoo Finance)"

Write in clear, professional language suitable for investment decision-making.
"""
        return prompt
    
    def _get_finnhub_data(self, ticker: str) -> Dict[str, Any]:
        """Get additional data from Finnhub API."""
        try:
            finnhub_data = {}
            
            # Get insider transactions (last 30 days)
            try:
                insider_transactions = self.finnhub_client.stock_insider_transactions(symbol=ticker)
                finnhub_data["insider_transactions"] = insider_transactions
            except Exception as e:
                finnhub_data["insider_transactions"] = {"error": f"Error getting insider transactions: {str(e)}"}
            
            # Get company basic financials
            try:
                company_financials = self.finnhub_client.company_basic_financials(symbol=ticker)
                finnhub_data["company_financials"] = company_financials
            except Exception as e:
                finnhub_data["company_financials"] = {"error": f"Error getting company financials: {str(e)}"}
            
            # Get company earnings
            try:
                company_earnings = self.finnhub_client.company_earnings(symbol=ticker)
                finnhub_data["company_earnings"] = company_earnings
            except Exception as e:
                finnhub_data["company_earnings"] = {"error": f"Error getting company earnings: {str(e)}"}
            
            # Get company profile
            try:
                company_profile = self.finnhub_client.company_profile2(symbol=ticker)
                finnhub_data["company_profile"] = company_profile
            except Exception as e:
                finnhub_data["company_profile"] = {"error": f"Error getting company profile: {str(e)}"}
            
            # Get SEC filings using the correct method name
            try:
                sec_filings = self.finnhub_client.filings(symbol=ticker)
                finnhub_data["sec_filings"] = sec_filings
            except Exception as e:
                finnhub_data["sec_filings"] = {"error": f"Error getting SEC filings: {str(e)}"}
            
            # Get insider sentiment
            try:
                insider_sentiment = self.finnhub_client.stock_insider_sentiment(symbol=ticker)
                finnhub_data["insider_sentiment"] = insider_sentiment
            except Exception as e:
                finnhub_data["insider_sentiment"] = {"error": f"Error getting insider sentiment: {str(e)}"}
            
            return finnhub_data
            
        except Exception as e:
            return {"error": f"Error getting Finnhub data: {str(e)}"} 