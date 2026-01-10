"""
Optimized parallel video scraping module for GTX 1660 Super systems.
Implements concurrent video detail extraction with smart batching and rate limiting.
"""

import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
from src.scrapers.video_scraper import get_detailed_video_data
from src.config.performance_config import (
    MAX_VIDEO_DETAIL_WORKERS,
    VIDEO_DETAIL_BATCH_SIZE,
    SHORTS_DETAIL_BATCH_SIZE,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    get_optimal_workers
)


def random_delay(min_delay=REQUEST_DELAY_MIN, max_delay=REQUEST_DELAY_MAX):
    """
    Sleep for a random duration to avoid detection patterns.
    
    Args:
        min_delay (float): Minimum delay in seconds
        max_delay (float): Maximum delay in seconds
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


def scrape_video_details_batch(video_batch: List[Dict], batch_num: int, total_batches: int, 
                                content_type: str = "video") -> List[Dict]:
    """
    Scrape detailed data for a batch of videos in parallel.
    
    Args:
        video_batch (List[Dict]): Batch of video objects with URLs
        batch_num (int): Current batch number
        total_batches (int): Total number of batches
        content_type (str): Type of content ('video' or 'short')
        
    Returns:
        List[Dict]: List of detailed video data
    """
    detailed_data = []
    batch_size = len(video_batch)
    
    # Calculate optimal workers for this batch
    workers = get_optimal_workers(batch_size, MAX_VIDEO_DETAIL_WORKERS)
    
    print(f"\n  [Batch {batch_num}/{total_batches}] Processing {batch_size} {content_type}s with {workers} workers...")
    
    def scrape_single_video(video_info: Dict, idx: int) -> Tuple[int, Dict]:
        """
        Scrape a single video with error handling.
        
        Returns:
            Tuple of (index, detailed_data)
        """
        try:
            title = video_info.get('title', 'No Title')[:40]
            
            # Add random delay before request
            if idx > 0:
                random_delay(REQUEST_DELAY_MIN * 0.5, REQUEST_DELAY_MAX * 0.5)
            
            detailed = get_detailed_video_data(video_info['url'])
            
            # Merge with original data
            detailed.update({
                'url': video_info['url'],
                'is_short': video_info.get('is_short', False)
            })
            
            print(f"    [{idx+1}/{batch_size}] ✓ {title}")
            return (idx, detailed)
            
        except Exception as e:
            print(f"    [{idx+1}/{batch_size}] ✗ Error: {e}")
            return (idx, video_info)  # Return original data on failure
    
    # Execute parallel scraping with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_video = {
            executor.submit(scrape_single_video, video, i): i 
            for i, video in enumerate(video_batch)
        }
        
        # Collect results in order
        results = [None] * batch_size
        for future in as_completed(future_to_video):
            idx, data = future.result()
            results[idx] = data
        
        detailed_data = [r for r in results if r is not None]
    
    print(f"  [Batch {batch_num}/{total_batches}] ✓ Completed {len(detailed_data)}/{batch_size} {content_type}s")
    
    return detailed_data


def scrape_videos_parallel(videos_list: List[Dict], content_type: str = "video") -> List[Dict]:
    """
    Scrape video details in parallel with smart batching.
    
    Args:
        videos_list (List[Dict]): List of video objects with URLs
        content_type (str): Type of content ('video' or 'short')
        
    Returns:
        List[Dict]: List of detailed video data
    """
    if not videos_list:
        return []
    
    # Determine batch size based on content type
    batch_size = SHORTS_DETAIL_BATCH_SIZE if content_type == "short" else VIDEO_DETAIL_BATCH_SIZE
    
    total_videos = len(videos_list)
    batches = [videos_list[i:i + batch_size] for i in range(0, total_videos, batch_size)]
    total_batches = len(batches)
    
    print(f"\n[Parallel Scraping] {total_videos} {content_type}s divided into {total_batches} batches")
    print(f"  Batch size: {batch_size} | Workers per batch: {MAX_VIDEO_DETAIL_WORKERS}")
    
    all_detailed_data = []
    
    for batch_num, batch in enumerate(batches, 1):
        # Process batch
        detailed_batch = scrape_video_details_batch(
            batch, 
            batch_num, 
            total_batches, 
            content_type
        )
        all_detailed_data.extend(detailed_batch)
        
        # Inter-batch delay (except for last batch)
        if batch_num < total_batches:
            delay = random.uniform(1.0, 2.0)
            print(f"  Pausing {delay:.1f}s before next batch...")
            time.sleep(delay)
    
    success_count = len([d for d in all_detailed_data if d.get('title')])
    print(f"\n[OK] Parallel scraping complete: {success_count}/{total_videos} {content_type}s scraped")
    
    return all_detailed_data


def scrape_videos_sequential(videos_list: List[Dict], content_type: str = "video") -> List[Dict]:
    """
    Scrape video details sequentially (fallback/safe mode).
    
    Args:
        videos_list (List[Dict]): List of video objects with URLs
        content_type (str): Type of content ('video' or 'short')
        
    Returns:
        List[Dict]: List of detailed video data
    """
    if not videos_list:
        return []
    
    print(f"\n[Sequential Scraping] Processing {len(videos_list)} {content_type}s one by one...")
    
    detailed_data = []
    
    for i, video in enumerate(videos_list):
        try:
            title = video.get('title', 'No Title')[:40]
            print(f"  [{i+1}/{len(videos_list)}] Processing: {title}...")
            
            detailed = get_detailed_video_data(video['url'])
            detailed.update({
                'url': video['url'],
                'is_short': video.get('is_short', False)
            })
            detailed_data.append(detailed)
            
            # Delay between requests
            if i < len(videos_list) - 1:
                random_delay()
        
        except Exception as e:
            print(f"    [ERROR] Error processing {content_type}: {e}")
            detailed_data.append(video)
    
    print(f"[OK] Sequential scraping complete: {len(detailed_data)}/{len(videos_list)} {content_type}s")
    
    return detailed_data


def scrape_video_details(videos_list: List[Dict], shorts_list: List[Dict], 
                         parallel: bool = True) -> Tuple[List[Dict], List[Dict]]:
    """
    Main function to scrape video details with optimized parallelization.
    
    Args:
        videos_list (List[Dict]): List of regular videos
        shorts_list (List[Dict]): List of shorts
        parallel (bool): Whether to use parallel scraping
        
    Returns:
        Tuple[List[Dict], List[Dict]]: (detailed_videos, detailed_shorts)
    """
    print("\n" + "="*60)
    mode = "PARALLEL" if parallel else "SEQUENTIAL"
    print(f"Video Detail Scraping - {mode} MODE")
    print("="*60)
    print(f"Videos to scrape: {len(videos_list)}")
    print(f"Shorts to scrape: {len(shorts_list)}")
    
    if parallel:
        # Parallel mode
        detailed_videos = scrape_videos_parallel(videos_list, "video")
        detailed_shorts = scrape_videos_parallel(shorts_list, "short")
    else:
        # Sequential mode
        detailed_videos = scrape_videos_sequential(videos_list, "video")
        detailed_shorts = scrape_videos_sequential(shorts_list, "short")
    
    print("\n" + "="*60)
    print(f"Detail scraping complete!")
    print(f"  Videos: {len(detailed_videos)}/{len(videos_list)}")
    print(f"  Shorts: {len(detailed_shorts)}/{len(shorts_list)}")
    print("="*60)
    
    return detailed_videos, detailed_shorts


# Convenience function for backward compatibility
def get_all_video_details(videos: List[Dict], parallel: bool = True) -> List[Dict]:
    """
    Get detailed data for a list of videos.
    
    Args:
        videos (List[Dict]): List of video objects with URLs
        parallel (bool): Whether to use parallel scraping
        
    Returns:
        List[Dict]: List of detailed video data
    """
    if parallel:
        return scrape_videos_parallel(videos, "video")
    else:
        return scrape_videos_sequential(videos, "video")
