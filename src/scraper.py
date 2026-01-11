"""
Main orchestration module for YouTube Analytics Scraper.
Coordinates the complete scraping pipeline.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config.config import (
    YOUTUBE_BASE_URL, MAX_VIDEOS_DEFAULT, VIDEO_LIMIT_TEST, 
    DEBUG_MODE, REQUEST_DELAY
)
from src.config.performance_config import (
    MAX_CHANNEL_WORKERS, print_performance_config, get_preset_config
)
from src.scrapers.channel_scraper import get_channel_data
from src.scrapers.video_scraper import (
    get_video_links, get_shorts_links, get_detailed_video_data,
    get_total_videos_count, get_total_shorts_count,
    calculate_total_views_from_pages
)
from src.scrapers.parallel_video_scraper import scrape_video_details
from src.utils.data_processor import (
    validate_channel_data, validate_video_data, process_video_data,
    calculate_channel_metrics, calculate_daily_metrics, export_to_excel
)


def scrape_channel(channel_name, max_videos=50, max_shorts=50, parallel_videos=True):
    """
    Complete scraping pipeline for a YouTube channel.
    Extracts both regular videos and shorts into separate datasets.
    
    Args:
        channel_name (str): YouTube channel name (e.g., '@valorant')
        max_videos (int): Maximum regular videos to scrape
        max_shorts (int): Maximum shorts to scrape
        parallel_videos (bool): Whether to use parallel video detail scraping
        
    Returns:
        tuple: (channel_data, videos, shorts) or (None, [], []) if error
    """
    
    print("\n" + "="*60)
    print("YouTube Analytics Scraper - Complete Pipeline")
    print("="*60)
    
    # Step 1: Scrape channel data
    print("\n[1/5] Scraping Channel Data...")
    print("-"*60)
    channel_data = get_channel_data(channel_name)
    channel_data = validate_channel_data(channel_data)
    
    if not channel_data:
        print("[ERROR] Failed to scrape channel data")
        return None, [], []
    
    # Extract channel_id for linking
    channel_id = channel_data.get('channel_id', '')
    channel_url = f'{YOUTUBE_BASE_URL}/{channel_name}'
    
    # Step 1.5: Get actual total counts from YouTube
    print("\n[1.5/5] Getting Actual Content Counts...")
    print("-"*60)
    
    # Calculate total views by scrolling through all content pages
    # This also gives us accurate video/shorts counts
    video_count, shorts_count, video_views, shorts_views, accurate_total_views = calculate_total_views_from_pages(channel_url)
    
    # Update channel data with actual counts and accurate total views
    channel_data['video_count'] = video_count
    channel_data['shorts_count'] = shorts_count
    channel_data['total_content_count'] = video_count + shorts_count
    channel_data['total_views'] = accurate_total_views
    
    # Step 2: Get regular videos
    print("\n[2/5] Scraping Regular Videos...")
    print("-"*60)
    
    # Get basic video list (limited to max_videos for detailed scraping)
    videos_list = get_video_links(channel_url, max_videos=max_videos, total_videos_count=video_count)
    videos_list = validate_video_data(videos_list)
    
    # Filter to only long videos (not shorts)
    original_count = len(videos_list)
    videos_list = [v for v in videos_list if not v.get('is_short', False)]
    if original_count > len(videos_list):
        print(f"[OK] Filtered to {len(videos_list)} LONG videos (out of {original_count})")
    
    print(f"[OK] Found {len(videos_list)} regular videos for detailed scraping")
    
    # Step 3: Get shorts from dedicated tab
    print("\n[3/5] Scraping Shorts...")
    print("-"*60)
    
    # Get basic shorts list (limited to max_shorts for detailed scraping)
    shorts_list = get_shorts_links(channel_url, max_shorts=max_shorts, total_shorts_count=shorts_count)
    shorts_list = validate_video_data(shorts_list)
    
    print(f"[OK] Found {len(shorts_list)} shorts for detailed scraping")
    
    # Step 4 & 5: Get detailed data for videos and shorts using optimized parallel scraper
    print("\n[4/5] Scraping Video & Short Details...")
    print("-"*60)
    
    detailed_videos_list, detailed_shorts_list = scrape_video_details(
        videos_list, 
        shorts_list, 
        parallel=parallel_videos
    )
    
    # Process and combine data
    print("\n[5/5] Processing Data...")
    print("-"*60)
    
    # Process videos with channel_id for linking (only the limited set for detailed scraping)
    videos = process_video_data(videos_list, detailed_videos_list, channel_id)
    videos = validate_video_data(videos)
    
    shorts = process_video_data(shorts_list, detailed_shorts_list, channel_id)
    shorts = validate_video_data(shorts)
    
    # Calculate aggregate metrics using long videos and shorts separately
    channel_data = calculate_channel_metrics(channel_data, videos, shorts)
    
    # Calculate daily metrics by comparing with historical data
    print("\n[6/6] Calculating Daily Metrics...")
    print("-"*60)
    channel_data = calculate_daily_metrics(channel_data)
    
    return channel_data, videos, shorts


def save_results(channel_data, videos, shorts):
    """
    Save scraped data to Excel file with separate sheets for channel, videos, and shorts.
    
    Args:
        channel_data (dict): Channel data
        videos (list): Regular videos data list
        shorts (list): Shorts data list
        
    Returns:
        bool: Success status
    """
    print("\n[Export] Saving to Excel...")
    print("-"*60)
    
    if channel_data:
        return export_to_excel(channel_data, videos, shorts)
    else:
        print("[ERROR] No data to export")
        return False


def scrape_multiple_channels(channel_list, max_videos=50, max_shorts=50, parallel=True, 
                            max_workers=None, parallel_videos=True, preset='balanced'):
    """
    Scrape multiple YouTube channels and combine results into a single export.
    Can run in parallel or sequential mode.
    
    Args:
        channel_list (list): List of channel names (e.g., ['@valorant', '@mkbhd'])
        max_videos (int): Maximum regular videos per channel
        max_shorts (int): Maximum shorts per channel
        parallel (bool): Whether to scrape channels in parallel (default: True)
        max_workers (int): Number of parallel workers (default: auto from config)
        parallel_videos (bool): Whether to use parallel video detail scraping
        preset (str): Performance preset ('fast', 'balanced', 'safe', 'single')
        
    Returns:
        tuple: (all_channel_data, all_videos, all_shorts)
    """
    all_channel_data = []
    all_videos = []
    all_shorts = []
    
    # Load performance preset if specified
    if preset and preset != 'balanced':
        config = get_preset_config(preset)
        max_workers = config['max_channel_workers']
        print(f"\n[Performance] Using '{preset}' preset: {config['description']}")
    
    # Use config default if max_workers not specified
    if max_workers is None:
        max_workers = MAX_CHANNEL_WORKERS
    
    # Print performance configuration
    print_performance_config()
    
    print("\n" + "="*60)
    mode = "PARALLEL" if parallel else "SEQUENTIAL"
    print(f"Multi-Channel Scraper - {mode} MODE")
    print(f"Processing {len(channel_list)} channels")
    if parallel:
        print(f"Using {max_workers} parallel channel workers")
        print(f"Video detail scraping: {'PARALLEL' if parallel_videos else 'SEQUENTIAL'}")
    print("="*60)
    
    if parallel:
        # Parallel scraping with ThreadPoolExecutor
        def scrape_single_channel(channel_name, idx, total):
            """Helper function to scrape a single channel."""
            print(f"\n{'='*60}")
            print(f"[Channel {idx}/{total}] {channel_name} - Starting...")
            print("="*60)
            
            try:
                channel_data, videos, shorts = scrape_channel(
                    channel_name, 
                    max_videos=max_videos, 
                    max_shorts=max_shorts,
                    parallel_videos=parallel_videos
                )
                
                if channel_data:
                    print(f"\n[OK] Successfully scraped {channel_name}")
                    print(f"  - Videos: {len(videos)}")
                    print(f"  - Shorts: {len(shorts)}")
                    return {
                        'success': True,
                        'channel': channel_name,
                        'data': (channel_data, videos, shorts)
                    }
                else:
                    print(f"\n[ERROR] Failed to scrape {channel_name}")
                    return {'success': False, 'channel': channel_name, 'data': None}
                    
            except Exception as e:
                print(f"\n[ERROR] Error scraping {channel_name}: {e}")
                import traceback
                traceback.print_exc()
                return {'success': False, 'channel': channel_name, 'data': None}
        
        # Execute parallel scraping
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks with staggered start
            future_to_channel = {}
            for idx, channel in enumerate(channel_list):
                # Stagger the start of each worker by 2 seconds to avoid overwhelming YouTube
                if idx > 0:
                    time.sleep(2)
                future = executor.submit(scrape_single_channel, channel, idx+1, len(channel_list))
                future_to_channel[future] = channel
            
            # Collect results as they complete
            for future in as_completed(future_to_channel):
                result = future.result()
                if result['success'] and result['data']:
                    channel_data, videos, shorts = result['data']
                    all_channel_data.append(channel_data)
                    all_videos.extend(videos)
                    all_shorts.extend(shorts)
    
    else:
        # Sequential scraping (original method)
        for idx, channel_name in enumerate(channel_list, 1):
            print(f"\n{'='*60}")
            print(f"[Channel {idx}/{len(channel_list)}] {channel_name}")
            print("="*60)
            
            try:
                # Scrape individual channel
                channel_data, videos, shorts = scrape_channel(
                    channel_name, 
                    max_videos=max_videos, 
                    max_shorts=max_shorts
                )
                
                if channel_data:
                    all_channel_data.append(channel_data)
                    all_videos.extend(videos)
                    all_shorts.extend(shorts)
                    
                    print(f"\n[OK] Successfully scraped {channel_name}")
                    print(f"  - Videos: {len(videos)}")
                    print(f"  - Shorts: {len(shorts)}")
                else:
                    print(f"\n[ERROR] Failed to scrape {channel_name}")
                
                # Delay between channels to avoid rate limiting
                if idx < len(channel_list):
                    print(f"\nWaiting {REQUEST_DELAY} seconds before next channel...")
                    time.sleep(REQUEST_DELAY)
            
            except Exception as e:
                print(f"\n[ERROR] Error scraping {channel_name}: {e}")
                import traceback
                traceback.print_exc()
    
    return all_channel_data, all_videos, all_shorts


def save_multi_channel_results(all_channel_data, all_videos, all_shorts):
    """
    Save multi-channel results to Excel with consolidated sheets.
    
    Args:
        all_channel_data (list): List of channel data dicts
        all_videos (list): Combined videos from all channels
        all_shorts (list): Combined shorts from all channels
        
    Returns:
        bool: Success status
    """
    print("\n" + "="*60)
    print("Multi-Channel Export")
    print("="*60)
    
    if not all_channel_data:
        print("[ERROR] No channel data to export")
        return False
    
    try:
        import pandas as pd
        import os
        from src.config.config import EXCEL_OUTPUT_FILE, CHANNEL_FIELDS, VIDEO_FIELDS
        
        # Create DataFrames
        channels_df = pd.DataFrame(all_channel_data)
        videos_df = pd.DataFrame(all_videos) if all_videos else pd.DataFrame()
        shorts_df = pd.DataFrame(all_shorts) if all_shorts else pd.DataFrame()
        
        # Ensure all expected columns exist
        for field in CHANNEL_FIELDS:
            if field not in channels_df.columns:
                channels_df[field] = ''
        
        for field in VIDEO_FIELDS:
            if all_videos and field not in videos_df.columns:
                videos_df[field] = ''
            if all_shorts and field not in shorts_df.columns:
                shorts_df[field] = ''
        
        # Reorder columns
        channels_df = channels_df[CHANNEL_FIELDS]
        if all_videos:
            videos_df = videos_df[VIDEO_FIELDS]
        if all_shorts:
            shorts_df = shorts_df[VIDEO_FIELDS]
        
        # Export to Excel with absolute path
        output_file = 'data/processed/multi_channel_youtube_analytics_scraped.xlsx'
        abs_path = os.path.abspath(output_file)
        
        with pd.ExcelWriter(abs_path, engine='openpyxl') as writer:
            channels_df.to_excel(writer, sheet_name='All_Channels', index=False)
            if all_videos:
                videos_df.to_excel(writer, sheet_name='All_Videos', index=False)
            if all_shorts:
                shorts_df.to_excel(writer, sheet_name='All_Shorts', index=False)
        
        # Verify file was created
        if os.path.exists(abs_path):
            file_size = os.path.getsize(abs_path)
            print(f"[OK] Exported to: {abs_path}")
            print(f"[OK] File size: {file_size:,} bytes")
        else:
            print(f"[WARNING] File may not have been saved")
        
        print(f"  - Channels: {len(all_channel_data)}")
        print(f"  - Total Videos: {len(all_videos)}")
        print(f"  - Total Shorts: {len(all_shorts)}")
        
        return True
    
    except Exception as e:
        print(f"[ERROR] Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main(channel_name=None, channel_list=None, max_videos=50, max_shorts=50, parallel=True, 
         max_workers=None, parallel_videos=True, preset='balanced'):
    """
    Main entry point for the scraper.
    Extracts both regular videos and shorts into separate Excel sheets.
    Supports single channel or multiple channels (parallel or sequential).
    
    Args:
        channel_name (str): Single YouTube channel name (e.g., '@valorant')
        channel_list (list): List of YouTube channel names (e.g., ['@valorant', '@mkbhd'])
        max_videos (int): Maximum regular videos to scrape per channel
        max_shorts (int): Maximum shorts to scrape per channel
        parallel (bool): Whether to scrape channels in parallel (default: True)
        max_workers (int): Number of parallel workers (default: auto from config)
        parallel_videos (bool): Whether to use parallel video detail scraping
        preset (str): Performance preset ('fast', 'balanced', 'safe', 'single')
    """
    try:
        # Determine if single or multiple channels
        if channel_list and len(channel_list) > 0:
            # Multi-channel mode
            all_channel_data, all_videos, all_shorts = scrape_multiple_channels(
                channel_list, 
                max_videos=max_videos, 
                max_shorts=max_shorts,
                parallel=parallel,
                max_workers=max_workers,
                parallel_videos=parallel_videos,
                preset=preset
            )
            
            # Save multi-channel results
            if all_channel_data:
                success = save_multi_channel_results(all_channel_data, all_videos, all_shorts)
                
                # Print final summary
                print("\n" + "="*60)
                print("MULTI-CHANNEL SUMMARY")
                print("="*60)
                print(f"Total Channels Scraped: {len(all_channel_data)}")
                print(f"Total Videos: {len(all_videos)}")
                print(f"Total Shorts: {len(all_shorts)}")
                print(f"Total Content: {len(all_videos) + len(all_shorts)}")
                print(f"Export Status: {'[OK] Success' if success else '[ERROR] Failed'}")
                
                # Show per-channel breakdown
                print("\nPer-Channel Breakdown:")
                for ch_data in all_channel_data:
                    print(f"  - {ch_data['channel_title']}: {ch_data['subscribers']:,} subscribers | Niche: {ch_data.get('niche', 'N/A')} | Country: {ch_data.get('country', 'N/A')}")
                
                print("="*60 + "\n")
            else:
                print("\n[ERROR] Failed to scrape any channels")
        
        elif channel_name:
            # Single channel mode
            channel_data, videos, shorts = scrape_channel(
                channel_name, 
                max_videos=max_videos, 
                max_shorts=max_shorts,
                parallel_videos=parallel_videos
            )
            
            # Save results
            if channel_data:
                success = save_results(channel_data, videos, shorts)
                
                # Print summary
                print("\n" + "="*60)
                print("SUMMARY")
                print("="*60)
                print(f"Channel: {channel_data['channel_title']}")
                print(f"Subscribers: {channel_data['subscribers']:,}")
                print(f"Total Views: {channel_data['total_views']:,}")
                print(f"Niche: {channel_data.get('niche', 'N/A')}")
                print(f"Country: {channel_data.get('country', 'N/A')}")
                print(f"Language: {channel_data.get('default_language', 'N/A')}")
                print(f"Regular Videos: {len(videos)}")
                print(f"Shorts: {len(shorts)}")
                print(f"Total Content: {len(videos) + len(shorts)}")
                print(f"Export Status: {'[OK] Success' if success else '[ERROR] Failed'}")
                print("="*60 + "\n")
            else:
                print("\n[ERROR] Failed to scrape channel data")
        else:
            print("[ERROR] Please provide either channel_name or channel_list")
    
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Example 1: Single channel
    #main(channel_name='@thesavagesiblings', max_videos=1, max_shorts=1)
    
    # Example 2: Multiple channels
    channels_to_scrape = [
        '@thesavagesiblings',
        '@valorant',
        '@mkbhd'
    ]
    # main(channel_list=channels_to_scrape, max_videos=5, max_shorts=5)
