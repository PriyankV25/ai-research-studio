from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from rich import print
load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query: str) -> str:
    """
    Search the web for recent and relevent information on a topic. Returns Titles, URLs and snippets of the top results.
    Perform a web search using the Tavily API and return the results.
    """
    try:
        results = tavily.search(query=query, max_results=10)
        out = []

        for r in results.get("results", []):
            title = r.get("title", "")
            url = r.get("url", "")
            content = r.get("content", "")
            out.append(f"Title: {title}\nURL: {url}\nSnippet: {content[:300]}\n")

        return "\n----\n".join(out) if out else "No results found."
    except Exception as e:
        return f"An error occurred while performing the web search: {str(e)}"


@tool
def scrape_url(url: str) -> str:
    """
    Scrape the content of a given URL and return the text content for deep reading and analysis.
    """
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()  # Raise an error for bad responses
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav','footer']):
            tag.decompose()  # Remove script and style elements
        return soup.get_text(separator='\n', strip=True)[:5000]
    except requests.exceptions.RequestException as e:
        return f"An error occurred while scraping the URL: {str(e)}"

