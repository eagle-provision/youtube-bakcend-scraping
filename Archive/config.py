"""Configuration module for YouTube Analytics application."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Search Configuration
TOPICS = [
    "Artificial Intelligence",
    "Machine Learning",
    "Gaming",
    "cartoons",
    "Finance"
]

VIDEOS_PER_TOPIC = 3

# API Endpoints
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"

# Transcription Configuration
WHISPER_MODEL = "small"  # Options: tiny, base, small, medium, large
CHUNK_DURATION = 45  # seconds
CHUNK_OVERLAP = 2  # seconds
CLEANUP_TEMP_FILES = True
TEMP_DIR = "temp"

# Content Analysis Configuration
GPT_MODEL = "gpt-4o-mini"  # Options: gpt-4o-mini, gpt-4o, gpt-3.5-turbo

# Output Configuration
OUTPUT_FILENAME = "youtube_data_complete.xlsx"
TRANSCRIPTS_DIR = "transcripts"

# API Rate Limiting
REQUEST_DELAY = 1  # seconds between requests

# Parallel transcription settings
# On macOS with Apple Silicon (MPS) loading multiple heavy models in parallel
# can be memory intensive. Tune `MAX_PARALLEL_TRANSCRIPTS` based on your
# machine (2 is a safe default for many Macs). Set to 1 to force sequential.
PARALLEL_TRANSCRIPTION = True
MAX_PARALLEL_TRANSCRIPTS = 3
