"""YouTube API interaction module."""
import requests
import json
from typing import List, Dict, Set, Tuple
from config import (
    YOUTUBE_API_KEY,
    YOUTUBE_SEARCH_URL,
    YOUTUBE_VIDEOS_URL,
    YOUTUBE_CHANNELS_URL,
    VIDEOS_PER_TOPIC
)


def load_language_mapping() -> Dict[str, str]:
    """Load language code to language name mapping from JSON file."""
    try:
        with open('languages.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: languages.json not found. Using raw language codes.")
        return {}


def extract_niches_from_topics(topic_categories: List[str]) -> str:
    """
    Extract niche names from Wikipedia topic URLs.
    
    Args:
        topic_categories: List of Wikipedia URLs
        
    Returns:
        Comma-separated string of niche names
    """
    if not topic_categories:
        return "N/A"
    
    niches = []
    for url in topic_categories:
        # Extract the last part after the last '/'
        niche = url.split('/')[-1]
        # Replace underscores with spaces
        niche = niche.replace('_', ' ')
        niches.append(niche)
    
    return ", ".join(niches)


def _extract_niches_from_topics(topic_categories: List[str]) -> str:
    """
    Extract and format topic niches from Wikipedia URLs.
    
    Args:
        topic_categories: List of Wikipedia URLs
        
    Returns:
        Comma-separated string of topic names
    """
    if not topic_categories:
        return "N/A"
    
    niches = []
    for url in topic_categories:
        # Extract the topic name from Wikipedia URL
        # e.g., "https://en.wikipedia.org/wiki/Action-adventure_game" -> "Action-adventure_game"
        if "/wiki/" in url:
            topic = url.split("/wiki/")[-1]
            niches.append(topic)
    
    return ", ".join(niches) if niches else "N/A"


def search_videos_by_topic(topic: str) -> List[str]:
    """
    Search for videos by topic keywords.
    
    Args:
        topic: The search query/topic
        
    Returns:
        List of video IDs
    """
    params = {
        "part": "id",
        "q": topic,
        "type": "video",
        "maxResults": VIDEOS_PER_TOPIC,
        "key": YOUTUBE_API_KEY
    }
    
    response = requests.get(YOUTUBE_SEARCH_URL, params=params)
    
    if response.status_code != 200:
        print(f"Error searching topic '{topic}': {response.text}")
        return []
    
    data = response.json()
    video_ids = [item['id']['videoId'] for item in data.get('items', [])]
    
    return video_ids


def fetch_video_details(video_ids: List[str]) -> Tuple[List[Dict], Set[str]]:
    """
    Batch fetch video statistics and metadata.
    
    Args:
        video_ids: List of video IDs to fetch details for
        
    Returns:
        Tuple of (video_data_list, channel_ids_set)
    """
    if not video_ids:
        return [], set()

    # Load language mapping once
    language_map = load_language_mapping()

    params = {
        "part": "snippet,statistics,topicDetails",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY
    }
    
    response = requests.get(YOUTUBE_VIDEOS_URL, params=params)
    data = response.json()
    
    video_data_list = []
    channel_ids = set()

    for item in data.get('items', []):
        stats = item.get('statistics', {})
        snippet = item.get('snippet', {})
        topic_details = item.get('topicDetails', {})
        
        # Extract default audio language and convert to full name
        language_code = snippet.get('defaultAudioLanguage', 'N/A')
        if language_code != 'N/A' and language_code in language_map:
            default_language = language_map[language_code]
        else:
            default_language = language_code  # Use code if not found in mapping
        
        # Extract and format topic categories
        topic_categories = topic_details.get('topicCategories', [])
        specific_niches = _extract_niches_from_topics(topic_categories)
        
        video_obj = {
            "id": item['id'],
            "video_url": f"https://www.youtube.com/watch?v={item['id']}",
            "title": snippet.get('title'),
            "upload_date": snippet.get('publishedAt'),
            "thumbnail": snippet.get('thumbnails', {}).get('high', {}).get('url'),
            "views": stats.get('viewCount', 0),
            "likes": stats.get('likeCount', 0),
            "comment_count": stats.get('commentCount', 0),
            "channel_id": snippet.get('channelId'),
            "default_language": default_language,
            "specific_niches": specific_niches
        }
        
        video_data_list.append(video_obj)
        if video_obj['channel_id']:
            channel_ids.add(video_obj['channel_id'])
            
    return video_data_list, channel_ids


def fetch_channel_details(channel_ids: Set[str]) -> Dict[str, Dict]:
    """
    Batch fetch channel statistics and metadata.
    
    Args:
        channel_ids: Set of channel IDs to fetch details for
        
    Returns:
        Dictionary mapping channel_id to channel details
    """
    if not channel_ids:
        return {}

    ids_list = list(channel_ids)[:50]  # API limit
    
    params = {
        "part": "snippet,statistics",
        "id": ",".join(ids_list),
        "key": YOUTUBE_API_KEY
    }
    
    response = requests.get(YOUTUBE_CHANNELS_URL, params=params)
    data = response.json()
    
    channel_map = {}
    
    for item in data.get('items', []):
        stats = item.get('statistics', {})
        snippet = item.get('snippet', {})
        
        channel_obj = {
            "subscribers": stats.get('subscriberCount', 0),
            "country": snippet.get('country', "N/A")
        }
        channel_map[item['id']] = channel_obj
        
    return channel_map
