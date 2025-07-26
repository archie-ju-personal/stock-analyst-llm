"""
Stock Analyst - Main coordinator for the multi-agent stock analysis system.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agents import (
    FinancialMarketAgent,
    SocialMediaAgent,
    NewsAgent,
    FundamentalAgent,
    BullAgent,
    BearAgent
)

load_dotenv()

class StockAnalyst:
    """Main coordinator for the stock analysis system."""
    
    def __init__(self, model_name: str = "gpt-4", debug: bool = False):
        """
        Initialize the StockAnalyst system.
        
        Args:
            model_name: The OpenAI model to use for all agents
            debug: Whether to run in debug mode
        """
        self.console = Console()
        self.debug = debug
        self.model_name = model_name
        
        # Initialize LLM for executive summary generation
        from langchain_openai import ChatOpenAI
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        
        # Initialize all agents
        self.financial_agent = FinancialMarketAgent(model_name)
        self.social_agent = SocialMediaAgent(model_name)
        self.news_agent = NewsAgent(model_name)
        self.fundamental_agent = FundamentalAgent(model_name)
        self.bull_agent = BullAgent(model_name)
        self.bear_agent = BearAgent(model_name)
        
        # Data storage
        self.data_reports = {}
        self.debate_history = []
        
    def analyze_stock(self, ticker: str, debate_rounds: int = 3) -> Dict[str, Any]:
        """
        Perform comprehensive stock analysis with multi-agent debate.
        
        Args:
            ticker: The stock ticker symbol
            debate_rounds: Number of debate rounds between bull and bear agents
            
        Returns:
            Dictionary containing the complete analysis report
        """
        try:
            self.console.print(Panel(f"[bold blue]Starting Analysis for {ticker.upper()}[/bold blue]"))
            
            # Step 1: Collect data from all agents
            self._collect_data(ticker)
            
            # Step 2: Conduct debate between bull and bear agents
            self._conduct_debate(debate_rounds)
            
            # Step 3: Generate final summary
            final_report = self._generate_final_report(ticker)
            
            return final_report
            
        except Exception as e:
            error_msg = f"Error in stock analysis: {str(e)}"
            self.console.print(f"[bold red]{error_msg}[/bold red]")
            return {"error": error_msg}
    
    def _collect_data(self, ticker: str):
        """Collect data from all four data collection agents."""
        self.console.print("\n[bold green]Phase 1: Data Collection[/bold green]")
        
        # Data limitations notice
        self._display_data_sources()
        
        # Initialize storage for both raw and analyzed data
        self.raw_data = {}
        self.data_reports = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            # Financial Market Data
            task1 = progress.add_task("Collecting financial market data...", total=None)
            raw_financial = self.financial_agent.collect_data(ticker)
            self.raw_data["financial_market"] = raw_financial
            financial_report = self.financial_agent.analyze_data(raw_financial)
            self.data_reports["financial_market"] = financial_report
            progress.update(task1, description="✓ Financial market data collected")
            
            # Social Media Data
            task2 = progress.add_task("Collecting social media data...", total=None)
            raw_social = self.social_agent.collect_data(ticker)
            self.raw_data["social_media"] = raw_social
            social_report = self.social_agent.analyze_data(raw_social)
            self.data_reports["social_media"] = social_report
            progress.update(task2, description="✓ Social media data collected")
            
            # News Data
            task3 = progress.add_task("Collecting news data...", total=None)
            raw_news = self.news_agent.collect_data(ticker)
            self.raw_data["news"] = raw_news
            news_report = self.news_agent.analyze_data(raw_news)
            self.data_reports["news"] = news_report
            progress.update(task3, description="✓ News data collected")
            
            # Fundamental Data
            task4 = progress.add_task("Collecting fundamental data...", total=None)
            raw_fundamental = self.fundamental_agent.collect_data(ticker)
            self.raw_data["fundamental"] = raw_fundamental
            fundamental_report = self.fundamental_agent.analyze_data(raw_fundamental)
            self.data_reports["fundamental"] = fundamental_report
            progress.update(task4, description="✓ Fundamental data collected")
        
        if self.debug:
            self._print_data_summary()
    
    def _conduct_debate(self, rounds: int):
        """Conduct debate between bull and bear agents."""
        self.console.print(f"\n[bold green]Phase 2: Multi-Round Debate ({rounds} rounds)[/bold green]")
        
        for round_num in range(1, rounds + 1):
            self.console.print(f"\n[bold yellow]Round {round_num}[/bold yellow]")
            
            # Bull argument
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Bull agent creating argument...", total=None)
                bull_argument = self.bull_agent.create_argument(
                    self.data_reports,
                    self.debate_history,
                    self.debate_history[-1] if self.debate_history else None
                )
                progress.update(task, description="✓ Bull argument created")
            
            # Store complete bull argument
            self.debate_history.append({
                "round": round_num,
                "agent": "Bull",
                "argument": bull_argument
            })
            
            if self.debug:
                self.console.print(f"[cyan]Bull Argument (Round {round_num}):[/cyan]")
                self.console.print(Panel(bull_argument, title="Bull"))
            
            # Bear argument
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Bear agent creating argument...", total=None)
                bear_argument = self.bear_agent.create_argument(
                    self.data_reports,
                    self.debate_history,
                    bull_argument
                )
                progress.update(task, description="✓ Bear argument created")
            
            # Store complete bear argument
            self.debate_history.append({
                "round": round_num,
                "agent": "Bear", 
                "argument": bear_argument
            })
            
            if self.debug:
                self.console.print(f"[cyan]Bear Argument (Round {round_num}):[/cyan]")
                self.console.print(Panel(bear_argument, title="Bear"))
    
    def _generate_final_report(self, ticker: str) -> Dict[str, Any]:
        """Generate the final comprehensive report."""
        self.console.print("\n[bold green]Phase 3: Final Report Generation[/bold green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            # Generate final summaries from both agents
            task1 = progress.add_task("Generating bull summary...", total=None)
            
            # Get the last bull argument for summary
            last_bull_arg = ""
            for entry in reversed(self.debate_history):
                if isinstance(entry, dict) and entry['agent'] == 'Bull':
                    last_bull_arg = entry['argument']
                    break
            
            bull_summary = self.bull_agent.summarize_debate(
                self.debate_history,
                last_bull_arg
            )
            progress.update(task1, description="✓ Bull summary generated")
            
            task2 = progress.add_task("Generating bear summary...", total=None)
            
            # Get the last bear argument for summary
            last_bear_arg = ""
            for entry in reversed(self.debate_history):
                if isinstance(entry, dict) and entry['agent'] == 'Bear':
                    last_bear_arg = entry['argument']
                    break
            
            bear_summary = self.bear_agent.summarize_debate(
                self.debate_history,
                last_bear_arg
            )
            progress.update(task2, description="✓ Bear summary generated")
        
        # Create final report
        final_report = {
            "ticker": ticker,
            "analysis_date": datetime.now().isoformat(),
            "data_reports": self.data_reports,
            "raw_data": self.raw_data,
            "debate_history": self.debate_history,
            "bull_summary": bull_summary,
            "bear_summary": bear_summary,
            "executive_summary": self._create_executive_summary(ticker, bull_summary, bear_summary)
        }
        
        return final_report
    
    def _create_executive_summary(self, ticker: str, bull_summary: str, bear_summary: str) -> str:
        """Create an executive summary of the analysis."""
        summary_prompt = f"""
You are a senior investment analyst creating an executive summary of a comprehensive stock analysis.

Stock: {ticker}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Bull Case Summary:
{bull_summary}

Bear Case Summary:
{bear_summary}

Please create a comprehensive executive summary that includes:

### Overview
A brief overview of the analysis approach and methodology.

### Key Findings
Extract and synthesize the most important insights from both bull and bear cases. Focus on:
- Critical financial metrics and their implications
- Key competitive advantages or disadvantages
- Major growth drivers or risk factors
- Market sentiment and positioning

### Investment Recommendation
Based on the analysis, provide a clear BUY/HOLD/SELL recommendation with confidence level (HIGH/MEDIUM/LOW). Include:
- Specific recommendation with rationale
- Confidence level and reasoning
- Key factors that influenced the decision
- Time horizon considerations

### Risk Factors
List the primary risks identified in the analysis, including:
- Financial risks (debt, liquidity, etc.)
- Competitive risks
- Market risks
- Operational risks
- Specific metrics or events to monitor

Write in clear, professional language suitable for senior executives and investment committees. Be specific and actionable in your recommendations.
"""
        
        try:
            # Use LLM to generate the executive summary
            response = self.llm.invoke(summary_prompt)
            return response.content
        except Exception as e:
            # Fallback to a basic summary if LLM fails
            return f"""
LLM failed to generate executive summary.
"""
    
    def _print_data_summary(self):
        """Print a summary of collected data in debug mode."""
        self.console.print("\n[bold cyan]Data Collection Summary:[/bold cyan]")
        
        table = Table(title="Data Sources")
        table.add_column("Source", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Report Length", style="yellow")
        
        for source, report in self.data_reports.items():
            status = "✓ Collected" if report and not report.startswith("Error") else "✗ Error"
            length = f"{len(report)} chars" if report else "N/A"
            table.add_row(source.replace("_", " ").title(), status, length)
        
        self.console.print(table)
    
    def print_report(self, report: Dict[str, Any]):
        """Print the analysis report in a formatted way."""
        if "error" in report:
            self.console.print(f"[bold red]Error: {report['error']}[/bold red]")
            return
        
        # Print executive summary
        self.console.print(Panel(
            report["executive_summary"],
            title="[bold blue]Executive Summary[/bold blue]",
            border_style="blue"
        ))
        
        # Print bull and bear summaries
        self.console.print(Panel(
            report["bull_summary"],
            title="[bold green]Bull Case Summary[/bold green]",
            border_style="green"
        ))
        
        self.console.print(Panel(
            report["bear_summary"],
            title="[bold red]Bear Case Summary[/bold red]",
            border_style="red"
        ))
        
        # Print data reports if in debug mode
        if self.debug:
            for source, content in report["data_reports"].items():
                self.console.print(Panel(
                    content[:500] + "..." if len(content) > 500 else content,
                    title=f"[bold cyan]{source.replace('_', ' ').title()}[/bold cyan]",
                    border_style="cyan"
                ))
    
    def _check_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """Dynamically check which data sources are available."""
        sources = {}
        
        # Check Yahoo Finance (always available - no API key needed)
        sources["yahoo_finance"] = {
            "available": True,
            "status": "✓",
            "description": "Real-time financial data and ratios",
            "note": "Free tier available"
        }
        
        # Check Finnhub API
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        if finnhub_key:
            try:
                import finnhub
                client = finnhub.Client(api_key=finnhub_key)
                # Test API with a simple call
                test_result = client.company_profile2(symbol='AAPL')
                sources["finnhub_api"] = {
                    "available": True,
                    "status": "✓",
                    "description": "Real-time news and insider trading data",
                    "note": "API key configured and working"
                }
            except Exception as e:
                sources["finnhub_api"] = {
                    "available": False,
                    "status": "⚠️",
                    "description": "Real-time news and insider trading data",
                    "note": f"API key configured but test failed: {str(e)[:50]}..."
                }
        else:
            sources["finnhub_api"] = {
                "available": False,
                "status": "⚠️",
                "description": "Real-time news and insider trading data",
                "note": "FINNHUB_API_KEY not set"
            }
        
        # Check Google Custom Search API
        google_api_key = os.getenv("GOOGLE_API_KEY")
        google_cse_id = os.getenv("GOOGLE_CSE_ID")
        if google_api_key and google_cse_id:
            try:
                import requests
                # Test API with a simple search
                test_url = "https://www.googleapis.com/customsearch/v1"
                test_params = {
                    'key': google_api_key,
                    'cx': google_cse_id,
                    'q': 'test',
                    'num': 1
                }
                response = requests.get(test_url, params=test_params, timeout=5)
                if response.status_code == 200:
                    sources["google_search"] = {
                        "available": True,
                        "status": "✓",
                        "description": "Web search for news and social media",
                        "note": "API configured and working"
                    }
                else:
                    sources["google_search"] = {
                        "available": False,
                        "status": "⚠️",
                        "description": "Web search for news and social media",
                        "note": f"API test failed with status {response.status_code}"
                    }
            except Exception as e:
                sources["google_search"] = {
                    "available": False,
                    "status": "⚠️",
                    "description": "Web search for news and social media",
                    "note": f"API test failed: {str(e)[:50]}..."
                }
        else:
            sources["google_search"] = {
                "available": False,
                "status": "⚠️",
                "description": "Web search for news and social media",
                "note": "GOOGLE_API_KEY or GOOGLE_CSE_ID not set"
            }
        
        # Check for other potential sources (not implemented but could be)
        sources["bloomberg"] = {
            "available": False,
            "status": "❌",
            "description": "Professional financial data",
            "note": "Not implemented - requires paid subscription"
        }
        
        sources["reuters"] = {
            "available": False,
            "status": "❌",
            "description": "Professional news and financial data",
            "note": "Not implemented - requires paid subscription"
        }
        
        sources["paid_news_apis"] = {
            "available": False,
            "status": "❌",
            "description": "Premium news APIs (NewsAPI Pro, etc.)",
            "note": "Not implemented - requires paid subscription"
        }
        
        sources["social_media_apis"] = {
            "available": False,
            "status": "❌",
            "description": "Real-time social media APIs (Twitter, Reddit, etc.)",
            "note": "Not implemented - requires API access and rate limits"
        }
        
        return sources
    
    def _display_data_sources(self):
        """Display available data sources dynamically."""
        self.console.print("\n[bold yellow]Data Sources and Limitations:[/bold yellow]")
        
        sources = self._check_data_sources()
        
        for source_name, source_info in sources.items():
            status = source_info["status"]
            description = source_info["description"]
            note = source_info["note"]
            
            # Format the display
            if source_name == "yahoo_finance":
                display_name = "Yahoo Finance"
            elif source_name == "finnhub_api":
                display_name = "Finnhub API"
            elif source_name == "google_search":
                display_name = "Google Search"
            elif source_name == "bloomberg":
                display_name = "Bloomberg"
            elif source_name == "reuters":
                display_name = "Reuters"
            elif source_name == "paid_news_apis":
                display_name = "Paid News APIs"
            elif source_name == "social_media_apis":
                display_name = "Real-time Social Media APIs"
            else:
                display_name = source_name.replace("_", " ").title()
            
            self.console.print(f"{status} {display_name}: {description}")
            if note:
                self.console.print(f"   Note: {note}")
        
        # Summary note
        available_count = sum(1 for s in sources.values() if s["available"])
        total_count = len(sources)
        self.console.print(f"\nNote: {available_count}/{total_count} data sources available. Analysis quality depends on available sources.\n") 