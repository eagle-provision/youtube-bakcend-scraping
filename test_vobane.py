"""
Test Script for @vobane Channel
Validates POC with accurate data extraction and proper structure.
"""

from src.scraper import scrape_channel, save_results
from src.config.performance_config import print_performance_config, GPU_AVAILABLE
import os
from datetime import datetime


def test_vobane_channel():
    """
    Test the scraper with @vobane channel to validate:
    1. Data accuracy (views, subscriber counts, video counts)
    2. Proper data structure (Static, Evolving, Videos)
    3. All required fields per PDF specification
    4. Correct separation of long-form videos and Shorts
    """
    
    print("\n" + "="*70)
    print("TESTING WITH @vobane CHANNEL")
    print("="*70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"GPU Available: {'Yes ✓' if GPU_AVAILABLE else 'No ✗'}")
    print_performance_config()
    print("="*70)
    
    # Delete existing output file to start fresh
    output_file = 'data/processed/youtube_analytics_scraped.xlsx'
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"\n✓ Cleared previous output file")
    
    # Scrape @vobane channel
    channel_name = '@vobane'
    max_videos = 20  # Get enough to validate accuracy
    max_shorts = 20
    
    print(f"\n{'='*70}")
    print(f"SCRAPING: {channel_name}")
    print(f"Max Long-Form Videos: {max_videos}")
    print(f"Max Shorts: {max_shorts}")
    print(f"{'='*70}\n")
    
    # Run scraping
    channel_data, videos, shorts = scrape_channel(
        channel_name=channel_name,
        max_videos=max_videos,
        max_shorts=max_shorts,
        parallel_videos=True
    )
    
    # Validation & Results Summary
    print("\n" + "="*70)
    print("EXTRACTION RESULTS SUMMARY")
    print("="*70)
    
    if channel_data:
        print("\n[CHANNEL DATA]")
        print(f"  Channel ID: {channel_data.get('channel_id', 'NOT FOUND')}")
        print(f"  Channel URL: {channel_data.get('channel_url', 'NOT FOUND')}")
        print(f"  Channel Handle: {channel_data.get('channel_handle', 'NOT FOUND')}")
        print(f"  Channel Title: {channel_data.get('channel_title', 'NOT FOUND')}")
        print(f"  Subscribers: {channel_data.get('subscribers', 0):,}")
        print(f"  Total Views: {channel_data.get('total_views', 0):,}")
        print(f"  Creation Date: {channel_data.get('creation_date', 'NOT FOUND')}")
        print(f"  Country: {channel_data.get('country', 'Not specified')}")
        print(f"  Language: {channel_data.get('default_language', 'Not specified')}")
        print(f"  Monetization: {channel_data.get('monetization_status', 'Placeholder')}")
        
        print("\n[CONTENT COUNTS]")
        print(f"  Total Long-form Videos on Channel: {channel_data.get('video_count', 0)}")
        print(f"  Total Shorts on Channel: {channel_data.get('shorts_count', 0)}")
        print(f"  Total Content: {channel_data.get('total_content_count', 0)}")
        print(f"  Last Posted: {channel_data.get('last_posted_date', 'N/A')}")
        print(f"\n  Extracted Long-form Videos: {len(videos)}")
        print(f"  Extracted Shorts: {len(shorts)}")
        print(f"  Note: Extraction limited to max_videos={max_videos}, max_shorts={max_shorts}")
        
        print("\n[DAILY METRICS]")
        daily_sub_change = channel_data.get('daily_subscriber_change', 0)
        daily_view_change = channel_data.get('daily_views_change', 0)
        growth_rate = channel_data.get('growth_rate', 0.0)
        
        print(f"  Daily Subscriber Change: {daily_sub_change:+,}")
        print(f"  Daily Views Change: {daily_view_change:+,}")
        print(f"  Growth Rate: {growth_rate:+.2f}%")
        
        if daily_sub_change == 0 and daily_view_change == 0:
            print(f"  Note: First scrape or no historical data - daily metrics will be calculated on next run")
        
        # Check for required fields
        print("\n[REQUIRED FIELDS CHECK]")
        required_static = ['channel_id', 'channel_url', 'channel_handle', 'creation_date']
        required_evolving = ['subscribers', 'total_views', 'video_count', 'shorts_count']
        
        missing_fields = []
        for field in required_static + required_evolving:
            if not channel_data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"  ✗ MISSING FIELDS: {', '.join(missing_fields)}")
        else:
            print(f"  ✓ All required fields present")
    else:
        print("\n  ✗ ERROR: Failed to extract channel data")
    
    # Video data validation
    if videos:
        print(f"\n[LONG-FORM VIDEOS] - {len(videos)} videos extracted")
        print("  Sample (first 3):")
        for i, video in enumerate(videos[:3], 1):
            print(f"    {i}. {video.get('title', 'No title')[:50]}")
            print(f"       Video ID: {video.get('video_id', 'N/A')}")
            print(f"       Views: {video.get('view_count', 0):,}")
            print(f"       Likes: {video.get('like_count', 0):,}")
            print(f"       Comments: {video.get('comment_count', 0):,}")
            print(f"       Duration: {video.get('duration', 'N/A')}")
            print(f"       Upload Date: {video.get('upload_date', 'N/A')}")
        
        # Check video fields
        video_required = ['channel_id', 'video_id', 'url', 'title', 'view_count']
        video_missing = []
        for field in video_required:
            if field not in videos[0]:
                video_missing.append(field)
        
        if video_missing:
            print(f"  ✗ Videos missing fields: {', '.join(video_missing)}")
        else:
            print(f"  ✓ All required video fields present")
    else:
        print("\n[LONG-FORM VIDEOS]")
        print("  ⚠ No long-form videos found")
    
    # Shorts data validation
    if shorts:
        print(f"\n[SHORTS] - {len(shorts)} shorts extracted")
        print("  Sample (first 3):")
        for i, short in enumerate(shorts[:3], 1):
            print(f"    {i}. {short.get('title', 'No title')[:50]}")
            print(f"       Video ID: {short.get('video_id', 'N/A')}")
            print(f"       Views: {short.get('view_count', 0):,}")
            print(f"       Likes: {short.get('like_count', 0):,}")
            print(f"       Duration: {short.get('duration', 'N/A')}")
    else:
        print("\n[SHORTS]")
        print("  ⚠ No shorts found")
    
    # Save results
    print("\n" + "="*70)
    print("SAVING TO EXCEL")
    print("="*70)
    
    if channel_data:
        success = save_results(channel_data, videos, shorts)
        
        if success and os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"\n✓ SUCCESS!")
            print(f"  File: {os.path.abspath(output_file)}")
            print(f"  Size: {file_size:,} bytes")
            print(f"\n  The Excel file contains 4 sheets:")
            print(f"    1. Static_Data - Channel static information")
            print(f"    2. Evolving_Data - Daily metrics snapshot")
            print(f"    3. Videos_Data - Long-form videos")
            print(f"    4. Shorts_Data - Short-form videos")
        else:
            print("\n✗ Failed to save results")
    else:
        print("\n✗ No data to save")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    return channel_data, videos, shorts


if __name__ == "__main__":
    test_vobane_channel()
