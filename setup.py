#!/usr/bin/env python3
"""
Setup script for the Stock Analyst AI Agent project.
This script helps users set up their environment and API keys.
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create a .env file from the example if it doesn't exist."""
    env_file = Path('.env')
    example_file = Path('env_example.txt')
    
    if env_file.exists():
        print("✓ .env file already exists")
        return
    
    if example_file.exists():
        # Copy the example file
        with open(example_file, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✓ Created .env file from env_example.txt")
        print("⚠️  Please edit .env file and add your API keys")
    else:
        print("✗ env_example.txt not found")

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        ('langchain_openai', 'langchain_openai'),
        ('yfinance', 'yfinance'), 
        ('pandas', 'pandas'),
        ('rich', 'rich'),
        ('stockstats', 'stockstats'),
        ('python-dotenv', 'dotenv')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} - MISSING")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    print("\n✓ All dependencies are installed!")
    return True

def check_api_keys():
    """Check if API keys are configured."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("✗ .env file not found")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_keys = ['OPENAI_API_KEY']
    optional_keys = [
        'NEWS_API_KEY',
        'TWITTER_API_KEY', 
        'REDDIT_CLIENT_ID',
        'ALPHA_VANTAGE_API_KEY',
        'FINNHUB_API_KEY'
    ]
    
    print("\nAPI Key Status:")
    
    # Check required keys
    for key in required_keys:
        value = os.getenv(key)
        if value and value != f"your_{key.lower()}_here":
            print(f"✓ {key} - CONFIGURED")
        else:
            print(f"✗ {key} - REQUIRED (for LLM functionality)")
    
    # Check optional keys
    for key in optional_keys:
        value = os.getenv(key)
        if value and value != f"your_{key.lower()}_here":
            print(f"✓ {key} - CONFIGURED")
        else:
            print(f"⚠️  {key} - OPTIONAL (for enhanced data collection)")
    
    return True

def main():
    """Main setup function."""
    print("🚀 Stock Analyst AI Agent - Setup")
    print("=" * 40)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    deps_ok = check_dependencies()
    
    # Create .env file
    print("\n2. Setting up environment...")
    create_env_file()
    
    # Check API keys
    print("\n3. Checking API keys...")
    check_api_keys()
    
    print("\n" + "=" * 40)
    print("🎉 Setup complete!")
    
    if deps_ok:
        print("\nNext steps:")
        print("1. Edit .env file and add your OpenAI API key")
        print("2. Run: python main.py")
        print("3. Or test components: python test_system.py")
    else:
        print("\n⚠️  Please install missing dependencies first:")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main() 