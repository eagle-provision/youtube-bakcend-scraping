# YouTube Analytics Pipeline

Complete end-to-end pipeline that fetches YouTube video data, transcribes videos using Whisper, and analyzes content using GPT.

## Features

- **YouTube Data Collection**: Fetch video metadata, statistics, and channel information via YouTube Data API v3
- **Video Transcription**: Download and transcribe videos using OpenAI Whisper
- **Content Analysis**: Analyze transcripts with GPT to extract:
  - Content category
  - Specific niche
  - Target audience
  - Narrative style
  - Tone
- **Excel Export**: All data exported to a comprehensive Excel file

## Prerequisites

1. **Python 3.8+**
2. **ffmpeg** (required for audio processing)
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/
   ```

3. **API Keys**
   - YouTube Data API v3 key
   - OpenAI API key

## Installation

1. Clone or download this repository

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your API keys:
   ```
   YOUTUBE_API_KEY=your_youtube_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Configuration

Edit `config.py` to customize:

- **Topics to search**: Modify `TOPICS` list
- **Videos per topic**: Change `VIDEOS_PER_TOPIC`
- **Whisper model**: Options: `tiny`, `base`, `small`, `medium`, `large`
- **GPT model**: Options: `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`
- **Output filename**: Change `OUTPUT_FILENAME`

## Usage

Run the complete pipeline:

```bash
python main_pipeline.py
```

The pipeline will:
1. **Phase 1**: Fetch video data from YouTube API
2. **Phase 2**: Transcribe each video with Whisper
3. **Phase 3**: Analyze transcripts with GPT
4. **Export**: Save all data to Excel

## Output

### Excel File Columns

- **Niche**: Search topic
- **Country**: Channel country
- **Default Language**: Video language
- **Specific Niches**: YouTube topic categories
- **Views, Likes, Comment Count**: Video statistics
- **Subscribers**: Channel subscribers
- **Upload Date**: Video publish date
- **Thumbnail URL**: Video thumbnail
- **Video URL**: YouTube video link
- **Video Title**: Video title
- **Transcript**: Full video transcript
- **Narrative Style**: How content is presented
- **Target Audience**: Primary audience
- **Specific Niche (Analysis)**: GPT-analyzed niche
- **Content Category**: Broad category
- **Tone**: Content tone

### Additional Files

- `transcripts/`: Individual transcript files
- `logs/pipeline.log`: Detailed processing log
- `youtube_data_intermediate.xlsx`: Checkpoint after Phase 1
- `youtube_data_progress.xlsx`: Auto-saved every 5 videos

## Pipeline Performance

- **Whisper models**: `small` is recommended (good balance of speed/accuracy)
- **Processing time**: ~2-5 minutes per video (depending on length and model)
- **GPU support**: Automatically uses Apple Silicon (MPS) or NVIDIA CUDA if available

## Troubleshooting

### SSL Certificate Error (macOS)
If you encounter SSL errors, the pipeline includes a fix in `transcription.py`.

### Out of Memory
If transcription fails with OOM errors:
- Use a smaller Whisper model (`tiny` or `base`)
- Reduce `CHUNK_DURATION` in `config.py`

### Video Download Fails
- Check video availability (private/restricted videos won't work)
- Ensure ffmpeg is properly installed

## File Structure

```
.
├── main_pipeline.py          # Main pipeline orchestrator
├── config.py                 # Configuration settings
├── youtube_api.py           # YouTube API interactions
├── data_processor.py        # Data merging and Excel export
├── audio_processing.py      # Video download and chunking
├── transcription.py         # Whisper transcription
├── content_analyzer.py      # GPT content analysis
├── utils.py                 # Utility functions
├── languages.json           # Language code mapping
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## License

MIT

## Notes

- The pipeline saves progress automatically every 5 videos
- Press Ctrl+C to safely interrupt and save partial results
- Temporary audio files are automatically cleaned up
- Individual transcripts are saved in `transcripts/` directory
