"""
LangGraph Stock Analyst - Main coordinator for the multi-agent stock analysis system using LangGraph.
"""

import os
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from agents import (
    FinancialMarketAgent,
    SocialMediaAgent,
    NewsAgent,
    FundamentalAgent,
    BullAgent,
    BearAgent
)

import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()


# Define the state for our graph
class AgentState(TypedDict):
    ticker: str
    debate_rounds: int
    data_reports: Dict[str, str]
    raw_data: Dict[str, Any]
    debate_history: List[Dict[str, Any]]
    bull_summary: Optional[str]
    bear_summary: Optional[str]
    executive_summary: Optional[str]
    error: Optional[str]


class LangGraphStockAnalyst:
    """Main coordinator for the stock analysis system using LangGraph."""

    def __init__(self, model_name: str = "gpt-4o-mini", debug: bool = False):
        """
        Initialize the LangGraphStockAnalyst system.

        Args:
            model_name: The OpenAI model to use for all agents
            debug: Whether to run in debug mode
        """
        self.console = Console()
        self.debug = debug
        self.model_name = model_name

        # Initialize LLM for executive summary generation
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)

        # Initialize all agents
        self.financial_agent = FinancialMarketAgent(model_name)
        self.social_agent = SocialMediaAgent(model_name)
        self.news_agent = NewsAgent(model_name)
        self.fundamental_agent = FundamentalAgent(model_name)
        self.bull_agent = BullAgent(model_name)
        self.bear_agent = BearAgent(model_name)

        # Build and compile the graph
        self.graph = self.build_graph()

    def build_graph(self):
        """Build the LangGraph StateGraph for the analysis workflow."""
        workflow = StateGraph(AgentState)

        # Nodes
        workflow.add_node("collect_data", self.collect_data_node)
        workflow.add_node("debate", self.debate_node)
        workflow.add_node("summarize", self.summarize_node)
        workflow.add_node("generate_executive_summary", self.generate_executive_summary_node)

        # Edges
        workflow.set_entry_point("collect_data")
        workflow.add_edge("collect_data", "debate")
        workflow.add_conditional_edges(
            "debate",
            self.continue_debate_condition,
            {
                "continue": "debate",
                "end": "summarize",
            },
        )
        workflow.add_edge("summarize", "generate_executive_summary")
        workflow.add_edge("generate_executive_summary", END)

        return workflow.compile()

    def collect_data_node(self, state: AgentState) -> AgentState:
        """
        Node to collect data from all four data collection agents in parallel.
        """
        self.console.print("\n[bold green]Phase 1: Data Collection[/bold green]")
        self._display_data_sources()
        
        ticker = state['ticker']
        data_reports = {}
        raw_data = {}

        agent_functions = {
            "financial_market": (self.financial_agent.collect_data, self.financial_agent.analyze_data),
            "social_media": (self.social_agent.collect_data, self.social_agent.analyze_data),
            "news": (self.news_agent.collect_data, self.news_agent.analyze_data),
            "fundamental": (self.fundamental_agent.collect_data, self.fundamental_agent.analyze_data),
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            with ThreadPoolExecutor(max_workers=len(agent_functions)) as executor:
                future_to_agent = {}
                for agent_name, (collect_func, analyze_func) in agent_functions.items():
                    task = progress.add_task(f"Collecting {agent_name.replace('_', ' ')} data...", total=None)
                    future = executor.submit(self._run_agent, collect_func, analyze_func, ticker)
                    future_to_agent[future] = (agent_name, task)

                for future in as_completed(future_to_agent):
                    agent_name, task = future_to_agent[future]
                    try:
                        raw, report = future.result()
                        raw_data[agent_name] = raw
                        data_reports[agent_name] = report
                        progress.update(task, description=f"✓ {agent_name.replace('_', ' ')} data collected", completed=1)
                    except Exception as e:
                        self.console.print(f"[bold red]Error in {agent_name} agent: {e}[/bold red]")
                        raw_data[agent_name] = {"error": str(e)}
                        data_reports[agent_name] = f"Error: {e}"
                        progress.update(task, description=f"✗ {agent_name.replace('_', ' ')} data collection failed", completed=1)

        if self.debug:
            self._print_data_summary(data_reports)
        
        return {
            **state,
            "data_reports": data_reports,
            "raw_data": raw_data,
        }

    def _run_agent(self, collect_func, analyze_func, ticker):
        raw_data = collect_func(ticker)
        if "error" in raw_data:
            return raw_data, f"Error: {raw_data['error']}"
        report = analyze_func(raw_data)
        return raw_data, report

    def _print_data_summary(self, data_reports: Dict[str, str]):
        """Print a summary of collected data in debug mode."""
        self.console.print("\n[bold cyan]Data Collection Summary:[/bold cyan]")
        
        table = Table(title="Data Sources")
        table.add_column("Source", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Report Length", style="yellow")
        
        for source, report in data_reports.items():
            status = "✓ Collected" if report and not report.startswith("Error") else "✗ Error"
            length = f"{len(report)} chars" if report else "N/A"
            table.add_row(source.replace("_", " ").title(), status, length)
        
        self.console.print(table)
    
    def _display_data_sources(self):
        # This is a simplified version. A more robust implementation might check APIs live.
        self.console.print("\n[bold yellow]Data Sources and Limitations:[/bold yellow]")
        sources = {
            "Yahoo Finance": {"available": True, "note": "Real-time financial data and ratios"},
            "Finnhub API": {"available": bool(os.getenv("FINNHUB_API_KEY")), "note": "Real-time news and insider trading data"},
            "Tavily Search": {"available": bool(os.getenv("TAVILY_API_KEY")), "note": "Web search for news and social media"}
        }
        for source, info in sources.items():
            status = "✓" if info["available"] else "⚠️"
            self.console.print(f"{status} {source}: {info['note']}")
        self.console.print("\nNote: Analysis quality depends on available data sources.\n")

    def analyze_stock(self, ticker: str, debate_rounds: int = 3) -> Dict[str, Any]:
        """
        Perform comprehensive stock analysis using the LangGraph workflow.

        Args:
            ticker: The stock ticker symbol
            debate_rounds: Number of debate rounds between bull and bear agents

        Returns:
            Dictionary containing the complete analysis report
        """
        initial_state: AgentState = {
            "ticker": ticker,
            "debate_rounds": debate_rounds,
            "data_reports": {},
            "raw_data": {},
            "debate_history": [],
            "bull_summary": None,
            "bear_summary": None,
            "executive_summary": None,
            "error": None
        }

        try:
            self.console.print(Panel(f"[bold blue]Starting Analysis for {ticker.upper()} with LangGraph[/bold blue]"))

            # Invoke the graph with the initial state
            final_state = self.graph.invoke(initial_state)

            if "error" in final_state and final_state["error"]:
                return {"error": final_state["error"]}

            # Construct the final report from the graph's final state
            report = {
                "ticker": final_state.get("ticker"),
                "analysis_date": datetime.now().isoformat(),
                "data_reports": final_state.get("data_reports"),
                "raw_data": final_state.get("raw_data"),
                "debate_history": final_state.get("debate_history"),
                "bull_summary": final_state.get("bull_summary"),
                "bear_summary": final_state.get("bear_summary"),
                "executive_summary": final_state.get("executive_summary")
            }
            return report

        except Exception as e:
            error_msg = f"Error in LangGraph stock analysis: {str(e)}"
            self.console.print(f"[bold red]{error_msg}[/bold red]")
            import traceback
            traceback.print_exc()
            return {"error": error_msg}

    def print_report(self, report: Dict[str, Any]):
        """Print the analysis report in a formatted way."""
        if "error" in report and report["error"]:
            self.console.print(f"[bold red]Error: {report['error']}[/bold red]")
            return
        
        if not any(report.values()):
            self.console.print("[bold yellow]Report is empty. Graph execution might be incomplete.[/bold yellow]")
            return

        # Print executive summary
        if report.get("executive_summary"):
            self.console.print(Panel(
                report["executive_summary"],
                title="[bold blue]Executive Summary[/bold blue]",
                border_style="blue"
            ))

        # Print bull and bear summaries
        if report.get("bull_summary"):
            self.console.print(Panel(
                report["bull_summary"],
                title="[bold green]Bull Case Summary[/bold green]",
                border_style="green"
            ))
        if report.get("bear_summary"):
            self.console.print(Panel(
                report["bear_summary"],
                title="[bold red]Bear Case Summary[/bold red]",
                border_style="red"
            ))

        # Print data reports if in debug mode
        if self.debug and report.get("data_reports"):
            for source, content in report["data_reports"].items():
                self.console.print(Panel(
                    content[:500] + "..." if len(content) > 500 else content,
                    title=f"[bold cyan]{source.replace('_', ' ').title()}[/bold cyan]",
                    border_style="cyan"
                )) 

    def debate_node(self, state: AgentState) -> AgentState:
        """
        Node to conduct one round of debate between the bull and bear agents.
        """
        if not state.get("debate_history"):
            self.console.print("\n[bold green]Phase 2: Multi-Round Debate[/bold green]")
        
        round_num = len(state.get("debate_history", [])) // 2 + 1
        self.console.print(f"\n[bold yellow]Round {round_num}[/bold yellow]")

        # Bull argument
        bull_argument = self.bull_agent.create_argument(
            state["data_reports"],
            state["debate_history"],
            state["debate_history"][-1]["argument"] if state["debate_history"] else None
        )
        new_history = state["debate_history"] + [{"round": round_num, "agent": "Bull", "argument": bull_argument}]
        
        if self.debug:
            self.console.print(f"[cyan]Bull Argument (Round {round_num}):[/cyan]")
            self.console.print(Panel(bull_argument, title="Bull"))

        # Bear argument
        bear_argument = self.bear_agent.create_argument(
            state["data_reports"],
            new_history,
            bull_argument
        )
        new_history.append({"round": round_num, "agent": "Bear", "argument": bear_argument})

        if self.debug:
            self.console.print(f"[cyan]Bear Argument (Round {round_num}):[/cyan]")
            self.console.print(Panel(bear_argument, title="Bear"))

        return {**state, "debate_history": new_history}

    def continue_debate_condition(self, state: AgentState) -> str:
        """
        Conditional edge to determine if the debate should continue.
        """
        num_rounds_completed = len(state.get("debate_history", [])) // 2
        if num_rounds_completed < state["debate_rounds"]:
            return "continue"
        return "end"

    def summarize_node(self, state: AgentState) -> AgentState:
        """
        Node to generate final summaries from both agents.
        """
        self.console.print("\n[bold green]Phase 3: Final Report Generation[/bold green]")
        
        last_bull_arg = ""
        for entry in reversed(state["debate_history"]):
            if entry['agent'] == 'Bull':
                last_bull_arg = entry['argument']
                break

        bull_summary = self.bull_agent.summarize_debate(state["debate_history"], last_bull_arg)

        last_bear_arg = ""
        for entry in reversed(state["debate_history"]):
            if entry['agent'] == 'Bear':
                last_bear_arg = entry['argument']
                break
        
        bear_summary = self.bear_agent.summarize_debate(state["debate_history"], last_bear_arg)

        return {**state, "bull_summary": bull_summary, "bear_summary": bear_summary}
    
    def generate_executive_summary_node(self, state: AgentState) -> AgentState:
        """
        Node to generate the final executive summary.
        """
        summary = self._create_executive_summary(
            state["ticker"],
            state["bull_summary"],
            state["bear_summary"]
        )
        return {**state, "executive_summary": summary}

    def _create_executive_summary(self, ticker: str, bull_summary: str, bear_summary: str) -> str:
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
            return f"LLM failed to generate executive summary: {e}" 