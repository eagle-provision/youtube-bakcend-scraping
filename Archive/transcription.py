"""Whisper-based audio transcription with timestamp management."""

import logging
import ssl
import certifi
from pathlib import Path
from typing import List, Dict, Tuple
import whisper
import torch

from utils import format_timestamp

logger = logging.getLogger(__name__)

# Fix SSL certificate verification for macOS
ssl._create_default_https_context = ssl._create_unverified_context


def load_whisper_model(model_size: str = "small") -> whisper.Whisper:
    """Load Whisper model with GPU support if available."""
    # Check for MPS (Apple Silicon), CUDA (NVIDIA), or fallback to CPU
    if torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    logger.info(f"Loading Whisper '{model_size}' on {device}")
    return whisper.load_model(model_size, device=device)


def transcribe_chunk(model: whisper.Whisper, audio_file: str, 
                    language: str = None) -> Dict:
    """Transcribe single audio chunk."""
    result = model.transcribe(
        audio_file, 
        language=language, 
        word_timestamps=False,  # Faster without word-level timestamps
        verbose=False,
        fp16=torch.cuda.is_available()  # Only use fp16 on CUDA, not on MPS
    )
    if not language:
        logger.info(f"Detected: {result.get('language', 'unknown')}")
    return result


def transcribe_all_chunks(
    chunks: List[Tuple[str, float, float]],
    model_size: str = "small",
    language: str = None
) -> List[Dict]:
    """Transcribe all audio chunks (loads model once, reuses for all chunks)."""
    # Load model ONCE at the start
    logger.info(f"Loading Whisper model once for {len(chunks)} chunks...")
    model = load_whisper_model(model_size)
    logger.info("Model loaded. Starting transcription...")
    
    results = []
    
    for idx, (path, start, end) in enumerate(chunks, 1):
        logger.info(f"Transcribing chunk {idx}/{len(chunks)} [{start:.1f}s - {end:.1f}s]")
        try:
            result = transcribe_chunk(model, path, language)
            results.append({
                'chunk_index': idx - 1,
                'chunk_start': start,
                'chunk_end': end,
                'result': result
            })
            logger.info(f"[OK] Chunk {idx} complete")
        except Exception as e:
            logger.error(f"[FAIL] Chunk {idx} failed: {e}")
            continue
    
    logger.info(f"[OK] Transcribed {len(results)}/{len(chunks)} chunks successfully")
    return results


def merge_transcriptions(results: List[Dict]) -> List[Tuple[float, float, str]]:
    """Merge chunk transcriptions into single timeline with absolute timestamps."""
    segments = []
    
    for chunk in results:
        offset = chunk['chunk_start']
        for seg in chunk['result'].get('segments', []):
            text = seg['text'].strip()
            if text:
                segments.append((offset + seg['start'], offset + seg['end'], text))
    
    segments.sort(key=lambda x: x[0])
    logger.info(f"Merged {len(segments)} segments")
    return segments


def save_transcript(segments: List[Tuple[float, float, str]], 
                   output_file: Path | str, 
                   include_timestamps: bool = True) -> None:
    """Save transcript to file."""
    output_file = Path(output_file)
    logger.info(f"Saving transcript to {output_file}")
    
    with output_file.open('w', encoding='utf-8') as f:
        for start, end, text in segments:
            if include_timestamps:
                f.write(f"[{format_timestamp(start)} --> {format_timestamp(end)}]\n")
            f.write(f"{text}\n\n")


def get_transcript_text(segments: List[Tuple[float, float, str]]) -> str:
    """Convert segments to plain text transcript without timestamps."""
    return " ".join([text for _, _, text in segments])
