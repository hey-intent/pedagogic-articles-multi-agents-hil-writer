"""Tools for the Pedagogical Article Writer.

This module exports the web search and web page reader tools used by
the approach agent to research pedagogical approaches.
"""

from src.tools.web_search import web_search
from src.tools.web_reader import read_webpage

__all__ = ["web_search", "read_webpage"]
