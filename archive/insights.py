"""
Insights generation module for YouTube analytics.
Produces actionable insights from analyzed data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from metrics import duration_to_seconds


class InsightGenerator:
    """Generate insights from channel and video data."""
    
    @staticmethod
    def identify_top_performers(df_videos: pd.DataFrame, n: int = 5) -> List[Dict]:
        """
        Identify top performing videos.
        
        Args:
            df_videos: Videos dataframe
            n: Number of top videos to return
            
        Returns:
            list: Top videos with metrics
        """
        try:
            top_videos = df_videos.nlargest(n, 'view_count')[
                ['title', 'view_count', 'like_count', 'comment_count', 'upload_date']
            ].to_dict('records')
            
            insights = []
            for rank, video in enumerate(top_videos, 1):
                insights.append({
                    'rank': rank,
                    'title': video['title'][:50],
                    'views': f"{video['view_count']:,}",
                    'likes': f"{video['like_count']:,}",
                    'comments': f"{video['comment_count']:,}",
                    'uploaded': video['upload_date']
                })
            
            return insights
        except Exception as e:
            print(f"Error identifying top performers: {e}")
            return []
    
    @staticmethod
    def identify_underperformers(df_videos: pd.DataFrame, n: int = 5) -> List[Dict]:
        """
        Identify underperforming videos.
        
        Args:
            df_videos: Videos dataframe
            n: Number of underperforming videos to return
            
        Returns:
            list: Underperforming videos with metrics
        """
        try:
            bottom_videos = df_videos.nsmallest(n, 'view_count')[
                ['title', 'view_count', 'like_count', 'comment_count', 'upload_date']
            ].to_dict('records')
            
            insights = []
            for rank, video in enumerate(bottom_videos, 1):
                insights.append({
                    'rank': rank,
                    'title': video['title'][:50],
                    'views': f"{video['view_count']:,}",
                    'likes': f"{video['like_count']:,}",
                    'comments': f"{video['comment_count']:,}",
                    'uploaded': video['upload_date']
                })
            
            return insights
        except Exception as e:
            print(f"Error identifying underperformers: {e}")
            return []
    
    @staticmethod
    def analyze_channel_health(df_channel: pd.Series, df_videos: pd.DataFrame) -> Dict:
        """
        Generate overall channel health assessment.
        
        Args:
            df_channel: Channel data series
            df_videos: Videos dataframe
            
        Returns:
            dict: Health indicators
        """
        health = {}
        
        try:
            # Subscriber engagement
            avg_engagement = (
                (df_videos['like_count'] + df_videos['comment_count']) /
                df_videos['view_count'].replace(0, np.nan) * 100
            ).mean()
            
            health['avg_engagement_rate'] = f"{avg_engagement:.4f}%"
            health['engagement_health'] = "Excellent" if avg_engagement > 1 else "Good" if avg_engagement > 0.5 else "Needs Work"
            
            # Content consistency
            if len(df_videos) > 0:
                views_std = df_videos['view_count'].std()
                views_mean = df_videos['view_count'].mean()
                
                consistency_ratio = views_std / views_mean if views_mean > 0 else 0
                health['content_consistency'] = f"{(1 - min(consistency_ratio, 1)) * 100:.1f}%"
                health['consistency_status'] = "Consistent" if consistency_ratio < 1 else "Variable"
            
            # Audience response
            avg_likes = df_videos['like_count'].mean()
            avg_comments = df_videos['comment_count'].mean()
            
            health['avg_likes_per_video'] = f"{avg_likes:,.0f}"
            health['avg_comments_per_video'] = f"{avg_comments:,.0f}"
            
            # Overall health score
            engagement_score = min(avg_engagement * 100, 100)  # Out of 100
            consistency_score = min((1 - consistency_ratio) * 100 if consistency_ratio > 0 else 100, 100)
            
            overall_score = (engagement_score + consistency_score) / 2
            health['overall_health_score'] = f"{overall_score:.1f}/100"
            
            return health
        except Exception as e:
            print(f"Error analyzing channel health: {e}")
            return {}
    
    @staticmethod
    def content_recommendations(df_videos: pd.DataFrame) -> List[str]:
        """
        Generate content strategy recommendations.
        
        Args:
            df_videos: Videos dataframe
            
        Returns:
            list: Recommendations
        """
        recommendations = []
        
        try:
            # Check performance distribution
            views = df_videos['view_count'].values
            views_mean = views.mean()
            views_std = views.std()
            
            # High variability = inconsistent performance
            if views_std > views_mean:
                recommendations.append(
                    "🎯 High view variability detected. Focus on understanding what makes top videos successful."
                )
            
            # Check engagement
            engagement_rate = (
                (df_videos['like_count'] + df_videos['comment_count']) /
                df_videos['view_count'].replace(0, np.nan) * 100
            ).mean()
            
            if engagement_rate < 0.5:
                recommendations.append(
                    "💬 Low engagement rate. Try to boost interaction through CTAs and engaging titles."
                )
            elif engagement_rate > 2:
                recommendations.append(
                    "✅ Excellent engagement rate. Keep up the current content strategy!"
                )
            
            # Check content mix
            shorts_count = len(df_videos[df_videos['is_short'] == True])
            videos_count = len(df_videos[df_videos['is_short'] == False])
            
            if shorts_count == 0 and videos_count > 0:
                recommendations.append(
                    "📱 Consider adding Shorts to your content mix for better reach."
                )
            elif videos_count == 0 and shorts_count > 0:
                recommendations.append(
                    "🎬 Consider adding longer-form videos alongside Shorts for diverse audience."
                )
            
            # Check comment-to-like ratio
            comments = df_videos['comment_count'].sum()
            likes = df_videos['like_count'].sum()
            
            if likes > 0 and comments > 0:
                comment_ratio = (comments / likes) * 100
                if comment_ratio < 1:
                    recommendations.append(
                        "🗨️ Low comment-to-like ratio. Try asking questions in your videos."
                    )
            
            # Check video duration impact
            # Convert MM:SS format to seconds for comparison
            df_videos_copy = df_videos.copy()
            df_videos_copy['duration_seconds'] = df_videos_copy['duration'].apply(duration_to_seconds)
            
            short_videos = df_videos_copy[df_videos_copy['duration_seconds'] < 300]  # < 5 minutes
            long_videos = df_videos_copy[df_videos_copy['duration_seconds'] >= 300]
            
            if len(short_videos) > 0 and len(long_videos) > 0:
                short_avg = short_videos['view_count'].mean()
                long_avg = long_videos['view_count'].mean()
                
                if short_avg > long_avg * 1.5:
                    recommendations.append(
                        "⏱️ Shorter videos perform significantly better. Consider reducing video length."
                    )
                elif long_avg > short_avg * 1.5:
                    recommendations.append(
                        "⏱️ Longer videos perform significantly better. Consider creating more in-depth content."
                    )
            
            # Default recommendation if no specific issues
            if not recommendations:
                recommendations.append(
                    "✨ Channel performing well overall. Continue monitoring metrics for trends."
                )
            
            return recommendations
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return ["Unable to generate recommendations at this time."]
    
    @staticmethod
    def growth_opportunities(df_channel: pd.Series, df_videos: pd.DataFrame) -> List[str]:
        """
        Identify growth opportunities for the channel.
        
        Args:
            df_channel: Channel data series
            df_videos: Videos dataframe
            
        Returns:
            list: Growth opportunities
        """
        opportunities = []
        
        try:
            # Untapped audience potential
            subscribers = df_channel.get('subscribers', 0)
            total_views = df_channel.get('total_views', 0)
            
            if total_views > 0:
                views_per_subscriber = total_views / subscribers if subscribers > 0 else 0
                
                if views_per_subscriber > 40:
                    opportunities.append(
                        "📈 High view-to-subscriber ratio. Consider converting viewers to subscribers."
                    )
                elif views_per_subscriber < 20:
                    opportunities.append(
                        "👥 Low view-to-subscriber ratio. Focus on viral content to reach new audiences."
                    )
            
            # Best performing content type
            shorts = df_videos[df_videos['is_short'] == True]
            videos = df_videos[df_videos['is_short'] == False]
            
            if len(shorts) > 0 and len(videos) > 0:
                shorts_avg = shorts['view_count'].mean()
                videos_avg = videos['view_count'].mean()
                
                if shorts_avg > videos_avg * 1.5:
                    opportunities.append(
                        "🎬 Shorts significantly outperform regular videos. Increase Shorts production."
                    )
                elif videos_avg > shorts_avg * 1.5:
                    opportunities.append(
                        "📺 Regular videos outperform Shorts. Focus on long-form content."
                    )
            
            # Engagement optimization
            avg_engagement = (
                (df_videos['like_count'] + df_videos['comment_count']) /
                df_videos['view_count'].replace(0, np.nan) * 100
            ).mean()
            
            if avg_engagement > 1.5:
                opportunities.append(
                    "🤝 High engagement indicates loyal audience. Build community with live streams or Q&As."
                )
            
            # Upload frequency
            video_count = df_channel.get('video_count', 0)
            if video_count < 10:
                opportunities.append(
                    "📅 Limited content library. Increase upload frequency to build audience."
                )
            
            return opportunities if opportunities else ["Monitor channel performance for growth patterns."]
        except Exception as e:
            print(f"Error identifying growth opportunities: {e}")
            return []
