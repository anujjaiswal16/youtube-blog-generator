from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import sys
import os
import asyncio
import json
import logging
from pathlib import Path
from threading import Thread
from queue import Queue
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path to import MCP client
sys.path.append(str(Path(__file__).parent))
from client.mcp_client import MCPClient

app = FastAPI(title="YouTube Blog Chatbot")

# Initialize MCP client
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
mcp_client = MCPClient(MCP_SERVER_URL)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the chatbot interface"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Blog Generator - AI Chatbot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .chat-container {
            width: 100%;
            max-width: 900px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .chat-header h1 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .chat-header .icon {
            font-size: 28px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            background: #f8f9fa;
        }
        
        .message {
            display: flex;
            gap: 12px;
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 18px;
            border-radius: 18px;
            word-wrap: break-word;
            line-height: 1.5;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
        }
        
        .message.assistant .message-content.progress {
            background: #fff3cd;
            border-color: #ffc107;
            color: #856404;
            font-style: italic;
        }
        
        .message.assistant .message-content.error {
            background: #f8d7da;
            border-color: #dc3545;
            color: #721c24;
        }
        
        .message.assistant .message-content.success {
            background: #d4edda;
            border-color: #28a745;
            color: #155724;
        }
        
        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }
        
        .message.user .avatar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .message.assistant .avatar {
            background: #e0e0e0;
            color: #666;
        }
        
        .chat-input-container {
            padding: 20px 30px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        
        .chat-input-form {
            display: flex;
            gap: 10px;
        }
        
        .chat-input {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .chat-input:focus {
            border-color: #667eea;
        }
        
        .send-button {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .send-button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .result-links {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e0e0e0;
        }
        
        .result-links a {
            display: inline-block;
            margin: 5px 10px 5px 0;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 20px;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .result-links a:hover {
            background: #764ba2;
        }
        
        .loading {
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 2px solid #667eea;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .example-prompts {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .example-prompts h3 {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }
        
        .example-btn {
            display: inline-block;
            margin: 5px 5px 5px 0;
            padding: 6px 12px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 15px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .example-btn:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="icon">🎬</div>
            <h1>YouTube Blog Generator</h1>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message assistant">
                <div class="avatar">🤖</div>
                <div class="message-content">
                    <strong>Welcome to YouTube Blog Generator!</strong><br><br>
                    I can help you convert YouTube videos into professional blog posts. Just paste a YouTube video URL or ID, and I'll:
                    <ul style="margin-top: 10px; padding-left: 20px;">
                        <li>Extract the transcript</li>
                        <li>Generate a well-formatted blog post</li>
                        <li>Create diagrams if needed</li>
                        <li>Export to DOCX and PDF formats</li>
                    </ul>
                    <div class="example-prompts">
                        <h3>Try these examples:</h3>
                        <button class="example-btn" onclick="setExample('Generate a blog from https://youtube.com/watch?v=uMzUB89uSxU')">Example 1</button>
                        <button class="example-btn" onclick="setExample('Create a professional blog post with diagrams from this video: https://youtu.be/Yq0QkCxoTHM')">Example 2</button>
                        <button class="example-btn" onclick="setExample('Convert this YouTube video to a blog: nVyD6THcvDQ')">Example 3</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="chat-input-container">
            <form class="chat-input-form" id="chatForm" onsubmit="sendMessage(event)">
                <input 
                    type="text" 
                    class="chat-input" 
                    id="messageInput" 
                    placeholder="Paste YouTube URL or describe what you want..."
                    autocomplete="off"
                />
                <button type="submit" class="send-button" id="sendButton">Send</button>
            </form>
        </div>
    </div>
    
    <script>
        // Determine WebSocket URL - handle both localhost and remote hosts
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = window.location.host;
        const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws`);
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const chatForm = document.getElementById('chatForm');
        
        function setExample(text) {
            messageInput.value = text;
            messageInput.focus();
        }
        
        function addMessage(content, type, className = '') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'avatar';
            avatar.textContent = type === 'user' ? '👤' : '🤖';
            
            const messageContent = document.createElement('div');
            messageContent.className = `message-content ${className}`;
            messageContent.innerHTML = content;
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            return messageContent;
        }
        
        function sendMessage(event) {
            event.preventDefault();
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Add user message
            addMessage(message, 'user');
            messageInput.value = '';
            sendButton.disabled = true;
            
            // Add loading message
            const progressMsg = addMessage('<span class="loading"></span> Processing your request...', 'assistant', 'progress');
            
            // Send to server
            ws.send(JSON.stringify({ type: 'message', content: message }));
        }
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'progress') {
                // Update progress message
                const progressMessages = chatMessages.querySelectorAll('.message-content.progress');
                if (progressMessages.length > 0) {
                    const lastProgress = progressMessages[progressMessages.length - 1];
                    lastProgress.innerHTML = `<span class="loading"></span> ${data.message}`;
                } else {
                    addMessage(`<span class="loading"></span> ${data.message}`, 'assistant', 'progress');
                }
            } else if (data.type === 'result') {
                // Remove progress messages
                const progressMessages = chatMessages.querySelectorAll('.message-content.progress');
                progressMessages.forEach(msg => msg.parentElement.remove());
                
                let resultHtml = '<strong>✅ Task completed successfully!</strong><br><br>';
                
                if (data.result.final_result) {
                    const finalResult = data.result.final_result;
                    
                    if (finalResult.blog_markdown) {
                        resultHtml += '<strong>Blog Generated:</strong><br>';
                        const preview = finalResult.blog_markdown.substring(0, 500) + '...';
                        resultHtml += `<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto;">${escapeHtml(preview)}</pre><br>`;
                    }
                    
                    if (finalResult.docx_url || finalResult.pdf_url) {
                        resultHtml += '<div class="result-links">';
                        resultHtml += '<strong>Download:</strong><br>';
                        if (finalResult.docx_url) {
                            resultHtml += `<a href="/download/${encodeURIComponent(finalResult.docx_url)}" target="_blank">📄 DOCX</a>`;
                        }
                        if (finalResult.pdf_url) {
                            resultHtml += `<a href="/download/${encodeURIComponent(finalResult.pdf_url)}" target="_blank">📑 PDF</a>`;
                        }
                        resultHtml += '</div>';
                    }
                    
                    if (data.result.execution_log) {
                        resultHtml += '<br><strong>Execution Steps:</strong><ul>';
                        data.result.execution_log.forEach(log => {
                            const status = log.status === 'success' ? '✓' : '✗';
                            resultHtml += `<li>${status} ${log.description || log.tool}</li>`;
                        });
                        resultHtml += '</ul>';
                    }
                }
                
                addMessage(resultHtml, 'assistant', 'success');
                sendButton.disabled = false;
            } else if (data.type === 'error') {
                // Remove progress messages
                const progressMessages = chatMessages.querySelectorAll('.message-content.progress');
                progressMessages.forEach(msg => msg.parentElement.remove());
                
                addMessage(`<strong>❌ Error:</strong> ${escapeHtml(data.message)}`, 'assistant', 'error');
                sendButton.disabled = false;
            }
            
            chatMessages.scrollTop = chatMessages.scrollHeight;
        };
        
        ws.onopen = function() {
            console.log('WebSocket connected successfully');
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
            addMessage('<strong>Connection Error:</strong> Could not connect to server. Make sure the chatbot server is running on port 8080.', 'assistant', 'error');
            sendButton.disabled = false;
        };
        
        ws.onclose = function(event) {
            console.log('WebSocket closed:', event.code, event.reason);
            if (event.code !== 1000) {
                addMessage('<strong>Connection Closed:</strong> WebSocket connection was closed. Please refresh the page.', 'assistant', 'error');
            }
        };
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Auto-focus input
        messageInput.focus();
    </script>
</body>
</html>
    """
    return html_content

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    logger.info(f"WebSocket connection attempt from {client_id}")
    
    try:
        await websocket.accept()
        logger.info(f"WebSocket connection accepted from {client_id}")
    except Exception as e:
        logger.error(f"Failed to accept WebSocket connection: {e}")
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            logger.info(f"Received message from {client_id}: {message_data.get('type', 'unknown')}")
            
            if message_data.get("type") == "message":
                user_message = message_data.get("content", "")
                logger.info(f"Processing user message: {user_message[:100]}...")
                start_time = datetime.now()
                
                # Queue for progress updates from the thread
                progress_queue = Queue()
                
                # Progress callback function that queues messages
                def progress_callback(status):
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"[{elapsed:.1f}s] Progress: {status}")
                    progress_queue.put(status)
                
                # Worker thread to execute the plan
                def execute_plan():
                    try:
                        logger.info("Starting plan execution in worker thread")
                        result = mcp_client.plan_and_execute(user_message, progress_callback)
                        elapsed = (datetime.now() - start_time).total_seconds()
                        logger.info(f"Plan execution completed in {elapsed:.1f} seconds")
                        progress_queue.put(("result", result))
                    except Exception as e:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        logger.error(f"Plan execution failed after {elapsed:.1f} seconds: {str(e)}", exc_info=True)
                        progress_queue.put(("error", str(e)))
                
                # Start execution in a thread
                thread = Thread(target=execute_plan, daemon=True)
                thread.start()
                logger.info("Execution thread started")
                
                # Monitor progress queue and send updates with timeout
                timeout_seconds = 600  # 10 minutes timeout
                start_monitor = datetime.now()
                
                try:
                    while thread.is_alive() or not progress_queue.empty():
                        elapsed = (datetime.now() - start_monitor).total_seconds()
                        
                        # Check for timeout
                        if elapsed > timeout_seconds:
                            logger.error(f"Execution timeout after {timeout_seconds} seconds")
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Operation timed out after {timeout_seconds} seconds. Please try with a shorter video or check server logs."
                            })
                            break
                        
                        try:
                            item = progress_queue.get(timeout=0.5)
                            if isinstance(item, tuple) and item[0] == "result":
                                logger.info("Sending result to client")
                                await websocket.send_json({
                                    "type": "result",
                                    "result": item[1]
                                })
                                break
                            elif isinstance(item, tuple) and item[0] == "error":
                                logger.error(f"Sending error to client: {item[1]}")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": item[1]
                                })
                                break
                            else:
                                # Progress update
                                await websocket.send_json({
                                    "type": "progress",
                                    "message": item
                                })
                        except:
                            await asyncio.sleep(0.1)
                    
                    # Wait for thread to finish if still alive
                    if thread.is_alive():
                        logger.warning("Thread still alive after queue monitoring, waiting...")
                        thread.join(timeout=5)
                except Exception as e:
                    logger.error(f"Error in progress monitoring: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Internal error: {str(e)}"
                    })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    from fastapi.responses import FileResponse
    from fastapi import HTTPException
    import os
    
    # Security: Only allow files in the server directory
    # Normalize the path to prevent directory traversal
    file_path = file_path.lstrip('/')
    if '..' in file_path or file_path.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    full_path = os.path.join(os.path.dirname(__file__), "server", file_path)
    
    # Additional security: ensure the resolved path is within server directory
    server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "server"))
    full_path = os.path.abspath(full_path)
    
    if not full_path.startswith(server_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if os.path.exists(full_path) and os.path.isfile(full_path):
        # Determine content type
        if file_path.endswith('.pdf'):
            media_type = 'application/pdf'
        elif file_path.endswith('.docx'):
            media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            media_type = 'application/octet-stream'
        
        return FileResponse(
            full_path,
            media_type=media_type,
            filename=os.path.basename(file_path)
        )
    else:
        raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

