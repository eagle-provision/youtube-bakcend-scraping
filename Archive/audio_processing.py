"""Audio download and chunking for transcription pipeline."""

import subprocess
import logging
from pathlib import Path
from typing import List, Tuple
import yt_dlp

logger = logging.getLogger(__name__)


def download_audio(video_url: str, output_dir: str = "temp", 
                  filename: str = "audio.wav") -> str:
    """Download and convert video to WAV audio."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    audio_file = output_path / filename
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': str(audio_file.with_suffix('')),
        'quiet': True,
    }
    
    logger.info(f"Downloading from {video_url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        logger.info(f"Downloaded: {info.get('title', 'unknown')}")
    
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio not created at {audio_file}")
    
    size_mb = audio_file.stat().st_size / (1024 * 1024)
    logger.info(f"Audio ready: {audio_file} ({size_mb:.1f} MB)")
    return str(audio_file)


def _get_duration(audio_file: str) -> float:
    """Get audio duration using ffprobe."""
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def split_audio_into_chunks(
    audio_file: str,
    chunk_duration: int = 45,
    output_dir: Path | str = "temp/chunks",
    overlap: int = 2
) -> List[Tuple[str, float, float]]:
    """Split audio into overlapping chunks for transcription."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    duration = _get_duration(audio_file)
    logger.info(f"Splitting {duration:.1f}s audio into {chunk_duration}s chunks")
    
    chunks = []
    start = 0.0
    idx = 0
    
    while start < duration:
        end = min(start + chunk_duration, duration)
        
        # Skip if remaining duration is too short (less than overlap)
        if end - start < overlap:
            break
            
        chunk_file = output_path / f"chunk_{idx:04d}.wav"
        
        subprocess.run([
            'ffmpeg', '-i', audio_file, '-ss', str(start), '-t', str(end - start),
            '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', '-y', str(chunk_file)
        ], capture_output=True, check=True)
        
        chunks.append((str(chunk_file), start, end))
        logger.info(f"Chunk {idx}: {start:.1f}s - {end:.1f}s")
        
        # Break if we've reached the end
        if end >= duration:
            break
            
        start = end - overlap
        idx += 1
    
    logger.info(f"Created {len(chunks)} chunks")
    return chunks
