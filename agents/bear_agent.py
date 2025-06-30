"""
Bear Agent - Presents risks and challenges, emphasizing potential downsides.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent

class BearAgent(BaseAgent):
    """Agent that takes a bearish stance on the stock."""
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.3):
        super().__init__(model_name, temperature)
    
    def collect_data(self, ticker: str) -> Dict[str, Any]:
        """
        Collect data for the given ticker.
        Note: Bear agents don't collect data directly, they work with pre-collected data.
        
        Args:
            ticker: The stock ticker symbol
            
        Returns:
            Empty dictionary since bear agents don't collect data
        """
        return {"ticker": ticker, "note": "Bear agents work with pre-collected data"}
    
    def analyze_data(self, data: Dict[str, Any]) -> str:
        """
        Analyze the collected data and return insights.
        Note: Bear agents analyze data through debate arguments.
        
        Args:
            data: The collected data
            
        Returns:
            String containing the analysis and insights
        """
        return "Bear agents analyze data through debate arguments"
    
    def create_argument(self, data_reports: Dict[str, str], debate_history: List[str] = None, bull_argument: str = None) -> str:
        """
        Create a bearish argument based on the data reports.
        
        Args:
            data_reports: Dictionary containing reports from all data collection agents
            debate_history: List of previous debate exchanges
            bull_argument: The most recent bull argument to counter
            
        Returns:
            String containing the bearish argument
        """
        try:
            # Prepare the analysis prompt
            analysis_prompt = self._create_bear_prompt(data_reports, debate_history, bull_argument)
            
            # Get LLM response
            response = self.llm.invoke(analysis_prompt)
            
            return response.content
            
        except Exception as e:
            return f"Error creating bear argument: {str(e)}"
    
    def _create_bear_prompt(self, data_reports: Dict[str, str], debate_history: List[str], bull_argument: str) -> str:
        """Create the prompt for the bear argument."""
        
        # Extract reports
        financial_report = data_reports.get("financial_market", "No financial market data available")
        social_report = data_reports.get("social_media", "No social media data available")
        news_report = data_reports.get("news", "No news data available")
        fundamental_report = data_reports.get("fundamental", "No fundamental data available")
        
        # Format debate history
        history_text = ""
        if debate_history:
            history_text = "\n\nPrevious Debate History:\n"
            # Handle new structured format
            if isinstance(debate_history, list) and debate_history and isinstance(debate_history[0], dict):
                for i, entry in enumerate(debate_history[-6:], 1):  # Last 6 exchanges
                    history_text += f"{i}. {entry['agent']} Round {entry['round']}: {entry['argument'][:200]}...\n"
            else:
                # Handle old format
                for i, exchange in enumerate(debate_history[-6:], 1):  # Last 6 exchanges
                    history_text += f"{i}. {exchange}\n"
        
        # Format bull argument to counter
        bull_text = ""
        if bull_argument:
            bull_text = f"\n\nMost Recent Bull Argument to Counter:\n{bull_argument}"
        
        prompt = f"""
You are a Bear Analyst making the case against investing in the stock. Your goal is to present a well-reasoned argument emphasizing risks, challenges, and negative indicators. Leverage the provided research and data to highlight potential downsides and counter bullish arguments effectively.

Key points to focus on:
- Risks and Challenges: Highlight factors like market saturation, financial instability, or macroeconomic threats that could hinder the stock's performance
- Competitive Weaknesses: Emphasize vulnerabilities such as weaker market positioning, declining innovation, or threats from competitors
- Negative Indicators: Use evidence from financial data, market trends, or recent adverse news to support your position
- Bull Counterpoints: Critically analyze the bull argument with specific data and sound reasoning, exposing weaknesses or over-optimistic assumptions
- Engagement: Present your argument in a conversational style, directly engaging with the bull analyst's points and debating effectively rather than simply listing facts

Resources available:

Financial Market Analysis:
{financial_report}

Social Media Sentiment Analysis:
{social_report}

News and Market Analysis:
{news_report}

Fundamental Analysis:
{fundamental_report}{history_text}{bull_text}

Use this information to deliver a compelling bear argument, refute the bull's claims, and engage in a dynamic debate that demonstrates the risks and weaknesses of investing in the stock.

Structure your response as:
1. Executive Summary of Bear Case
2. Key Risk Factors and Challenges
3. Financial Weaknesses and Valuation Concerns
4. Competitive Threats and Market Vulnerabilities
5. Counter-Arguments to Bull Claims
6. Downside Scenarios and Worst-Case Outcomes
7. Investment Recommendation

Write in clear, professional language suitable for investment decision-making. Be specific with data points and provide actionable insights.
"""
        return prompt
    
    def summarize_debate(self, debate_history: List[str], final_position: str) -> str:
        """
        Summarize the bear's final position after the debate.
        
        Args:
            debate_history: Complete history of the debate
            final_position: The bear's final position
            
        Returns:
            String containing the bear's summary
        """
        try:
            # Format debate history for the prompt
            history_text = ""
            if debate_history:
                if isinstance(debate_history, list) and debate_history and isinstance(debate_history[0], dict):
                    # New structured format
                    history_text = "\nDebate History:\n"
                    for entry in debate_history:
                        history_text += f"{entry['agent']} Round {entry['round']}: {entry['argument'][:300]}...\n\n"
                else:
                    # Old format
                    history_text = "\nDebate History:\n" + "\n".join(debate_history) if debate_history else ""
            
            summary_prompt = f"""
You are a Bear Analyst summarizing your final position after a comprehensive debate about a stock investment.

{history_text}

Your Final Position:
{final_position}

Please provide a concise summary of your bear case covering:
1. Key reasons for bearish stance
2. Most compelling evidence from the debate
3. Positive factors you acknowledge but believe are outweighed by risks
4. Investment recommendation and confidence level
5. Key risk factors to monitor

Write in clear, professional language suitable for investment decision-making.
"""
            
            response = self.llm.invoke(summary_prompt)
            return response.content
            
        except Exception as e:
            return f"Error creating bear summary: {str(e)}" 