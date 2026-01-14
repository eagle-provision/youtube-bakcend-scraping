# Configuration and Constants for YouTube Analytics Scraper

# URLs
YOUTUBE_BASE_URL = "https://www.youtube.com"
CHANNEL_ABOUT_PATH = "/about"
CHANNEL_VIDEOS_PATH = "/videos"
CHANNEL_SHORTS_PATH = "/shorts"

# Selenium Configuration
BROWSER_WAIT_TIME = 10  # seconds
DYNAMIC_CONTENT_WAIT = 5  # seconds
SCROLL_DELAY = 2  # seconds
REQUEST_DELAY = 2  # seconds between requests

# Scraping Parameters
MAX_VIDEOS_DEFAULT = 50
VIDEO_LIMIT_TEST = 1  # For testing purposes

# Chrome Options
CHROME_OPTIONS = [
    '--headless=new',  # Use new headless mode (more stable)
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled',  
    '--disable-software-rasterizer',
    '--disable-extensions',
    '--disable-logging',
    '--log-level=3',  # Suppress Chrome logs
    '--window-size=1920,1080',  # Set consistent window size
    '--disable-web-security',
    '--ignore-certificate-errors',
    'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
]

# XPath Selectors
XPATH_SUBSCRIBERS = "//span[contains(text(), 'subscribers')]"
XPATH_VIEWS = "//span[contains(text(), 'views')]"
XPATH_JOINED_DATE = "//span[contains(text(), 'Joined')]"

# CSS Selectors
CSS_SUBSCRIBER_COUNT = 'yt-formatted-string#subscriber-count'

# Export Configuration
EXCEL_OUTPUT_FILE = 'data/processed/youtube_analytics_scraped.xlsx'
SHEET_CHANNEL_STATIC = 'Static_Data'
SHEET_CHANNEL_EVOLVING = 'Evolving_Data'
SHEET_VIDEOS_DATA = 'Videos_Data'
SHEET_SHORTS_DATA = 'Shorts_Data'

# Image Domains
IMAGE_DOMAIN_YT3 = 'yt3.googleusercontent.com'
IMAGE_DOMAIN_YT4 = 'yt4.googleusercontent.com'
IMAGE_DOMAIN_THUMBNAIL = 'i.ytimg.com'

# Data Field Definitions (3-Part Structure per PDF)

# PART 1: STATIC DATA (Channel-level, rarely changes)
CHANNEL_STATIC_FIELDS = [
    'channel_id',              # YouTube channel ID (unique identifier)
    'channel_url',             # Channel URL/handle
    'channel_handle',          # Channel @handle
    'channel_title',           # Channel name/title
    'channel_description',     # Channel description
    'creation_date',           # Channel activation/first upload date
    'banner_url',              # Banner image URL
    'profile_pic_url',         # Profile picture URL
    'country',                 # Channel country/residence (if visible)
    'default_language',        # Channel language
    'monetization_status'      # Monetization status (placeholder for now)
]

# PART 2: EVOLVING DATA (Channel-level, updated daily)
CHANNEL_EVOLVING_FIELDS = [
    'channel_id',              # YouTube channel ID (for linking)
    'channel_handle',          # Channel @handle (for reference)
    'scrape_date',             # Date of data collection
    'subscribers',             # Total subscribers (daily)
    'total_views',             # Total channel views (daily)
    'video_count',             # Total long-form video count
    'shorts_count',            # Total Shorts count
    'total_content_count',     # Total videos + shorts
    'last_posted_date',        # Date of last upload
    'daily_subscriber_change', # Daily subscriber change (computed)
    'daily_views_change',      # Daily views change (computed)
    'growth_rate'              # Growth rate percentage (computed)
]

# PART 3: VIDEO DATA (Video-level)
VIDEO_FIELDS = [
    'channel_id',              # YouTube channel ID (for linking)
    'video_id',                # YouTube video ID
    'url',                     # Video URL
    'title',                   # Video title
    'description',             # Video description
    'view_count',              # View count
    'like_count',              # Like count (engagement metric)
    'comment_count',           # Comment count (engagement metric)
    'upload_date',             # Upload date
    'duration',                # Video duration (MM:SS format)
    'thumbnail_url',           # Thumbnail URL
    'is_short'                 # Boolean: is it a Short?
]

# Legacy combined fields for backward compatibility during migration
CHANNEL_FIELDS = CHANNEL_STATIC_FIELDS + [
    'scrape_date',
    'subscribers',
    'total_views', 
    'video_count',
    'shorts_count',
    'last_posted_date'
]

# Logging
DEBUG_MODE = True
LOG_LEVEL = 'INFO'
