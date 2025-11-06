from openai import OpenAI
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Custom LiteLLM proxy endpoint
client = OpenAI(
    base_url="OPEN_AI_URL" #replace OPEN_AI_URL with actula url
)

def generate_blog(clean_transcript: str, tone: str = "educational"):
    logger.info(f"Starting blog generation. Transcript length: {len(clean_transcript)} chars, Tone: {tone}")
    start_time = datetime.now()
    
    try:
        # Check if transcript is too long (might need chunking)
        transcript_length = len(clean_transcript)
        if transcript_length > 100000:  # ~100k chars
            logger.warning(f"Large transcript detected ({transcript_length} chars). This may take a while.")
        
        prompt = f"Create a detailed blog in {tone} tone from this transcript:\n{clean_transcript}"
        
        logger.info("Sending blog generation request to LLM...")
        # Note: OpenAI client timeout is set via timeout parameter (in seconds)
        # For very long transcripts, this might take several minutes
        try:
            response = client.chat.completions.create(
                model="gpt-4o", 
                messages=[{"role": "user", "content": prompt}],
                timeout=300.0  # 5 minute timeout
            )
        except Exception as e:
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                logger.error("LLM request timed out. Transcript may be too long.")
                raise Exception("Blog generation timed out. The transcript may be too long. Try a shorter video.")
            raise
        
        blog_content = response.choices[0].message.content
        blog_length = len(blog_content)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Blog generation completed in {elapsed:.2f}s. Blog length: {blog_length} characters")
        
        return {"blog_markdown": blog_content}
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"Blog generation failed after {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise