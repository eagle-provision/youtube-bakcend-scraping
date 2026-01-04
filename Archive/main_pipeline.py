"""Integrated YouTube Analytics Pipeline with Transcription and Content Analysis.

This pipeline:
1. Fetches video metadata from YouTube API
2. Transcribes each video using Whisper
3. Analyzes transcripts using GPT for content insights
4. Exports all data to Excel
"""

import os
import time
import logging
from pathlib import Path
from typing import List, Dict

from config import (
    TOPICS,
    REQUEST_DELAY,
    WHISPER_MODEL,
    CHUNK_DURATION,
    CHUNK_OVERLAP,
    CLEANUP_TEMP_FILES,
    TEMP_DIR,
    GPT_MODEL,
    OPENAI_API_KEY,
    TRANSCRIPTS_DIR
)
from config import PARALLEL_TRANSCRIPTION, MAX_PARALLEL_TRANSCRIPTS
import concurrent.futures
from youtube_api import search_videos_by_topic, fetch_video_details, fetch_channel_details
from data_processor import (
    merge_video_channel_data,
    export_to_excel,
    add_transcript_to_record,
    add_analysis_to_record
)
from audio_processing import download_audio, split_audio_into_chunks
from transcription import transcribe_all_chunks, merge_transcriptions, get_transcript_text
from content_analyzer import analyze_content
from utils import setup_logging, cleanup_files

logger = logging.getLogger(__name__)


def transcribe_video(video_url: str, video_id: str) -> str:
    """
    Download and transcribe a single video.
    
    Args:
        video_url: YouTube video URL
        video_id: Video ID for file naming
        
    Returns:
        Transcript text
    """
    temp_files = []
    
    try:
        # Create video-specific temp directory
        video_temp_dir = Path(TEMP_DIR) / video_id
        video_temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Download audio
        logger.info(f"  → Downloading audio for {video_id}...")
        audio_file = download_audio(
            video_url,
            output_dir=str(video_temp_dir),
            filename=f"{video_id}.wav"
        )
        temp_files.append(audio_file)
        
        # Split into chunks
        logger.info(f"  → Splitting audio into chunks...")
        chunks = split_audio_into_chunks(
            audio_file,
            chunk_duration=CHUNK_DURATION,
            output_dir=video_temp_dir / "chunks",
            overlap=CHUNK_OVERLAP
        )
        temp_files.extend([chunk[0] for chunk in chunks])
        
        # Transcribe
        logger.info(f"  → Transcribing with Whisper ({WHISPER_MODEL})...")
        results = transcribe_all_chunks(chunks, model_size=WHISPER_MODEL)
        
        # Merge and extract text
        segments = merge_transcriptions(results)
        transcript_text = get_transcript_text(segments)
        
        # Save transcript to file
        transcript_dir = Path(TRANSCRIPTS_DIR)
        transcript_dir.mkdir(parents=True, exist_ok=True)
        transcript_file = transcript_dir / f"{video_id}.txt"
        
        with transcript_file.open('w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        logger.info(f"  ✓ Transcript saved: {transcript_file}")
        
        # Cleanup
        if CLEANUP_TEMP_FILES:
            cleanup_files(temp_files, logger)
            # Remove temp directory
            try:
                video_temp_dir.rmdir()
            except:
                pass
        
        return transcript_text
        
    except Exception as e:
        logger.error(f"  ✗ Transcription failed for {video_id}: {e}")
        if CLEANUP_TEMP_FILES:
            cleanup_files(temp_files, logger)
        return ""


def analyze_transcript(transcript: str, country: str, language: str) -> Dict[str, str]:
    """
    Analyze transcript using GPT.
    
    Args:
        transcript: Video transcript text
        country: Country/region context
        language: Video language
        
    Returns:
        Analysis results dictionary
    """
    try:
        if not transcript or len(transcript.strip()) < 50:
            logger.warning("  ⚠ Transcript too short for analysis")
            return {
                "narrative_style": "N/A",
                "target_audience": "N/A",
                "specific_niche": "N/A",
                "content_category": "N/A",
                "tone": "N/A"
            }
        
        logger.info(f"  → Analyzing content with GPT ({GPT_MODEL})...")
        analysis = analyze_content(
            transcript=transcript,
            country=country,
            default_language=language,
            api_key=OPENAI_API_KEY,
            model=GPT_MODEL
        )
        
        logger.info(f"  ✓ Analysis complete: {analysis.get('content_category')}")
        return analysis
        
    except Exception as e:
        logger.error(f"  ✗ Analysis failed: {e}")
        return {
            "narrative_style": "Error",
            "target_audience": "Error",
            "specific_niche": "Error",
            "content_category": "Error",
            "tone": "Error"
        }


def process_video_with_transcript(record: Dict, index: int, total: int) -> None:
    """
    Process a single video record: transcribe and analyze.
    
    Args:
        record: Video record dictionary
        index: Current video index (1-based)
        total: Total number of videos
    """
    video_url = record["Video URL"]
    video_id = video_url.split("v=")[-1].split("&")[0]
    
    logger.info(f"\n[{index}/{total}] Processing video: {video_id}")
    logger.info(f"  Title: {record['Video Title'][:60]}...")
    
    # Transcribe video
    transcript = transcribe_video(video_url, video_id)
    add_transcript_to_record(record, transcript)
    
    # Analyze transcript if available
    if transcript:
        analysis = analyze_transcript(
            transcript,
            country=record["Country"],
            language=record["Default Language"]
        )
        add_analysis_to_record(record, analysis)
    else:
        logger.warning(f"  ⚠ Skipping analysis due to missing transcript")


def process_video_record(record: Dict) -> Dict:
    """Worker-friendly function: transcribe and analyze a single record.

    Returns the updated record dictionary.
    """
    # Re-importing utilities inside worker can help avoid pickling issues
    try:
        video_url = record["Video URL"]
        video_id = video_url.split("v=")[-1].split("&")[0]
        print(f"Worker: processing {video_id}")

        transcript = transcribe_video(video_url, video_id)
        # Add transcript to record
        add_transcript_to_record(record, transcript)

        if transcript:
            analysis = analyze_transcript(
                transcript,
                country=record.get("Country", "United States"),
                language=record.get("Default Language", "English")
            )
            add_analysis_to_record(record, analysis)
        else:
            # leave analysis fields empty
            pass
    except Exception as e:
        # Return record with an error marker
        record.setdefault("_error", str(e))
    return record


def main():
    """Main pipeline orchestrator."""
    # Setup logging
    log_file = Path("logs") / "pipeline.log"
    setup_logging(log_file)
    
    print("=" * 80)
    print("INTEGRATED YOUTUBE ANALYTICS PIPELINE")
    print("=" * 80)
    print(f"Whisper Model: {WHISPER_MODEL}")
    print(f"GPT Model: {GPT_MODEL}")
    print(f"Topics: {', '.join(TOPICS)}")
    print("=" * 80)
    
    all_records = []

    # PHASE 1: Fetch YouTube data
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1: FETCHING YOUTUBE DATA")
    logger.info("=" * 80)
    
    for topic in TOPICS:
        print(f"\n📊 Processing Topic: {topic}")
        
        # Search for videos
        video_ids = search_videos_by_topic(topic)
        print(f"  → Found {len(video_ids)} videos")
        
        if not video_ids:
            continue

        # Fetch video details
        videos_data, channel_ids = fetch_video_details(video_ids)
        
        # Fetch channel details
        channel_lookup = fetch_channel_details(channel_ids)
        
        # Merge data
        records = merge_video_channel_data(topic, videos_data, channel_lookup)
        all_records.extend(records)
        
        print(f"  ✓ Fetched {len(records)} video records")
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)

    print(f"\n✓ Phase 1 Complete: {len(all_records)} total videos collected")
    
    # Save intermediate results
    export_to_excel(all_records, filename="youtube_data_intermediate.xlsx")
    print(f"  → Intermediate data saved to: youtube_data_intermediate.xlsx")
    
    # PHASE 2: Transcribe videos
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: TRANSCRIBING VIDEOS")
    logger.info("=" * 80)
    
    total_videos = len(all_records)

    if PARALLEL_TRANSCRIPTION and total_videos > 0:
        max_workers = max(1, int(MAX_PARALLEL_TRANSCRIPTS))
        print(f"Starting parallel transcription with up to {max_workers} workers")

        # Submit all records to the process pool and update as they complete
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as exe:
            future_to_url = {exe.submit(process_video_record, rec): rec["Video URL"] for rec in all_records}

            completed = 0
            try:
                for fut in concurrent.futures.as_completed(future_to_url):
                    video_url = future_to_url[fut]
                    try:
                        updated = fut.result()
                    except Exception as e:
                        logger.error(f"Worker failed for {video_url}: {e}")
                        updated = None

                    # Replace the matching record in all_records
                    for i, r in enumerate(all_records):
                        if r.get("Video URL") == video_url:
                            if updated:
                                all_records[i] = updated
                            break

                    completed += 1
                    # Save progress every 2 completed tasks
                    if completed % 2 == 0:
                        export_to_excel(all_records, filename="youtube_data_progress.xlsx")
                        logger.info(f"\n  💾 Progress saved ({completed}/{total_videos} completed)")

            except KeyboardInterrupt:
                logger.warning("\n⚠ Pipeline interrupted by user (parallel)")
                export_to_excel(all_records, filename="youtube_data_partial.xlsx")
                print(f"\n  → Partial results saved to: youtube_data_partial.xlsx")
                return
    else:
        # Sequential fallback
        for idx, record in enumerate(all_records, 1):
            try:
                process_video_with_transcript(record, idx, total_videos)
                
                # Save progress every 2 videos
                if idx % 2 == 0:
                    export_to_excel(all_records, filename="youtube_data_progress.xlsx")
                    logger.info(f"\n  💾 Progress saved ({idx}/{total_videos} videos)")
                    
            except KeyboardInterrupt:
                logger.warning("\n⚠ Pipeline interrupted by user")
                export_to_excel(all_records, filename="youtube_data_partial.xlsx")
                print(f"\n  → Partial results saved to: youtube_data_partial.xlsx")
                return
            except Exception as e:
                logger.error(f"  ✗ Failed to process video {idx}: {e}")
                continue

    # PHASE 3: Final export
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 3: EXPORTING FINAL RESULTS")
    logger.info("=" * 80)
    
    export_to_excel(all_records)
    
    # Statistics
    transcribed = sum(1 for r in all_records if r["Transcript"])
    analyzed = sum(1 for r in all_records if r["Content Category"] and r["Content Category"] != "N/A")
    
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE!")
    print("=" * 80)
    print(f"Total Videos: {len(all_records)}")
    print(f"Transcribed: {transcribed}")
    print(f"Analyzed: {analyzed}")
    print(f"Output File: {OUTPUT_FILENAME}")
    print("=" * 80)


if __name__ == "__main__":
    # Check for required API keys
    if not os.getenv("YOUTUBE_API_KEY"):
        print("ERROR: YOUTUBE_API_KEY not found in environment")
        print("Please set it in your .env file")
        exit(1)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not found")
        print("Content analysis will be skipped")
        print("Press Ctrl+C to cancel, or Enter to continue...")
        input()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
    except Exception as e:
        print(f"\n\nPipeline failed: {e}")
        logging.error(f"Pipeline failed: {e}", exc_info=True)
