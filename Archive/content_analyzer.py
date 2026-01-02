"""Content analysis using OpenAI GPT API for video transcripts."""

import logging
import json
from typing import Dict, Optional
from pathlib import Path
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


def analyze_content(
    transcript: str,
    country: str = "United States",
    default_language: str = "English",
    api_key: str = None,
    model: str = "gpt-4o-mini"
) -> Dict[str, str]:
    """
    Analyze video transcript to extract content metadata.
    
    Args:
        transcript: Full transcript text to analyze
        country: Country/region context for the content
        default_language: Primary language of the content
        api_key: OpenAI API key (reads from OPENAI_API_KEY env if not provided)
        model: GPT model to use (gpt-4o-mini, gpt-4o, gpt-3.5-turbo)
    
    Returns:
        Dict containing:
            - narrative_style: How the content is presented
            - target_audience: Who the content is made for
            - specific_niche: Detailed categorization of content type
            - content_category: Broad category
            - tone: Overall tone of the content
    """
    logger.info("Analyzing transcript with ChatGPT API")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key) if api_key else OpenAI()
    
    # Truncate transcript if too long (keep first 8000 chars for context)
    if len(transcript) > 8000:
        transcript_sample = transcript[:8000] + "\n\n[...transcript truncated for analysis...]"
        logger.info("Transcript truncated to 8000 characters for API call")
    else:
        transcript_sample = transcript
    
    # Create analysis prompt
    prompt = f"""Analyze the following video transcript and provide detailed content metadata.

Country/Region: {country}
Language: {default_language}

Transcript:
\"\"\"
{transcript_sample}
\"\"\"

Based on this transcript, provide the following analysis in JSON format:

1. **narrative_style**: Describe how the content is presented (e.g., "Educational lecture format", "Casual conversational storytelling", "Fast-paced commentary", "Documentary narration", "Interview/dialogue", etc.)

2. **target_audience**: Identify the primary audience (e.g., "Young adults 18-25 interested in finance", "Beginner programmers", "Gaming enthusiasts", "Professional marketers", "General audience seeking entertainment", etc.)

3. **age_bracket**: Specify the primary age range of the target audience (e.g., "13-17", "18-24", "25-34", "35-44", "45-54", "55+", "All ages", etc.)

4. **specific_niche**: Be very specific about the content niche (e.g., "First-person Valorant ranked gameplay commentary", "Personal finance - retirement account comparison", "JavaScript React tutorial for beginners", "True crime documentary analysis", "Fitness - home workout routines for beginners", etc.)

5. **content_category**: Broad category (e.g., "Gaming", "Education", "Finance", "Technology", "Entertainment", "Lifestyle", "News", etc.)

6. **tone**: Overall tone (e.g., "Informative and professional", "Casual and humorous", "Energetic and enthusiastic", "Serious and analytical", "Inspirational", etc.)

Respond ONLY with valid JSON in this exact format:
{{
    "narrative_style": "...",
    "target_audience": "...",
    "age_bracket": "...",
    "specific_niche": "...",
    "content_category": "...",
    "tone": "..."
}}"""

    try:
        # Call OpenAI API
        logger.info(f"Calling OpenAI API with model: {model}")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert content analyst specializing in video content categorization and audience analysis. Provide detailed, accurate analysis in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent analysis
            response_format={"type": "json_object"}
        )
        
        # Parse response
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        logger.info("Content analysis complete")
        logger.info(f"Category: {result.get('content_category')}")
        logger.info(f"Niche: {result.get('specific_niche')}")
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse API response as JSON: {e}")
        raise ValueError("API returned invalid JSON response")
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        raise


def analyze_transcript_file(
    transcript_file: str | Path,
    country: str = "United States",
    default_language: str = "English",
    api_key: str = None,
    output_file: Optional[str | Path] = None
) -> Dict[str, str]:
    """
    Analyze transcript from file and optionally save results.
    
    Args:
        transcript_file: Path to transcript text file
        country: Country/region context
        default_language: Primary language
        api_key: OpenAI API key
        output_file: Optional path to save analysis results as JSON
    
    Returns:
        Analysis results dictionary
    """
    transcript_file = Path(transcript_file)
    
    if not transcript_file.exists():
        raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
    
    logger.info(f"Reading transcript from {transcript_file}")
    with transcript_file.open('r', encoding='utf-8') as f:
        transcript = f.read()
    
    # Perform analysis
    analysis = analyze_content(transcript, country, default_language, api_key)
    
    # Save results if output file specified
    if output_file:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis saved to {output_file}")
    
    return analysis


def format_analysis_report(analysis: Dict[str, str]) -> str:
    """Format analysis results as human-readable report."""
    report = f"""
{'=' * 80}
CONTENT ANALYSIS REPORT
{'=' * 80}

📁 Content Category: {analysis.get('content_category', 'N/A')}

🎯 Specific Niche: {analysis.get('specific_niche', 'N/A')}

👥 Target Audience: {analysis.get('target_audience', 'N/A')}

📝 Narrative Style: {analysis.get('narrative_style', 'N/A')}

🎭 Tone: {analysis.get('tone', 'N/A')}

{'=' * 80}
"""
    return report
