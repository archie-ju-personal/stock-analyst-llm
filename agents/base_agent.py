"""
Base agent class for all data collection and analysis agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class BaseAgent(ABC):
    """Base class for all agents in the stock analysis system."""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        """
        Initialize the base agent.
        
        Args:
            model_name: The OpenAI model to use
            temperature: The temperature for the LLM
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.name = self.__class__.__name__
    
    @abstractmethod
    def collect_data(self, ticker: str) -> Dict[str, Any]:
        """
        Collect data for the given ticker.
        
        Args:
            ticker: The stock ticker symbol
            
        Returns:
            Dictionary containing the collected data and analysis
        """
        pass
    
    @abstractmethod
    def analyze_data(self, data: Dict[str, Any]) -> str:
        """
        Analyze the collected data and return insights.
        
        Args:
            data: The collected data
            
        Returns:
            String containing the analysis and insights
        """
        pass
    
    def run(self, ticker: str) -> str:
        """
        Run the complete data collection and analysis pipeline.
        
        Args:
            ticker: The stock ticker symbol
            
        Returns:
            String containing the final analysis report
        """
        try:
            data = self.collect_data(ticker)
            analysis = self.analyze_data(data)
            return analysis
        except Exception as e:
            return f"Error in {self.name}: {str(e)}"
    
    def _format_report(self, title: str, content: str, key_points: list = None) -> str:
        """
        Format the analysis report with a consistent structure.
        
        Args:
            title: The report title
            content: The main content
            key_points: List of key points to highlight
            
        Returns:
            Formatted report string
        """
        report = f"# {title}\n\n{content}\n\n"
        
        if key_points:
            report += "## Key Points\n\n"
            for i, point in enumerate(key_points, 1):
                report += f"{i}. {point}\n"
            report += "\n"
        
        return report 