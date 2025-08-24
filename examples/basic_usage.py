"""Basic usage examples for YouTube API MCP Server."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from youtube_api_server.extractors.youtube_api_extractor import YouTubeAPIExtractor


async def main():
    """Demonstrate basic usage of the YouTube API extractor."""
    
    # Initialize the extractor
    extractor = YouTubeAPIExtractor()
    
    # Example URLs for testing
    video_url = "https://youtu.be/cjVhfsx_6kc?feature=shared"
    channel_url = "https://www.youtube.com/@RickAstleyYT"
    
    print("🎥 YouTube API MCP Server - Basic Usage Examples\n")
    print("=" * 50)
    
    # Example 1: Get Video Information
    print("\n📊 Example 1: Get Video Information")
    print("-" * 30)
    try:
        video_info = await extractor.get_video_info(video_url)
        print(f"Title: {video_info['title']}")
        print(f"Channel: {video_info['channel']}")
        print(f"Views: {video_info['statistics']['view_count']:,}")
        print(f"Likes: {video_info['statistics']['like_count']:,}")
        print(f"Duration: {video_info['duration']['formatted']}")
        print(f"Engagement Rate: {video_info['engagement_rate']:.2f}%")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 2: Get Video Comments
    print("\n💬 Example 2: Get Video Comments")
    print("-" * 30)
    try:
        comments = await extractor.get_video_comments(video_url, max_comments=5)
        print(f"Total comments extracted: {len(comments['comments'])}")
        
        for i, comment in enumerate(comments['comments'][:3], 1):
            print(f"\n{i}. {comment['author']}")
            print(f"   💝 {comment['likes']} likes")
            print(f"   📝 {comment['text'][:100]}{'...' if len(comment['text']) > 100 else ''}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 3: Search YouTube
    print("\n🔍 Example 3: Search YouTube")
    print("-" * 30)
    try:
        search_results = await extractor.search_youtube(
            query="Python programming tutorial",
            search_type="video",
            max_results=3
        )
        
        print(f"Found {len(search_results['results'])} results:")
        for i, result in enumerate(search_results['results'], 1):
            print(f"\n{i}. {result['title']}")
            print(f"   📺 {result['channel_title']}")
            print(f"   🔗 {result['url']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 4: Get Channel Information
    print("\n📺 Example 4: Get Channel Information")
    print("-" * 30)
    try:
        channel_info = await extractor.get_channel_info(channel_url)
        print(f"Channel: {channel_info['title']}")
        print(f"Subscribers: {channel_info['statistics']['subscriber_count']:,}")
        print(f"Total Views: {channel_info['statistics']['view_count']:,}")
        print(f"Videos: {channel_info['statistics']['video_count']:,}")
        print(f"Subscriber Tier: {channel_info['subscriber_tier']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 5: Analyze Video Engagement
    print("\n📈 Example 5: Analyze Video Engagement")
    print("-" * 30)
    try:
        analysis = await extractor.analyze_video_engagement(video_url)
        engagement = analysis['engagement_analysis']
        
        print(f"Engagement Rate: {engagement['engagement_rate']:.2f}%")
        print(f"Like Ratio: {engagement['like_ratio']:.1f}%")
        print(f"Engagement Level: {engagement['engagement_level']}")
        print(f"Total Interactions: {engagement['total_interactions']:,}")
        
        if analysis.get('recommendations'):
            print("\n📋 Recommendations:")
            for rec in analysis['recommendations'][:2]:
                print(f"   • {rec}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 6: Get Transcript (if available)
    print("\n📜 Example 6: Get Video Transcript")
    print("-" * 30)
    try:
        transcript = await extractor.get_video_transcript(video_url)
        if transcript:
            print(f"Transcript available: {transcript['language']}")
            print(f"Total segments: {transcript['total_segments']}")
            print(f"Duration: {transcript['duration']:.1f} seconds")
            print(f"Sample text: {transcript['full_text'][:150]}...")
        else:
            print("❌ No transcript available for this video")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 7: Get Extractor Statistics
    print("\n📊 Example 7: Extractor Statistics")
    print("-" * 30)
    try:
        stats = extractor.get_extractor_stats()
        rate_limiter = stats['api_client']['rate_limiter']
        cache = stats['api_client']['cache']
        
        print(f"API Requests Made Today: {rate_limiter['daily_requests_made']}")
        print(f"Requests Remaining: {rate_limiter['daily_requests_remaining']}")
        print(f"Cache Hit Rate: {cache['hit_rate'] * 100:.1f}%")
        print(f"Cache Size: {cache['size']}/{cache['max_size']}")
        print(f"Status: {stats['status']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ All examples completed!")
    print("\n💡 Tips:")
    print("   • Set YOUTUBE_API_KEY in your .env file")
    print("   • API quota: 10,000 units/day (free tier)")
    print("   • Video info: 1 unit, Comments: ~100 units, Search: 100 units")
    print("   • Enable caching to reduce API calls")


if __name__ == "__main__":
    asyncio.run(main())