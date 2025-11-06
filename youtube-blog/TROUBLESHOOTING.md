# Troubleshooting Guide

## Issues Fixed

### 1. ✅ Updated Example Video IDs
- Changed example prompts to use your actual video IDs:
  - `uMzUB89uSxU`
  - `Yq0QkCxoTHM`
  - `nVyD6THcvDQ`

### 2. ✅ Added Comprehensive Logging
All components now log detailed information:

**Log Files Created:**
- `chatbot.log` - Chatbot server logs
- `mcp_client.log` - MCP client logs
- `server.log` - MCP server logs (in `server/` directory)

**What's Logged:**
- WebSocket connections/disconnections
- Each step execution with timestamps
- Tool call durations
- LLM API calls and responses
- Errors with full stack traces
- Progress updates with elapsed time

### 3. ✅ Fixed WebSocket Connection Issues
- Fixed WebSocket URL detection (works with both localhost and remote hosts)
- Added proper connection state handling
- Better error messages for connection failures
- Added connection timeout (10 minutes)

## Monitoring Long-Running Operations

### Check Logs in Real-Time

**Terminal 1 - Watch Chatbot Logs:**
```bash
tail -f chatbot.log
```

**Terminal 2 - Watch MCP Client Logs:**
```bash
tail -f mcp_client.log
```

**Terminal 3 - Watch Server Logs:**
```bash
tail -f server/server.log
```

### What to Look For

**If Processing Takes >30 Minutes:**

1. **Check which step is taking time:**
   - Look for log entries like: `"Executing step X/Y: ToolName"`
   - Check the duration: `"Step X completed in XXX.XXs"`

2. **Common bottlenecks:**
   - **Transcript extraction**: YouTube API might be slow or rate-limited
   - **Blog generation**: Large transcripts can take 5-10 minutes
   - **LLM planning**: Should be <60 seconds

3. **Check for errors:**
   - Look for `ERROR` entries in logs
   - Check for timeout messages
   - Look for network errors

### Timeout Settings

- **LLM Planning**: 60 seconds
- **Each Tool Call**: 300 seconds (5 minutes)
- **Overall Operation**: 600 seconds (10 minutes)

## Debugging Steps

### 1. Verify Servers Are Running

**MCP Server (port 8000):**
```bash
curl http://localhost:8000/tools
```
Should return JSON with tool manifests.

**Chatbot Server (port 8080):**
```bash
curl http://localhost:8080/
```
Should return HTML.

### 2. Test WebSocket Connection

Open browser console (F12) and check for:
- `WebSocket connected successfully` message
- Any WebSocket errors

### 3. Check if LLM Proxy is Accessible

The LiteLLM proxy might be slow or unavailable. Check:
- Network connectivity to: `https://litellm-proxy-service-1059491012611.us-central1.run.app`
- Check logs for LLM API timeouts

### 4. Test Individual Components

**Test Transcript Extraction:**
```python
from server.agents.transcript_agent import get_transcript
result = get_transcript("https://youtube.com/watch?v=uMzUB89uSxU")
print(f"Transcript length: {len(result['clean_transcript'])}")
```

**Test Blog Generation:**
```python
from server.agents.blog_agent import generate_blog
result = generate_blog("Test transcript text", "educational")
print(f"Blog length: {len(result['blog_markdown'])}")
```

## Performance Optimization

### If Blog Generation is Slow:

1. **Large Transcripts**: Transcripts >100k characters will take longer
   - Consider summarizing first
   - Or chunk the transcript

2. **LLM Proxy Issues**: Check if the LiteLLM proxy is responding
   - Look for timeout errors in logs
   - Try a shorter transcript to test

### If Transcript Extraction is Slow:

1. **YouTube API Rate Limits**: YouTube might be rate-limiting
   - Wait a few minutes and retry
   - Check if video has transcripts available

2. **Network Issues**: Check internet connection
   - Look for network errors in logs

## Common Error Messages

### "Connection Error: Could not connect to server"
- **Cause**: WebSocket connection failed
- **Fix**: 
  - Ensure chatbot server is running on port 8080
  - Check firewall settings
  - Try refreshing the page

### "Tool call error for X: timeout"
- **Cause**: Tool took longer than 5 minutes
- **Fix**: 
  - Check logs to see which tool timed out
  - Try with a shorter video
  - Check if LLM proxy is accessible

### "Failed to create execution plan"
- **Cause**: LLM planning failed
- **Fix**: 
  - Check LLM proxy connectivity
  - Check `mcp_client.log` for details
  - Verify OpenAI API key is valid

## Getting Help

When reporting issues, include:
1. Relevant log entries from all three log files
2. Which video ID you're trying to process
3. How long the operation has been running
4. Any error messages from the browser console

