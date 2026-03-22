"""Basic tests. Run with: pytest tests/ -v"""
import pytest
from unittest.mock import patch, MagicMock
from agent.tools.detect_input import detect_input_type
from agent.tools.youtube_tool import get_youtube_transcript
from agent.tools.scraper_tool import scrape_url

def test_detect_youtube():
    assert detect_input_type("https://www.youtube.com/watch?v=abc")["input_type"] == "youtube"

def test_detect_youtube_short():
    assert detect_input_type("https://youtu.be/abc")["input_type"] == "youtube"

def test_detect_url():
    assert detect_input_type("https://example.com/post")["input_type"] == "url"

def test_detect_topic():
    assert detect_input_type("How to grow LinkedIn in 2025")["input_type"] == "topic"

def test_youtube_invalid():
    r = get_youtube_transcript("not-a-url")
    assert r["success"] is False

@patch("agent.tools.youtube_tool.YouTubeTranscriptApi.get_transcript")
def test_youtube_success(mock_get):
    mock_get.return_value = [{"text": "Hello"}, {"text": "World"}]
    r = get_youtube_transcript("https://youtu.be/dQw4w9WgXcQ")
    assert r["success"] is True and "Hello" in r["transcript"]

@patch("agent.tools.scraper_tool.trafilatura.fetch_url", return_value="<html/>")
@patch("agent.tools.scraper_tool.trafilatura.extract", return_value="Article text")
@patch("agent.tools.scraper_tool.trafilatura.extract_metadata", return_value=MagicMock(title="Title"))
def test_scrape_success(a, b, c):
    r = scrape_url("https://example.com")
    assert r["success"] is True and r["text"] == "Article text"

@patch("agent.tools.scraper_tool.trafilatura.fetch_url", return_value=None)
def test_scrape_fail(mock):
    assert scrape_url("https://x.com")["success"] is False
