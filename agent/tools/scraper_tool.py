"""
Tool: scrape_url
Extracts clean article text from any URL using trafilatura.
"""
import trafilatura




def scrape_url(url: str) -> dict:
    """
    Scrape and extract the main text content from a web URL.

    Args:
        url: Full URL of the blog post or article.

    Returns:
        dict with keys: text (str), title (str|None), success (bool), error (str|None)
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {"success": False, "error": "Failed to fetch URL", "text": "", "title": None}

        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        meta = trafilatura.extract_metadata(downloaded)
        title = meta.title if meta else None

        if not text:
            return {"success": False, "error": "No content extracted", "text": "", "title": title}

        return {"success": True, "text": text, "title": title, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e), "text": "", "title": None}
