"""API setup guide and validation for YouTube Data API v3."""

import os
import sys
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def check_environment():
    """Check if environment is properly configured."""
    print("🔧 Checking Environment Configuration")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("❌ YOUTUBE_API_KEY not found in environment")
        print("\n📋 Setup Steps:")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable YouTube Data API v3")
        print("4. Create API credentials (API key)")
        print("5. Add YOUTUBE_API_KEY=your_key_here to .env file")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    return api_key


def validate_api_key(api_key):
    """Validate API key by making a test request."""
    print("\n🔍 Validating API Key")
    print("=" * 40)
    
    try:
        # Build YouTube service
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Make a simple test request (search for a common video)
        request = youtube.search().list(
            part='snippet',
            q='test',
            maxResults=1,
            type='video'
        )
        
        response = request.execute()
        
        if response.get('items'):
            print("✅ API key is valid and working!")
            print(f"✅ Successfully retrieved {len(response['items'])} search result")
            
            # Show quota usage info
            print("\n📊 API Quota Information:")
            print("• Daily quota limit: 10,000 units (free tier)")
            print("• This test used: ~100 units")
            print("• Video info: 1 unit per request")
            print("• Comments: 1 unit per comment thread")
            print("• Search: 100 units per request")
            
            return True
        else:
            print("⚠️  API key works but no results returned")
            return True
            
    except HttpError as e:
        print(f"❌ API Error: {e}")
        
        if e.resp.status == 403:
            print("\n🔧 Possible Issues:")
            print("• API key may be invalid")
            print("• YouTube Data API v3 not enabled")
            print("• API key restrictions (IP, referrer, etc.)")
            print("• Daily quota exceeded")
        elif e.resp.status == 400:
            print("• Bad request - check API key format")
        
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_specific_operations(api_key):
    """Test specific YouTube API operations."""
    print("\n🧪 Testing Specific Operations")
    print("=" * 40)
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # Test 1: Get video details (Rick Astley - Never Gonna Give You Up)
    print("\n1️⃣ Testing Video Details...")
    try:
        request = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id='dQw4w9WgXcQ'
        )
        response = request.execute()
        
        if response.get('items'):
            video = response['items'][0]
            print(f"✅ Video: {video['snippet']['title']}")
            print(f"✅ Views: {video['statistics']['viewCount']}")
            print(f"✅ Duration: {video['contentDetails']['duration']}")
        else:
            print("❌ No video data returned")
            
    except Exception as e:
        print(f"❌ Video details test failed: {e}")
    
    # Test 2: Get video comments
    print("\n2️⃣ Testing Video Comments...")
    try:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId='dQw4w9WgXcQ',
            maxResults=1,
            order='relevance'
        )
        response = request.execute()
        
        if response.get('items'):
            print(f"✅ Retrieved {len(response['items'])} comment(s)")
        else:
            print("⚠️  No comments returned (may be disabled)")
            
    except HttpError as e:
        if "commentsDisabled" in str(e):
            print("⚠️  Comments are disabled for this video (normal)")
        else:
            print(f"❌ Comments test failed: {e}")
    except Exception as e:
        print(f"❌ Comments test failed: {e}")
    
    # Test 3: Channel information
    print("\n3️⃣ Testing Channel Information...")
    try:
        request = youtube.channels().list(
            part='snippet,statistics',
            forUsername='RickAstleyYT'
        )
        response = request.execute()
        
        # If username doesn't work, try by channel ID
        if not response.get('items'):
            request = youtube.search().list(
                part='snippet',
                q='Rick Astley',
                type='channel',
                maxResults=1
            )
            response = request.execute()
            
        if response.get('items'):
            print("✅ Channel information retrieved successfully")
        else:
            print("❌ No channel data returned")
            
    except Exception as e:
        print(f"❌ Channel test failed: {e}")


def show_quota_optimization_tips():
    """Show tips for optimizing API quota usage."""
    print("\n💡 API Quota Optimization Tips")
    print("=" * 40)
    
    tips = [
        "Enable caching to reduce redundant API calls",
        "Use batch requests when getting multiple video details",
        "Request only the 'parts' you need (snippet, statistics, etc.)",
        "Implement exponential backoff for rate limiting",
        "Monitor your quota usage in Google Cloud Console",
        "Consider upgrading to paid tier for higher quotas",
        "Cache results locally for frequently accessed data"
    ]
    
    for i, tip in enumerate(tips, 1):
        print(f"{i}. {tip}")


def main():
    """Main setup validation function."""
    print("🚀 YouTube Data API v3 Setup Guide & Validation")
    print("=" * 50)
    
    # Step 1: Check environment
    api_key = check_environment()
    if not api_key:
        sys.exit(1)
    
    # Step 2: Validate API key
    if not validate_api_key(api_key):
        print("\n❌ API validation failed. Please check your setup.")
        sys.exit(1)
    
    # Step 3: Test specific operations
    test_specific_operations(api_key)
    
    # Step 4: Show optimization tips
    show_quota_optimization_tips()
    
    print("\n✅ Setup validation completed successfully!")
    print("\n🎯 Next Steps:")
    print("1. Run: python examples/basic_usage.py")
    print("2. Start the MCP server: python -m src.youtube_api_server.server")
    print("3. Configure Claude Desktop to use the server")
    
    print("\n📚 Configuration for Claude Desktop:")
    print("Add to your Claude Desktop config:")
    print("""
{
  "mcpServers": {
    "youtube-api": {
      "command": "python",
      "args": ["-m", "src.youtube_api_server.server"],
      "cwd": "/path/to/youtube-api-mcp-server",
      "env": {
        "YOUTUBE_API_KEY": "your_api_key_here"
      }
    }
  }
}
""")


if __name__ == "__main__":
    main()