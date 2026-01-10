"""
Analysis orchestration module for YouTube analytics.
Coordinates the complete analysis pipeline.
"""

import pandas as pd
import json
from typing import Dict, Tuple
from data_processor import load_from_excel
from metrics import ChannelMetrics, VideoMetrics, ContentTypeAnalysis, duration_to_seconds
from insights import InsightGenerator


class AnalysisEngine:
    """Main analysis engine that orchestrates all analysis components."""
    
    def __init__(self, excel_file: str = 'youtube_analytics_scraped.xlsx', video_type: str = 'all'):
        """
        Initialize analysis engine with data.
        
        Args:
            excel_file: Path to Excel file with scraped data
            video_type: Filter videos - 'all', 'shorts', or 'long'
        """
        self.excel_file = excel_file
        self.video_type = video_type
        self.df_channel = None
        self.df_videos = None
        self.analysis_results = {}
    
    def load_data(self) -> bool:
        """
        Load data from Excel file and filter by video type.
        
        Returns:
            bool: Success status
        """
        try:
            self.df_channel, self.df_videos = load_from_excel(self.excel_file)
            if self.df_channel is None or self.df_videos is None:
                print("✗ Failed to load data")
                return False
            
            # Filter by video type if specified
            if self.video_type == 'shorts':
                self.df_videos = self.df_videos[self.df_videos['is_short'] == True]
                print(f"✓ Loaded {len(self.df_channel)} channel(s) and {len(self.df_videos)} SHORT video(s)")
            elif self.video_type == 'long':
                self.df_videos = self.df_videos[self.df_videos['is_short'] == False]
                print(f"✓ Loaded {len(self.df_channel)} channel(s) and {len(self.df_videos)} LONG video(s)")
            else:
                print(f"✓ Loaded {len(self.df_channel)} channel(s) and {len(self.df_videos)} video(s) (all types)")
            
            return True
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            return False
    
    def analyze_channel(self) -> Dict:
        """
        Perform channel-level analysis.
        
        Returns:
            dict: Channel analysis results
        """
        try:
            channel_data = self.df_channel.iloc[0]
            
            analysis = {
                'channel_name': channel_data.get('channel_title', 'Unknown'),
                'subscribers': f"{int(channel_data.get('subscribers', 0)):,}",
                'total_views': f"{int(channel_data.get('total_views', 0)):,}",
                'video_count': int(channel_data.get('video_count', 0)),
                'shorts_count': int(channel_data.get('shorts_count', 0))
            }
            
            # Calculate engagement metrics
            engagement_metrics = ChannelMetrics.calculate_engagement_metrics(channel_data)
            analysis['engagement_metrics'] = engagement_metrics
            
            # Calculate content metrics
            content_metrics = ChannelMetrics.calculate_content_metrics(channel_data)
            analysis['content_metrics'] = content_metrics
            
            self.analysis_results['channel_analysis'] = analysis
            
            print("\n✓ Channel analysis complete")
            return analysis
        except Exception as e:
            print(f"✗ Error in channel analysis: {e}")
            return {}
    
    def analyze_videos(self) -> Dict:
        """
        Perform video-level analysis.
        
        Returns:
            dict: Video analysis results
        """
        try:
            # Add calculated metrics to dataframe
            self.df_videos['engagement_rate'] = VideoMetrics.calculate_engagement_rate(self.df_videos)
            self.df_videos['like_ratio'] = VideoMetrics.calculate_like_ratio(self.df_videos)
            self.df_videos['comment_ratio'] = VideoMetrics.calculate_comment_ratio(self.df_videos)
            self.df_videos['engagement_per_minute'] = VideoMetrics.calculate_per_minute_engagement(self.df_videos)
            self.df_videos['performance_category'] = VideoMetrics.categorize_video_performance(self.df_videos)
            
            # Convert duration to seconds for calculations
            duration_seconds = self.df_videos['duration'].apply(duration_to_seconds)
            
            analysis = {
                'total_videos': len(self.df_videos),
                'avg_views': f"{self.df_videos['view_count'].mean():,.0f}",
                'avg_likes': f"{self.df_videos['like_count'].mean():,.0f}",
                'avg_comments': f"{self.df_videos['comment_count'].mean():,.0f}",
                'avg_engagement_rate': f"{self.df_videos['engagement_rate'].mean():.4f}%",
                'avg_like_ratio': f"{self.df_videos['like_ratio'].mean():.2f}%",
                'avg_comment_ratio': f"{self.df_videos['comment_ratio'].mean():.2f}%",
                'median_duration_seconds': int(duration_seconds.median()),
                'high_performers': len(self.df_videos[self.df_videos['performance_category'] == 'High']),
                'medium_performers': len(self.df_videos[self.df_videos['performance_category'] == 'Medium']),
                'low_performers': len(self.df_videos[self.df_videos['performance_category'] == 'Low'])
            }
            
            self.analysis_results['video_analysis'] = analysis
            
            print("✓ Video analysis complete")
            return analysis
        except Exception as e:
            print(f"✗ Error in video analysis: {e}")
            return {}
    
    def analyze_content_types(self) -> Dict:
        """
        Perform content type comparison analysis.
        
        Returns:
            dict: Content type analysis results
        """
        try:
            # Shorts vs Videos comparison
            shorts_vs_videos = ContentTypeAnalysis.compare_shorts_vs_videos(self.df_videos)
            
            # Optimal video length analysis
            video_length_analysis = ContentTypeAnalysis.optimal_video_length(self.df_videos)
            
            analysis = {
                'shorts_vs_videos': shorts_vs_videos,
                'video_length_analysis': video_length_analysis
            }
            
            self.analysis_results['content_type_analysis'] = analysis
            
            print("✓ Content type analysis complete")
            return analysis
        except Exception as e:
            print(f"✗ Error in content type analysis: {e}")
            return {}
    
    def generate_insights(self) -> Dict:
        """
        Generate actionable insights from analysis.
        
        Returns:
            dict: Insights and recommendations
        """
        try:
            channel_data = self.df_channel.iloc[0]
            
            insights_dict = {
                'channel_health': InsightGenerator.analyze_channel_health(channel_data, self.df_videos),
                'top_performers': InsightGenerator.identify_top_performers(self.df_videos, n=5),
                'underperformers': InsightGenerator.identify_underperformers(self.df_videos, n=5),
                'content_recommendations': InsightGenerator.content_recommendations(self.df_videos),
                'growth_opportunities': InsightGenerator.growth_opportunities(channel_data, self.df_videos)
            }
            
            self.analysis_results['insights'] = insights_dict
            
            print("✓ Insights generation complete")
            return insights_dict
        except Exception as e:
            print(f"✗ Error generating insights: {e}")
            return {}
    
    def run_complete_analysis(self) -> bool:
        """
        Run complete analysis pipeline.
        
        Returns:
            bool: Success status
        """
        print("\n" + "="*60)
        print("YouTube Analytics - First Analysis Stage")
        print("="*60)
        
        # Load data
        print("\n[1/4] Loading Data...")
        print("-"*60)
        if not self.load_data():
            return False
        
        # Analyze channel
        print("\n[2/4] Analyzing Channel...")
        print("-"*60)
        self.analyze_channel()
        
        # Analyze videos
        print("\n[3/4] Analyzing Videos...")
        print("-"*60)
        self.analyze_videos()
        
        # Analyze content types
        print("\n[4/4] Analyzing Content Types...")
        print("-"*60)
        self.analyze_content_types()
        
        # Generate insights
        print("\n[BONUS] Generating Insights...")
        print("-"*60)
        self.generate_insights()
        
        print("\n" + "="*60)
        print("✓ Analysis Complete")
        print("="*60 + "\n")
        
        return True
    
    def print_summary(self):
        """Print analysis summary to console."""
        
        if not self.analysis_results:
            print("✗ No analysis results. Run analysis first.")
            return
        
        # Channel Summary
        print("\n" + "="*60)
        print("CHANNEL SUMMARY")
        print("="*60)
        channel = self.analysis_results.get('channel_analysis', {})
        print(f"Channel: {channel.get('channel_name', 'Unknown')}")
        print(f"Subscribers: {channel.get('subscribers', 'N/A')}")
        print(f"Total Views: {channel.get('total_views', 'N/A')}")
        print(f"Videos: {channel.get('video_count', 'N/A')} | Shorts: {channel.get('shorts_count', 'N/A')}")
        
        if channel.get('engagement_metrics'):
            print(f"\nViews per Subscriber: {channel['engagement_metrics'].get('views_per_subscriber', 'N/A')}")
            print(f"Avg Views per Video: {channel['engagement_metrics'].get('avg_views_per_video', 'N/A')}")
        
        # Video Summary
        print("\n" + "="*60)
        print("VIDEO SUMMARY")
        print("="*60)
        videos = self.analysis_results.get('video_analysis', {})
        print(f"Total Videos: {videos.get('total_videos', 'N/A')}")
        print(f"Avg Views: {videos.get('avg_views', 'N/A')}")
        print(f"Avg Likes: {videos.get('avg_likes', 'N/A')}")
        print(f"Avg Comments: {videos.get('avg_comments', 'N/A')}")
        print(f"Avg Engagement Rate: {videos.get('avg_engagement_rate', 'N/A')}")
        print(f"Avg Video Duration: {videos.get('median_duration_seconds', 'N/A')}s")
        
        # Performance Distribution
        print(f"\nPerformance Distribution:")
        print(f"  High: {videos.get('high_performers', 0)} videos")
        print(f"  Medium: {videos.get('medium_performers', 0)} videos")
        print(f"  Low: {videos.get('low_performers', 0)} videos")
        
        # Insights
        print("\n" + "="*60)
        print("CHANNEL HEALTH")
        print("="*60)
        insights = self.analysis_results.get('insights', {})
        health = insights.get('channel_health', {})
        print(f"Overall Health Score: {health.get('overall_health_score', 'N/A')}")
        print(f"Engagement Health: {health.get('engagement_health', 'N/A')}")
        print(f"Content Consistency: {health.get('content_consistency', 'N/A')}")
        
        # Top Performers
        print("\n" + "="*60)
        print("TOP 5 VIDEOS")
        print("="*60)
        top_videos = insights.get('top_performers', [])
        for video in top_videos:
            print(f"\n#{video['rank']} - {video['title']}")
            print(f"  Views: {video['views']} | Likes: {video['likes']} | Comments: {video['comments']}")
        
        # Recommendations
        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        recommendations = insights.get('content_recommendations', [])
        for rec in recommendations:
            print(f"• {rec}")
        
        # Growth Opportunities
        print("\n" + "="*60)
        print("GROWTH OPPORTUNITIES")
        print("="*60)
        opportunities = insights.get('growth_opportunities', [])
        for opp in opportunities:
            print(f"• {opp}")
        
        print("\n" + "="*60 + "\n")
    
    def export_analysis_json(self, filename: str = 'analysis_results.json'):
        """
        Export analysis results to JSON file.
        
        Args:
            filename: Output JSON filename
        """
        try:
            # Convert numpy/pandas types to native Python types
            def convert_to_serializable(obj):
                if isinstance(obj, (pd.DataFrame, pd.Series)):
                    return obj.to_dict()
                elif isinstance(obj, (pd.Int64Dtype, pd.Float64Dtype)):
                    return float(obj) if pd.notna(obj) else None
                elif hasattr(obj, 'item'):  # numpy types
                    return obj.item()
                return obj
            
            # Recursively convert the results
            serializable_results = json.loads(
                json.dumps(self.analysis_results, default=convert_to_serializable)
            )
            
            with open(filename, 'w') as f:
                json.dump(serializable_results, f, indent=2)
            print(f"✓ Analysis exported to {filename}")
        except Exception as e:
            print(f"✗ Error exporting analysis: {e}")
    
    def export_metrics_csv(self, filename: str = 'videos_with_metrics.csv'):
        """
        Export videos with calculated metrics to CSV.
        
        Args:
            filename: Output CSV filename
        """
        try:
            if self.df_videos is not None:
                # Select relevant columns
                export_cols = [
                    'title', 'view_count', 'like_count', 'comment_count',
                    'engagement_rate', 'like_ratio', 'comment_ratio',
                    'engagement_per_minute', 'performance_category', 'duration'
                ]
                
                available_cols = [col for col in export_cols if col in self.df_videos.columns]
                self.df_videos[available_cols].to_csv(filename, index=False)
                print(f"✓ Metrics exported to {filename}")
            else:
                print("✗ No video data available")
        except Exception as e:
            print(f"✗ Error exporting metrics: {e}")


def main(video_type: str = 'all'):
    """
    Main entry point for analysis.
    
    Args:
        video_type: Filter by video type - 'all', 'shorts', or 'long'
    """
    
    # Initialize and run analysis
    engine = AnalysisEngine(video_type=video_type)
    
    if engine.run_complete_analysis():
        # Print summary
        engine.print_summary()
        
        # Export results
        engine.export_analysis_json('analysis_results.json')
        engine.export_metrics_csv('videos_with_metrics.csv')
    else:
        print("✗ Analysis failed")


if __name__ == "__main__":
    main()
