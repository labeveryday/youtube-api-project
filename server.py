#!/usr/bin/env python3
"""Entry point for running the YouTube API MCP Server."""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the server
from youtube_api_server.server import main

if __name__ == "__main__":
    main()