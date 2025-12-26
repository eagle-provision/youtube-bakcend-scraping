"""Configuration module for YouTube Analytics application."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_KEY = os.getenv("YOUTUBE_API_KEY")

# Search Configuration
TOPICS = [
    "Artificial Intelligence",
    "Machine Learning",
    "Gaming",
    "cartoons",
    "Finance"
]

VIDEOS_PER_TOPIC = 50

# API Endpoints
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"

# Output Configuration
OUTPUT_FILENAME = "youtube_data_analysis.xlsx"

# API Rate Limiting
REQUEST_DELAY = 1  # seconds between requests
