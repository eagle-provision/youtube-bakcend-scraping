"""YouTube Analytics Data Pipeline - Main Entry Point."""
import time
from config import TOPICS, REQUEST_DELAY
from youtube_api import search_videos_by_topic, fetch_video_details, fetch_channel_details
from data_processor import merge_video_channel_data, export_to_excel


def main():
    """Main pipeline orchestrator."""
    print("═" * 50)
    print("YouTube Data Analytics Pipeline")
    print("═" * 50)
    
    all_records = []

    for topic in TOPICS:
        print(f"\n📊 Processing Niche: {topic}")
        
        # Step 1: Search for videos
        video_ids = search_videos_by_topic(topic)
        print(f"  → Found {len(video_ids)} videos")
        
        if not video_ids:
            continue

        # Step 2: Fetch video details
        videos_data, channel_ids = fetch_video_details(video_ids)
        
        # Step 3: Fetch channel details
        channel_lookup = fetch_channel_details(channel_ids)
        
        # Step 4: Merge data
        records = merge_video_channel_data(topic, videos_data, channel_lookup)
        all_records.extend(records)
        
        print(f"  ✓ Processed {len(records)} records")
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)

    # Step 5: Export to Excel
    print("\n" + "═" * 50)
    print("Exporting Data")
    print("═" * 50)
    export_to_excel(all_records)


if __name__ == "__main__":
    main()
