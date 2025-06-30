"""
Bull Agent - Advocates for investment, highlighting growth potential and positive indicators.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent

class BullAgent(BaseAgent):
    """Agent that takes a bullish stance on the stock."""
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.3):
        super().__init__(model_name, temperature)
    
    def collect_data(self, ticker: str) -> Dict[str, Any]:
        """
        Collect data for the given ticker.
        Note: Bull agents don't collect data directly, they work with pre-collected data.
        
        Args:
            ticker: The stock ticker symbol
            
        Returns:
            Empty dictionary since bull agents don't collect data
        """
        return {"ticker": ticker, "note": "Bull agents work with pre-collected data"}
    
    def analyze_data(self, data: Dict[str, Any]) -> str:
        """
        Analyze the collected data and return insights.
        Note: Bull agents analyze data through debate arguments.
        
        Args:
            data: The collected data
            
        Returns:
            String containing the analysis and insights
        """
        return "Bull agents analyze data through debate arguments"
    
    def create_argument(self, data_reports: Dict[str, str], debate_history: List[str] = None, bear_argument: str = None) -> str:
        """
        Create a bullish argument based on the data reports.
        
        Args:
            data_reports: Dictionary containing reports from all data collection agents
            debate_history: List of previous debate exchanges
            bear_argument: The most recent bear argument to counter
            
        Returns:
            String containing the bullish argument
        """
        try:
            # Prepare the analysis prompt
            analysis_prompt = self._create_bull_prompt(data_reports, debate_history, bear_argument)
            
            # Get LLM response
            response = self.llm.invoke(analysis_prompt)
            
            return response.content
            
        except Exception as e:
            return f"Error creating bull argument: {str(e)}"
    
    def _create_bull_prompt(self, data_reports: Dict[str, str], debate_history: List[str], bear_argument: str) -> str:
        """Create the prompt for the bull argument."""
        
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
        
        # Format bear argument to counter
        bear_text = ""
        if bear_argument:
            bear_text = f"\n\nMost Recent Bear Argument to Counter:\n{bear_argument}"
        
        prompt = f"""
You are a Bull Analyst advocating for investing in the stock. Your task is to build a strong, evidence-based case emphasizing growth potential, competitive advantages, and positive market indicators. Leverage the provided research and data to address concerns and counter bearish arguments effectively.

Key points to focus on:
- Growth Potential: Highlight the company's market opportunities, revenue projections, and scalability
- Competitive Advantages: Emphasize factors like unique products, strong branding, or dominant market positioning
- Positive Indicators: Use financial health, industry trends, and recent positive news as evidence
- Bear Counterpoints: Critically analyze the bear argument with specific data and sound reasoning, addressing concerns thoroughly and showing why the bull perspective holds stronger merit
- Engagement: Present your argument in a conversational style, engaging directly with the bear analyst's points and debating effectively rather than just listing data

Resources available:

Financial Market Analysis:
{financial_report}

Social Media Sentiment Analysis:
{social_report}

News and Market Analysis:
{news_report}

Fundamental Analysis:
{fundamental_report}{history_text}{bear_text}

Use this information to deliver a compelling bull argument, refute the bear's concerns, and engage in a dynamic debate that demonstrates the strengths of the bull position. 

Structure your response as:
1. Executive Summary of Bull Case
2. Key Growth Drivers and Opportunities
3. Financial Strength and Valuation Support
4. Competitive Advantages and Market Position
5. Counter-Arguments to Bear Concerns
6. Risk Mitigation and Upside Potential
7. Investment Recommendation

Write in clear, professional language suitable for investment decision-making. Be specific with data points and provide actionable insights.
"""
        return prompt
    
    def summarize_debate(self, debate_history: List[str], final_position: str) -> str:
        """
        Summarize the bull's final position after the debate.
        
        Args:
            debate_history: Complete history of the debate
            final_position: The bull's final position
            
        Returns:
            String containing the bull's summary
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
You are a Bull Analyst summarizing your final position after a comprehensive debate about a stock investment.

{history_text}

Your Final Position:
{final_position}

Please provide a concise summary of your bull case covering:
1. Key reasons for bullish stance
2. Most compelling evidence from the debate
3. Risk factors you acknowledge but believe are manageable
4. Investment recommendation and confidence level
5. Key metrics or events to monitor

Write in clear, professional language suitable for investment decision-making.
"""
            
            response = self.llm.invoke(summary_prompt)
            return response.content
            
        except Exception as e:
            return f"Error creating bull summary: {str(e)}" 