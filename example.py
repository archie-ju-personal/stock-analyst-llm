"""
Example script demonstrating the Stock Analyst AI Agent system.
"""

from stock_analyst import StockAnalyst
from rich.console import Console

def run_example():
    """Run a simple example analysis."""
    console = Console()
    
    console.print("[bold blue]Stock Analyst AI Agent - Example[/bold blue]")
    console.print("This example will analyze AAPL with 2 debate rounds in debug mode.\n")
    
    try:
        # Initialize the analyst in debug mode
        analyst = StockAnalyst(debug=True)
        
        # Run analysis for AAPL with 2 debate rounds
        console.print("[yellow]Starting analysis for AAPL...[/yellow]")
        report = analyst.analyze_stock("AAPL", debate_rounds=2)
        
        # Print results
        if "error" not in report:
            console.print("\n[bold green]Example Analysis Complete![/bold green]")
            analyst.print_report(report)
        else:
            console.print(f"[bold red]Analysis failed: {report['error']}[/bold red]")
    
    except Exception as e:
        console.print(f"[bold red]Error running example: {str(e)}[/bold red]")

if __name__ == "__main__":
    run_example() 