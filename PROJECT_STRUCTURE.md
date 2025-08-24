# Project Structure

## Overview

This is a production-ready YouTube MCP Server using Google Data API v3 with a clean, modular architecture.

## Directory Structure

```
youtube-api-mcp-server/
├── src/youtube_api_server/          # Main package
│   ├── __init__.py                  # Package initialization
│   ├── server.py                    # MCP server with 15 tools
│   ├── config/                      # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py              # Pydantic settings with env support
│   ├── extractors/                  # Data extraction logic
│   │   ├── __init__.py
│   │   ├── youtube_api_extractor.py # Main API extractor
│   │   └── transcript_extractor.py  # yt-dlp fallback for transcripts
│   ├── models/                      # Pydantic data models
│   │   ├── __init__.py
│   │   ├── base.py                  # Base models and common types
│   │   ├── video.py                 # Video information models
│   │   ├── comment.py               # Comment and threading models
│   │   ├── channel.py               # Channel information models
│   │   ├── search.py                # Search result models
│   │   └── transcript.py            # Transcript models
│   └── utils/                       # Utility modules
│       ├── __init__.py
│       ├── api_client.py            # YouTube API client wrapper
│       ├── rate_limiter.py          # API quota management
│       ├── cache.py                 # TTL-based caching
│       └── url_utils.py             # URL parsing utilities
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest configuration
│   ├── test_api_client.py           # API client tests
│   ├── test_models.py               # Model validation tests
│   └── test_url_utils.py            # URL parsing tests
├── examples/                        # Usage examples
│   ├── basic_usage.py               # Comprehensive usage demo
│   ├── api_setup_guide.py           # API validation & setup
│   └── comparison_demo.py           # yt-dlp vs API comparison
├── .env.example                     # Environment configuration template
├── .gitignore                       # Git ignore rules
├── LICENSE                          # MIT License
├── Makefile                         # Development commands
├── MIGRATION_GUIDE.md               # Migration from yt-dlp guide
├── PROJECT_STRUCTURE.md             # This file
├── README.md                        # Main documentation
└── pyproject.toml                   # Modern Python packaging
```

## Key Files

### Core Files
- **`src/youtube_api_server/server.py`** - FastMCP server with 15 YouTube tools
- **`src/youtube_api_server/extractors/youtube_api_extractor.py`** - Main extraction logic
- **`src/youtube_api_server/utils/api_client.py`** - YouTube API wrapper with rate limiting
- **`pyproject.toml`** - Project configuration and dependencies

### Configuration
- **`.env.example`** - Environment variable template (copy to `.env`)
- **`src/youtube_api_server/config/settings.py`** - Pydantic settings management

### Documentation
- **`README.md`** - Main documentation with 100% test results
- **`MIGRATION_GUIDE.md`** - Detailed migration from yt-dlp
- **`PROJECT_STRUCTURE.md`** - This structure overview

### Development
- **`Makefile`** - Common development tasks
- **`tests/`** - Comprehensive test suite
- **`examples/`** - Working examples and validation scripts

## Architecture Highlights

### 🏗️ **Clean Architecture**
- Separation of concerns (models, extractors, utils, config)
- Dependency injection with Pydantic settings
- Modular design for easy testing and maintenance

### 🔧 **Production Ready**
- Comprehensive error handling and logging
- Rate limiting and caching for API efficiency
- Environment-based configuration
- Full test coverage

### 📦 **Modern Python Packaging**
- Uses `pyproject.toml` for configuration
- Compatible with `uv`, `pip`, and other installers
- Proper dependency management
- Entry points for CLI usage

### 🚀 **Performance Optimized**
- Async/await throughout
- TTL-based caching
- Rate limiting with quotas
- Batch processing capabilities

## Development Workflow

1. **Setup**: `make install` or `uv sync`
2. **Test**: `make test` or `uv run pytest`
3. **Lint**: `make lint`
4. **Format**: `make format`
5. **Run Examples**: `make examples`
6. **Run Server**: `make run`

## File Removal Rationale

### Removed Files
- ❌ `youtube_service.py` - Legacy API code, replaced by modular extractors
- ❌ `test_all_functions.py` - Ad-hoc testing, replaced by proper test suite
- ❌ `uv.lock` - Generated file, not needed in repo

### Essential Files Kept
- ✅ All `src/youtube_api_server/` modules - Core functionality
- ✅ `tests/` directory - Proper test structure
- ✅ `examples/` - Working demonstrations
- ✅ Documentation files - User guidance
- ✅ Configuration files - Project setup

This structure follows Python best practices and provides a solid foundation for a production-ready MCP server.