"""
Data processing and export module.
Handles data validation, transformation, and Excel export.
"""

import pandas as pd
from config import (
    EXCEL_OUTPUT_FILE, SHEET_CHANNEL_DATA, SHEET_VIDEOS_DATA,
    CHANNEL_FIELDS, VIDEO_FIELDS, DEBUG_MODE
)


def format_duration(seconds):
    """
    Convert duration from seconds to MM:SS format.
    
    Args:
        seconds (int or float): Duration in seconds
        
    Returns:
        str: Formatted duration as MM:SS
    """
    if not seconds or pd.isna(seconds):
        return "00:00"
    
    try:
        total_seconds = int(float(seconds))
        minutes = total_seconds // 60
        secs = total_seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return "00:00"


def validate_channel_data(channel_data):
    """
    Validate channel data completeness.
    
    Args:
        channel_data (dict): Channel data dictionary
        
    Returns:
        dict: Validated data
    """
    if not channel_data:
        return None
    
    # Check required fields
    required_fields = ['channel_title', 'subscribers', 'total_views']
    for field in required_fields:
        if field not in channel_data or channel_data[field] is None:
            print(f"✗ Missing required field: {field}")
            return None
    
    if DEBUG_MODE:
        print("✓ Channel data validation passed")
    
    return channel_data


def validate_video_data(videos):
    """
    Validate video data list.
    
    Args:
        videos (list): List of video data dictionaries
        
    Returns:
        list: Validated videos
    """
    if not videos:
        return []
    
    valid_videos = []
    required_fields = ['url', 'title', 'view_count']
    
    for video in videos:
        # Check required fields
        if all(field in video and video[field] is not None for field in required_fields):
            valid_videos.append(video)
        else:
            if DEBUG_MODE:
                print(f"✗ Skipping invalid video: {video.get('title', 'Unknown')}")
    
    if DEBUG_MODE:
        print(f"✓ Video data validation: {len(valid_videos)}/{len(videos)} valid")
    
    return valid_videos


def process_video_data(basic_videos, detailed_data_list, channel_metadata=None):
    """
    Merge basic and detailed video data, and add channel metadata.
    
    Args:
        basic_videos (list): Basic video info from list page
        detailed_data_list (list): Detailed video info from individual pages
        channel_metadata (dict): Channel metadata (niche, country, language) to add to each video
        
    Returns:
        list: Combined video data
    """
    videos = []
    
    # Default channel metadata if not provided
    if channel_metadata is None:
        channel_metadata = {
            'niche': 'General',
            'country': '',
            'default_language': ''
        }
    
    for i, basic_video in enumerate(basic_videos):
        video_data = {**basic_video}
        
        if i < len(detailed_data_list):
            detailed = detailed_data_list[i]
            # Update with detailed data, but preserve view_count if detailed has better value
            for key, value in detailed.items():
                if key == 'view_count':
                    # Use detailed view_count if it's greater (for shorts from detailed scraping)
                    if value and value > video_data.get('view_count', 0):
                        video_data[key] = value
                elif key == 'upload_date':
                    # Use detailed upload_date if basic doesn't have it or detailed is better
                    if value and (not video_data.get('upload_date') or value):
                        video_data[key] = value
                else:
                    # For all other fields, use detailed data if available
                    if value is not None and value != '':
                        video_data[key] = value
        
        # Add channel metadata to each video/short
        video_data['channel_niche'] = channel_metadata.get('niche', 'General')
        video_data['channel_country'] = channel_metadata.get('country', '')
        video_data['channel_language'] = channel_metadata.get('default_language', '')
        
        # Determine if short - refined with actual duration
        duration = int(video_data.get('duration', 0))
        is_short = duration < 60 or '#shorts' in video_data.get('title', '').lower() or video_data.get('is_short', False)
        video_data['is_short'] = is_short
        
        videos.append(video_data)
    
    return videos


def calculate_channel_metrics(channel_data, videos):
    """
    Calculate aggregate channel metrics from videos.
    
    Args:
        channel_data (dict): Channel data
        videos (list): List of video data
        
    Returns:
        dict: Updated channel data with calculated metrics
    """
    if not videos:
        return channel_data
    
    try:
        channel_data['video_count'] = len(videos)
        channel_data['shorts_count'] = sum(1 for v in videos if v.get('is_short', False))
        
        # Get last posted date
        dates = [v.get('upload_date', '') for v in videos if v.get('upload_date', '')]
        if dates:
            channel_data['last_posted_date'] = dates[0]  # First item is latest
        
        # Calculate average recent views
        recent_videos = videos[:5]  # Last 5 videos
        if recent_videos:
            total_views = sum(v.get('view_count', 0) for v in recent_videos)
            channel_data['avg_recent_views'] = total_views / len(recent_videos)
        
        if DEBUG_MODE:
            print(f"✓ Channel metrics calculated")
            print(f"  - Videos: {channel_data['video_count']}")
            print(f"  - Shorts: {channel_data['shorts_count']}")
            print(f"  - Avg recent views: {channel_data['avg_recent_views']:.0f}")
        
        return channel_data
    
    except Exception as e:
        print(f"✗ Error calculating metrics: {e}")
        return channel_data


def export_to_excel(channel_data, videos, shorts):
    """
    Export channel, videos, and shorts data to Excel file with separate sheets.
    
    Args:
        channel_data (dict): Channel data
        videos (list): List of regular video data
        shorts (list): List of shorts data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import os
        
        # Get absolute path
        abs_path = os.path.abspath(EXCEL_OUTPUT_FILE)
        
        with pd.ExcelWriter(abs_path, engine='openpyxl') as writer:
            # Channel data sheet
            df_channel = pd.DataFrame([channel_data])
            df_channel = df_channel[CHANNEL_FIELDS]  # Ensure correct column order
            df_channel.to_excel(writer, sheet_name=SHEET_CHANNEL_DATA, index=False)
            
            if DEBUG_MODE:
                print(f"[OK] Channel data sheet created ({len(df_channel)} row)")
            
            # Videos data sheet
            if videos:
                df_videos = pd.DataFrame(videos)
                # Select only expected columns
                available_cols = [col for col in VIDEO_FIELDS if col in df_videos.columns]
                df_videos = df_videos[available_cols]
                
                # Format duration column if it exists
                if 'duration' in df_videos.columns:
                    df_videos['duration'] = df_videos['duration'].apply(format_duration)
                
                df_videos.to_excel(writer, sheet_name=SHEET_VIDEOS_DATA, index=False)
                
                if DEBUG_MODE:
                    print(f"[OK] Videos data sheet created ({len(df_videos)} rows)")
            
            # Shorts data sheet
            if shorts:
                df_shorts = pd.DataFrame(shorts)
                # Select only expected columns
                available_cols = [col for col in VIDEO_FIELDS if col in df_shorts.columns]
                df_shorts = df_shorts[available_cols]
                
                # Format duration column if it exists
                if 'duration' in df_shorts.columns:
                    df_shorts['duration'] = df_shorts['duration'].apply(format_duration)
                
                df_shorts.to_excel(writer, sheet_name='Shorts_Data', index=False)
                
                if DEBUG_MODE:
                    print(f"[OK] Shorts data sheet created ({len(df_shorts)} rows)")
        
        # Verify file was created
        if os.path.exists(abs_path):
            file_size = os.path.getsize(abs_path)
            print(f"[OK] Saved to: {abs_path}")
            print(f"[OK] File size: {file_size:,} bytes")
        else:
            print(f"[WARNING] File may not have been saved properly")
        
        return True
    
    except Exception as e:
        print(f"[ERROR] Error exporting to Excel: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_from_excel(filename=EXCEL_OUTPUT_FILE):
    """
    Load data from Excel file.
    
    Args:
        filename (str): Excel file name
        
    Returns:
        tuple: (channel_data_df, videos_data_df) or (None, None) if error
    """
    try:
        df_channel = pd.read_excel(filename, sheet_name=SHEET_CHANNEL_DATA)
        # Specify dtype for duration column to keep it as string (MM:SS format)
        df_videos = pd.read_excel(filename, sheet_name=SHEET_VIDEOS_DATA, dtype={'duration': str})
        
        if DEBUG_MODE:
            print(f"✓ Loaded {len(df_channel)} channels and {len(df_videos)} videos")
        
        return df_channel, df_videos
    
    except Exception as e:
        print(f"✗ Error loading Excel file: {e}")
        return None, None
