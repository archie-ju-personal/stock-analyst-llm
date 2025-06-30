# Google Custom Search API Setup Guide

This guide will help you set up Google Custom Search API to enable web search functionality in the Stock Analyst AI Agent.

## Prerequisites

- Google account
- Basic understanding of APIs

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "Stock-Analyst-AI")
4. Click "Create"

## Step 2: Enable Custom Search API

1. In your Google Cloud project, go to "APIs & Services" → "Library"
2. Search for "Custom Search API"
3. Click on "Custom Search API"
4. Click "Enable"

## Step 3: Create API Key

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "API Key"
3. Copy the generated API key
4. (Optional) Click "Restrict Key" to limit usage to Custom Search API only

## Step 4: Create Custom Search Engine

1. Go to [Google Custom Search](https://cse.google.com/)
2. Click "Add" to create a new search engine
3. Configure your search engine:
   - **Sites to search**: Leave blank for web-wide search, or add specific domains
   - **Name**: Give it a name (e.g., "Stock News Search")
   - **Language**: English
   - **Search the entire web**: Check this box
4. Click "Create"
5. Copy the **Search Engine ID** (cx parameter)

## Step 5: Set Environment Variables

Add these to your `.env` file:

```bash
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CSE_ID=your_search_engine_id_here
```

## Step 6: Test the Setup

Run the stock analysis with a ticker to test if Google search is working:

```bash
python main.py
```

You should see Google search results in the news and social media sections.

## API Usage and Costs

- **Free tier**: 100 searches per day
- **Paid tier**: $5 per 1000 searches
- **Rate limits**: 10,000 searches per day

## Troubleshooting

### Common Issues:

1. **"API key not valid"**: Check that the API key is correct and the Custom Search API is enabled
2. **"Search engine ID not found"**: Verify the CSE ID is correct
3. **"Quota exceeded"**: You've reached the daily limit (100 free searches)
4. **No results**: Try different search queries or check the search engine configuration

### Error Messages:

- `400 Bad Request`: Check API key and CSE ID format
- `403 Forbidden`: API key doesn't have permission or quota exceeded
- `429 Too Many Requests`: Rate limit exceeded

## Alternative Search APIs

If Google Custom Search API doesn't work for you, consider these alternatives:

1. **Bing Search API**: Microsoft's search API
2. **SerpAPI**: Paid service with multiple search engines
3. **NewsAPI**: Specifically for news articles
4. **DuckDuckGo API**: Free but limited functionality

## Security Notes

- Keep your API key secure and never commit it to version control
- Use environment variables for sensitive data
- Consider restricting the API key to specific IP addresses if possible
- Monitor your API usage to avoid unexpected charges 