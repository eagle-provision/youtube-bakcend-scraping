"""Data processing and export module."""
import pandas as pd
from typing import List, Dict
from config import OUTPUT_FILENAME


def merge_video_channel_data(
    topic: str,
    videos_data: List[Dict],
    channel_lookup: Dict[str, Dict]
) -> List[Dict]:
    """
    Merge video and channel data into final records.
    
    Args:
        topic: The niche/topic name
        videos_data: List of video data dictionaries
        channel_lookup: Dictionary mapping channel_id to channel details
        
    Returns:
        List of merged record dictionaries
    """
    records = []
    
    for video in videos_data:
        channel_id = video['channel_id']
        channel_details = channel_lookup.get(
            channel_id,
            {"subscribers": "N/A", "country": "N/A"}
        )
        
        record = {
            "Niche": topic,
            "Country": channel_details['country'],
            "Default Language": video['default_language'],
            "Specific Niches": video['specific_niches'],
            "Views": video['views'],
            "Likes": video['likes'],
            "Comment Count": video['comment_count'],
            "Subscribers": channel_details['subscribers'],
            "Upload Date": video['upload_date'],
            "Thumbnail URL": video['thumbnail'],
            "Video URL": video['video_url'],
            "Video Title": video['title'],
            # Placeholders for transcription and analysis data
            "Transcript": "",
            "Narrative Style": "",
            "Target Audience": "",
            "Age Bracket": "",
            "Specific Niche (Analysis)": "",
            "Content Category": "",
            "Tone": ""
        }
        records.append(record)
    
    return records


def export_to_excel(records: List[Dict], filename: str = OUTPUT_FILENAME) -> None:
    """
    Export records to Excel file.
    
    Args:
        records: List of data records
        filename: Output filename (default from config)
    """
    df = pd.DataFrame(records)
    df.to_excel(filename, index=False)
    print(f"✓ Successfully saved {len(df)} rows to '{filename}'")


def add_transcript_to_record(record: Dict, transcript: str) -> None:
    """Add transcript to a record dictionary."""
    record["Transcript"] = transcript


def add_analysis_to_record(record: Dict, analysis: Dict[str, str]) -> None:
    """Add content analysis results to a record dictionary."""
    record["Narrative Style"] = analysis.get("narrative_style", "")
    record["Target Audience"] = analysis.get("target_audience", "")
    record["Age Bracket"] = analysis.get("age_bracket", "")
    record["Specific Niche (Analysis)"] = analysis.get("specific_niche", "")
    record["Content Category"] = analysis.get("content_category", "")
    record["Tone"] = analysis.get("tone", "")
