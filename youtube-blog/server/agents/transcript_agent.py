from youtube_transcript_api import YouTubeTranscriptApi
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_transcript(video_url: str):
    logger.info(f"Starting transcript extraction for: {video_url}")
    start_time = datetime.now()
    
    # Extract video ID from URL
    if "v=" in video_url:
        video_id = video_url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in video_url:
        video_id = video_url.split("youtu.be/")[-1].split("?")[0]
    else:
        video_id = video_url  # Assume it's just the video ID
    
    logger.info(f"Extracted video ID: {video_id}")
    
    try:
        # Create API instance and fetch transcript
        logger.info("Fetching transcript from YouTube...")
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id).to_raw_data()
        
        logger.info(f"Retrieved {len(transcript_data)} transcript segments")
        
        # Extract text from transcript snippets
        text = " ".join([t["text"] for t in transcript_data])
        text_length = len(text)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Transcript extraction completed in {elapsed:.2f}s. Text length: {text_length} characters")
        
        return {"clean_transcript": text}
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"Transcript extraction failed after {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise