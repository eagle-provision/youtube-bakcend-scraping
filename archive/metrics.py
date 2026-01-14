"""
Metrics calculation module for YouTube analytics.
Handles computation of engagement rates, ratios, and performance indicators.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


def duration_to_seconds(duration):
    """
    Convert MM:SS or duration format to seconds.
    
    Args:
        duration: Duration in MM:SS format or seconds (int/float)
        
    Returns:
        int: Duration in seconds
    """
    if pd.isna(duration):
        return 0
    
    # If already numeric, return as int
    if isinstance(duration, (int, float)):
        return int(duration)
    
    # If string in MM:SS format
    if isinstance(duration, str):
        try:
            parts = duration.split(':')
            if len(parts) == 2:
                minutes, seconds = int(parts[0]), int(parts[1])
                return minutes * 60 + seconds
            else:
                return 0
        except (ValueError, IndexError):
            return 0
    
    return 0


class ChannelMetrics:
    """Calculate and analyze channel-level metrics."""
    
    @staticmethod
    def calculate_engagement_metrics(df_channel: pd.Series) -> Dict:
        """
        Calculate channel-level engagement metrics.
        
        Args:
            df_channel: Channel data series
            
        Returns:
            dict: Engagement metrics
        """
        metrics = {}
        
        try:
            subscribers = df_channel.get('subscribers', 0)
            total_views = df_channel.get('total_views', 0)
            
            if total_views > 0:
                # View to subscriber ratio
                metrics['views_per_subscriber'] = round(total_views / subscribers, 2) if subscribers > 0 else 0
                
                # Average views per video (approximate)
                video_count = df_channel.get('video_count', 1)
                metrics['avg_views_per_video'] = round(total_views / video_count, 0) if video_count > 0 else 0
            
            return metrics
        except Exception as e:
            print(f"Error calculating engagement metrics: {e}")
            return {}
    
    @staticmethod
    def calculate_content_metrics(df_channel: pd.Series) -> Dict:
        """
        Calculate content production metrics.
        
        Args:
            df_channel: Channel data series
            
        Returns:
            dict: Content metrics
        """
        metrics = {}
        
        try:
            video_count = df_channel.get('video_count', 0)
            shorts_count = df_channel.get('shorts_count', 0)
            
            total_content = video_count + shorts_count
            if total_content > 0:
                metrics['total_content_pieces'] = total_content
                metrics['shorts_percentage'] = round((shorts_count / total_content) * 100, 2)
                metrics['regular_videos_percentage'] = round((video_count / total_content) * 100, 2)
            
            metrics['shorts_count'] = shorts_count
            metrics['video_count'] = video_count
            
            return metrics
        except Exception as e:
            print(f"Error calculating content metrics: {e}")
            return {}


class VideoMetrics:
    """Calculate and analyze video-level metrics."""
    
    @staticmethod
    def calculate_engagement_rate(df_videos: pd.DataFrame) -> pd.Series:
        """
        Calculate engagement rate for each video.
        Engagement Rate = (Likes + Comments) / Views
        
        Args:
            df_videos: Videos dataframe
            
        Returns:
            pd.Series: Engagement rates
        """
        engagement = pd.Series(dtype=float)
        
        try:
            total_interactions = df_videos['like_count'].fillna(0) + df_videos['comment_count'].fillna(0)
            views = df_videos['view_count'].fillna(0)
            
            engagement = (total_interactions / views.replace(0, np.nan)) * 100
            engagement = engagement.fillna(0).round(4)
            
            return engagement
        except Exception as e:
            print(f"Error calculating engagement rate: {e}")
            return engagement
    
    @staticmethod
    def calculate_like_ratio(df_videos: pd.DataFrame) -> pd.Series:
        """
        Calculate like ratio.
        Like Ratio = Likes / (Likes + Comments)
        
        Args:
            df_videos: Videos dataframe
            
        Returns:
            pd.Series: Like ratios
        """
        ratio = pd.Series(dtype=float)
        
        try:
            likes = df_videos['like_count'].fillna(0)
            comments = df_videos['comment_count'].fillna(0)
            total_interaction = likes + comments
            
            ratio = (likes / total_interaction.replace(0, np.nan)) * 100
            ratio = ratio.fillna(0).round(2)
            
            return ratio
        except Exception as e:
            print(f"Error calculating like ratio: {e}")
            return ratio
    
    @staticmethod
    def calculate_comment_ratio(df_videos: pd.DataFrame) -> pd.Series:
        """
        Calculate comment ratio.
        Comment Ratio = Comments / (Likes + Comments)
        
        Args:
            df_videos: Videos dataframe
            
        Returns:
            pd.Series: Comment ratios
        """
        ratio = pd.Series(dtype=float)
        
        try:
            likes = df_videos['like_count'].fillna(0)
            comments = df_videos['comment_count'].fillna(0)
            total_interaction = likes + comments
            
            ratio = (comments / total_interaction.replace(0, np.nan)) * 100
            ratio = ratio.fillna(0).round(2)
            
            return ratio
        except Exception as e:
            print(f"Error calculating comment ratio: {e}")
            return ratio
    
    @staticmethod
    def calculate_per_minute_engagement(df_videos: pd.DataFrame) -> pd.Series:
        """
        Calculate engagement per minute.
        Engagement per Minute = (Likes + Comments) / (Duration in minutes)
        
        Args:
            df_videos: Videos dataframe
            
        Returns:
            pd.Series: Engagement per minute
        """
        engagement_per_min = pd.Series(dtype=float)
        
        try:
            likes = df_videos['like_count'].fillna(0)
            comments = df_videos['comment_count'].fillna(0)
            duration = df_videos['duration'].fillna(0)
            
            # Convert duration from MM:SS format to seconds
            duration_seconds = duration.apply(duration_to_seconds)
            
            total_engagement = likes + comments
            duration_minutes = (duration_seconds / 60).replace(0, np.nan)
            
            engagement_per_min = total_engagement / duration_minutes
            engagement_per_min = engagement_per_min.fillna(0).round(2)
            
            return engagement_per_min
        except Exception as e:
            print(f"Error calculating per-minute engagement: {e}")
            return engagement_per_min
    
    @staticmethod
    def categorize_video_performance(df_videos: pd.DataFrame) -> pd.Series:
        """
        Categorize videos as High/Medium/Low performers based on view count.
        
        Args:
            df_videos: Videos dataframe
            
        Returns:
            pd.Series: Performance categories
        """
        categories = pd.Series(dtype=str)
        
        try:
            views = df_videos['view_count'].fillna(0)
            
            if len(views) < 3:
                # Not enough data for meaningful categorization
                return pd.Series(['Medium'] * len(views), index=views.index)
            
            q75 = views.quantile(0.75)
            q25 = views.quantile(0.25)
            
            # Ensure bin edges are unique
            bins = [0]
            if q25 > 0 and q25 not in bins:
                bins.append(q25)
            if q75 > q25 and q75 not in bins:
                bins.append(q75)
            bins.append(float('inf'))
            
            # Only categorize if we have proper bins
            if len(bins) >= 3:
                categories = pd.cut(views, bins=bins, labels=['Low', 'Medium', 'High'][:len(bins)-1])
            else:
                categories = pd.Series(['Medium'] * len(views), index=views.index)
            
            return categories
        except Exception as e:
            print(f"Error categorizing video performance: {e}")
            return pd.Series(['Medium'] * len(df_videos), index=df_videos.index)


class ContentTypeAnalysis:
    """Analyze performance differences between content types."""
    
    @staticmethod
    def compare_shorts_vs_videos(df_videos: pd.DataFrame) -> Dict:
        """
        Compare performance metrics: Shorts vs Regular Videos.
        
        Args:
            df_videos: Videos dataframe
            
        Returns:
            dict: Comparison metrics
        """
        comparison = {}
        
        try:
            shorts = df_videos[df_videos['is_short'] == True]
            videos = df_videos[df_videos['is_short'] == False]
            
            if len(shorts) > 0:
                comparison['shorts'] = {
                    'count': len(shorts),
                    'avg_views': shorts['view_count'].mean(),
                    'avg_likes': shorts['like_count'].mean(),
                    'avg_comments': shorts['comment_count'].mean(),
                    'avg_engagement_rate': (
                        (shorts['like_count'] + shorts['comment_count']) / 
                        shorts['view_count'].replace(0, np.nan) * 100
                    ).mean()
                }
            
            if len(videos) > 0:
                comparison['videos'] = {
                    'count': len(videos),
                    'avg_views': videos['view_count'].mean(),
                    'avg_likes': videos['like_count'].mean(),
                    'avg_comments': videos['comment_count'].mean(),
                    'avg_engagement_rate': (
                        (videos['like_count'] + videos['comment_count']) / 
                        videos['view_count'].replace(0, np.nan) * 100
                    ).mean()
                }
            
            # Calculate percentage differences
            if 'shorts' in comparison and 'videos' in comparison:
                shorts_avg_views = comparison['shorts']['avg_views']
                videos_avg_views = comparison['videos']['avg_views']
                
                if videos_avg_views > 0:
                    comparison['view_difference_percent'] = round(
                        ((shorts_avg_views - videos_avg_views) / videos_avg_views) * 100, 2
                    )
            
            return comparison
        except Exception as e:
            print(f"Error comparing shorts vs videos: {e}")
            return {}
    
    @staticmethod
    def optimal_video_length(df_videos: pd.DataFrame) -> Dict:
        """
        Determine optimal video length for engagement.
        
        Args:
            df_videos: Videos dataframe
            
        Returns:
            dict: Video length analysis
        """
        analysis = {}
        
        try:
            # Create duration bins (in minutes)
            df_videos_copy = df_videos.copy()
            # Convert MM:SS format to seconds first
            df_videos_copy['duration_seconds'] = df_videos_copy['duration'].apply(duration_to_seconds)
            df_videos_copy['duration_minutes'] = df_videos_copy['duration_seconds'] / 60
            
            # Categorize by length
            df_videos_copy['length_category'] = pd.cut(
                df_videos_copy['duration_minutes'],
                bins=[0, 5, 10, 15, 30, float('inf')],
                labels=['0-5 min', '5-10 min', '10-15 min', '15-30 min', '30+ min']
            )
            
            # Calculate metrics per category
            for category in df_videos_copy['length_category'].unique():
                if pd.isna(category):
                    continue
                
                category_videos = df_videos_copy[df_videos_copy['length_category'] == category]
                
                if len(category_videos) > 0:
                    analysis[str(category)] = {
                        'count': len(category_videos),
                        'avg_views': round(category_videos['view_count'].mean(), 0),
                        'avg_engagement_rate': round(
                            ((category_videos['like_count'] + category_videos['comment_count']) /
                             category_videos['view_count'].replace(0, np.nan) * 100).mean(), 4
                        )
                    }
            
            return analysis
        except Exception as e:
            print(f"Error analyzing video length: {e}")
            return {}
