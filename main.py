"""
Main script for the Stock Analyst AI Agent system.
"""

import os
import sys
import textwrap
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
import json
import pandas as pd
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
import numpy as np
import datetime
import decimal

from stock_analyst import StockAnalyst

load_dotenv()

def convert_to_serializable(obj):
    """Convert non-JSON serializable objects to readable formats."""
    if isinstance(obj, pd.DataFrame):
        return {
            "type": "DataFrame",
            "shape": obj.shape,
            "columns": obj.columns.tolist(),
            "data": obj.to_dict('records'),
            "dtypes": {str(k): str(v) for k, v in obj.dtypes.items()}
        }
    elif isinstance(obj, pd.Series):
        return {
            "type": "Series",
            "name": obj.name,
            "dtype": str(obj.dtype),
            "data": obj.to_dict()
        }
    elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    elif isinstance(obj, (pd.Categorical,)):
        return obj.tolist()
    elif isinstance(obj, (pd.Index, pd.MultiIndex)):
        return obj.tolist()
    elif hasattr(obj, 'name') and 'DType' in obj.__class__.__name__:
        # Handles pandas extension dtypes like Float64DType, Int64DType, etc.
        return str(obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.datetime64,)):
        return str(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, (set, frozenset)):
        return list(obj)
    elif isinstance(obj, (bytes, bytearray)):
        return obj.decode(errors='replace')
    elif isinstance(obj, complex):
        return {'real': obj.real, 'imag': obj.imag}
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)

def serialize_dict_with_timestamps(obj):
    """Recursively serialize a dictionary, converting non-string keys to strings."""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            # Convert all non-string keys to strings
            if not isinstance(key, (str, int, float, bool, type(None))):
                key = str(key)
            result[key] = serialize_dict_with_timestamps(value)
        return result
    elif isinstance(obj, list):
        return [serialize_dict_with_timestamps(item) for item in obj]
    else:
        return convert_to_serializable(obj)

def wrap_text(text, width=150):
    """Wrap text to specified width while preserving formatting."""
    if not text:
        return ""
    
    lines = text.split('\n')
    wrapped_lines = []
    
    for line in lines:
        if len(line) <= width:
            wrapped_lines.append(line)
        else:
            # Simple word wrapping
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line + " " + word) <= width:
                    current_line += (" " + word) if current_line else word
                else:
                    if current_line:
                        wrapped_lines.append(current_line)
                    current_line = word
            if current_line:
                wrapped_lines.append(current_line)
    
    return '\n'.join(wrapped_lines)

def save_markdown_report(report, ticker, filename_base):
    """Save a Markdown version of the analysis report."""
    md_filename = filename_base + ".md"
    
    # Save raw data to separate files
    save_raw_data_files(report, ticker, filename_base)
    
    with open(md_filename, 'w') as f:
        f.write(f"# Stock Analysis Report for **{ticker}**\n\n")
        f.write(f"**Analysis Date:** {report['analysis_date']}\n\n")
        
        # Executive Summary (Level 2)
        f.write("## Executive Summary\n\n")
        
        # Process executive summary to ensure proper title hierarchy
        executive_summary = report['executive_summary'].strip()
        # Convert any H2 titles (##) to H3 (###) within the executive summary
        executive_summary = executive_summary.replace('\n## ', '\n### ')
        f.write(executive_summary + "\n\n")
        
        # Bull Case Summary (Level 2)
        f.write("## Bull Case Summary\n\n")
        f.write(report['bull_summary'].strip() + "\n\n")
        
        # Bear Case Summary (Level 2)
        f.write("## Bear Case Summary\n\n")
        f.write(report['bear_summary'].strip() + "\n\n")
        
        # Data Input to Debate Agents (Level 2) - renamed from "Raw Data Collection"
        f.write("## Data Input to Debate Agents\n\n")
        f.write("The following data was collected and fed into the bull and bear agents for their debate:\n\n")
        
        # Financial Market Data (Level 3)
        f.write("### Financial Market Data\n\n")
        f.write(report['data_reports']['financial_market'].strip() + "\n\n")
        
        # Social Media Data (Level 3)
        f.write("### Social Media Data\n\n")
        f.write(report['data_reports']['social_media'].strip() + "\n\n")
        
        # News Data (Level 3)
        f.write("### News Data\n\n")
        f.write(report['data_reports']['news'].strip() + "\n\n")
        
        # Fundamental Data (Level 3)
        f.write("### Fundamental Data\n\n")
        f.write(report['data_reports']['fundamental'].strip() + "\n\n")
        
        # Debate History (Level 2)
        f.write("## Debate History\n\n")
        f.write("\n---\n\n")
        
        # Process debate history with proper formatting
        for i, entry in enumerate(report['debate_history'], 1):
            if isinstance(entry, dict):
                round_num = entry.get('round', i)
                agent = entry.get('agent', 'Unknown')
                argument = entry.get('argument', '')
                
                f.write(f"### Round {round_num}\n\n")
                f.write(f"**{agent} Argument:**\n\n")
                f.write(argument.strip() + "\n\n")
    
    return md_filename

def save_raw_data_files(report, ticker, filename_base):
    """Save raw data from each agent to separate files."""
    raw_data_dir = "raw_data"
    os.makedirs(raw_data_dir, exist_ok=True)
    
    # Create timestamp for file naming
    timestamp = report['analysis_date'][:10]  # YYYY-MM-DD
    
    # Get raw data from the report
    raw_data = report.get('raw_data', {})
    
    # Save financial market raw data
    financial_filename = os.path.join(raw_data_dir, f"{ticker}_financial_market_raw_{timestamp}.md")
    with open(financial_filename, 'w') as f:
        f.write(f"# Raw Financial Market Data for {ticker}\n\n")
        f.write(f"**Collection Date:** {report['analysis_date']}\n\n")
        f.write("## Data Source: Yahoo Finance\n\n")
        f.write("### Raw Market Data\n\n")
        # Save the actual raw data structure
        f.write("```json\n")
        serialized_data = serialize_dict_with_timestamps(raw_data.get('financial_market', {}))
        f.write(json.dumps(serialized_data, indent=2))
        f.write("\n```\n\n")
        f.write("### Data Collection Notes\n\n")
        f.write("- Source: Yahoo Finance API\n")
        f.write("- Data includes: Current price, price changes, technical indicators, volume, volatility\n")
        f.write("- All data is real-time and verifiable\n")
    
    # Save social media raw data
    social_filename = os.path.join(raw_data_dir, f"{ticker}_social_media_raw_{timestamp}.md")
    with open(social_filename, 'w') as f:
        f.write(f"# Raw Social Media Data for {ticker}\n\n")
        f.write(f"**Collection Date:** {report['analysis_date']}\n\n")
        f.write("## Data Sources: Finnhub API, Google Custom Search\n\n")
        f.write("### Raw Sentiment Data\n\n")
        # Save the actual raw data structure
        f.write("```json\n")
        serialized_data = serialize_dict_with_timestamps(raw_data.get('social_media', {}))
        f.write(json.dumps(serialized_data, indent=2))
        f.write("\n```\n\n")
        f.write("### Data Collection Notes\n\n")
        f.write("- Primary Source: Finnhub API (news sentiment analysis)\n")
        f.write("- Secondary Source: Google Custom Search (social media discussions)\n")
        f.write("- Sentiment analysis performed on news articles and web content\n")
        f.write("- All data is real-time and verifiable\n")
    
    # Save news raw data
    news_filename = os.path.join(raw_data_dir, f"{ticker}_news_raw_{timestamp}.md")
    with open(news_filename, 'w') as f:
        f.write(f"# Raw News Data for {ticker}\n\n")
        f.write(f"**Collection Date:** {report['analysis_date']}\n\n")
        f.write("## Data Sources: Finnhub API, Google Custom Search\n\n")
        f.write("### Raw News Articles\n\n")
        # Save the actual raw data structure
        f.write("```json\n")
        serialized_data = serialize_dict_with_timestamps(raw_data.get('news', {}))
        f.write(json.dumps(serialized_data, indent=2))
        f.write("\n```\n\n")
        f.write("### Data Collection Notes\n\n")
        f.write("- Primary Source: Finnhub API (company-specific news)\n")
        f.write("- Secondary Source: Google Custom Search (recent news articles)\n")
        f.write("- News filtered for last 30 days (Finnhub) and last 7 days (Google)\n")
        f.write("- All data is real-time and verifiable\n")
    
    # Save fundamental raw data
    fundamental_filename = os.path.join(raw_data_dir, f"{ticker}_fundamental_raw_{timestamp}.md")
    with open(fundamental_filename, 'w') as f:
        f.write(f"# Raw Fundamental Data for {ticker}\n\n")
        f.write(f"**Collection Date:** {report['analysis_date']}\n\n")
        f.write("## Data Sources: Yahoo Finance, Finnhub API\n\n")
        f.write("### Raw Financial Data\n\n")
        # Save the actual raw data structure
        f.write("```json\n")
        serialized_data = serialize_dict_with_timestamps(raw_data.get('fundamental', {}))
        f.write(json.dumps(serialized_data, indent=2))
        f.write("\n```\n\n")
        f.write("### Data Collection Notes\n\n")
        f.write("- Primary Source: Yahoo Finance (financial ratios, company info)\n")
        f.write("- Secondary Source: Finnhub API (insider trading, SEC filings)\n")
        f.write("- All financial ratios and metrics are real-time\n")
        f.write("- All data is verifiable through respective APIs\n")

def main():
    """Main function to run the stock analysis system."""
    console = Console()
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[bold red]Error: OPENAI_API_KEY not found in environment variables.[/bold red]")
        console.print("Please set your OpenAI API key in the .env file or environment variables.")
        console.print("You can copy env_example.txt to .env and fill in your API keys.")
        return
    
    console.print(Panel(
        "[bold blue]Stock Analyst AI Agent[/bold blue]\n"
        "A multi-agent system for comprehensive stock analysis and investment decision making.",
        border_style="blue"
    ))
    
    # Get user input
    ticker = Prompt.ask(
        "[bold green]Enter stock ticker symbol[/bold green]",
        default="AAPL"
    ).upper()
    
    debate_rounds = Prompt.ask(
        "[bold green]Number of debate rounds[/bold green]",
        default="3",
        choices=["1", "2", "3", "4", "5"]
    )
    
    debug_mode = Confirm.ask(
        "[bold green]Enable debug mode?[/bold green]",
        default=False
    )
    
    # Initialize the analyst
    try:
        analyst = StockAnalyst(debug=debug_mode)
        
        # Run the analysis
        console.print(f"\n[bold yellow]Starting analysis for {ticker}...[/bold yellow]")
        report = analyst.analyze_stock(ticker, int(debate_rounds))
        
        # Print the results
        if "error" not in report:
            console.print("\n" + "="*80)
            console.print("[bold green]Analysis Complete![/bold green]")
            console.print("="*80)
            
            analyst.print_report(report)
            
            # Ask if user wants to save the report
            save_report = Confirm.ask(
                "[bold green]Save report to file?[/bold green]",
                default=False
            )
            
            if save_report:
                # Ensure reports directory exists
                reports_dir = "reports"
                os.makedirs(reports_dir, exist_ok=True)
                filename_base = os.path.join(reports_dir, f"{ticker}_analysis_{report['analysis_date'][:10]}")
                
                # Save Markdown version
                md_filename = save_markdown_report(report, ticker, filename_base)
                console.print(f"[bold green]Markdown report saved to {md_filename}[/bold green]")
        else:
            console.print(f"[bold red]Analysis failed: {report['error']}[/bold red]")
    
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Analysis interrupted by user.[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {str(e)}[/bold red]")
        if debug_mode:
            import traceback
            console.print(traceback.format_exc())

if __name__ == "__main__":
    main() 