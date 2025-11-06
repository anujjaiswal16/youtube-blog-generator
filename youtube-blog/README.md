# YouTube Blog MCP System

## 🧠 Overview
This project demonstrates an **Agentic AI workflow** that converts YouTube videos into structured blogs using an **MCP (Model Context Protocol)** architecture.

The system includes:
- Transcript extraction (via YouTube API)
- Blog generation (via OpenAI GPT)
- Diagram generation (stub for future use)
- Export to DOCX and PDF formats
- An MCP client for orchestration and planning

---

## ⚙️ Setup Instructions

### 1. Clone or Unzip the Project
```bash
unzip youtube-blog-mcp.zip
cd youtube-blog-mcp
In mcp_client.py and in agents/blog_agent.py add the OpenAI url.
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the MCP Server
```bash
cd server
uvicorn server:app --port 8000 --reload
```

The server exposes MCP-compatible endpoints at:
```
http://localhost:8000/jsonrpc
```

### 4. Run the MCP Client (Command Line)
```bash
cd ../client
python mcp_client.py
```

This triggers an AI-planned workflow that will:
1. Fetch a YouTube transcript  
2. Generate a blog from the transcript  
3. (Optionally) generate diagrams  
4. Export the final blog to both DOCX and PDF  

### 5. Run the Chatbot Interface (Web UI) 🎨

**Start the chatbot server:**
```bash
# From the project root directory
python chatbot.py
```

**Or with uvicorn:**
```bash
uvicorn chatbot:app --port 8080 --reload
```

**Access the chatbot:**
Open your browser and navigate to:
```
http://localhost:8080
```

The chatbot provides:
- 🤖 **Interactive Web Interface** - Beautiful, modern UI for interacting with the system
- 💬 **Natural Language Input** - Just paste YouTube URLs or describe what you want
- 📊 **Real-time Progress Updates** - See each step as it executes
- 📥 **Download Links** - Get your generated DOCX and PDF files directly
- 🎯 **Smart Planning** - Enhanced prompt engineering for better LLM planning

**Example prompts you can try:**
- "Generate a blog from https://youtube.com/watch?v=VIDEO_ID"
- "Create a professional blog post with diagrams from this video: https://youtu.be/VIDEO_ID"
- "Convert this YouTube video to a blog: VIDEO_ID"
- "Make an educational blog post from [YouTube URL]"

---

## 📂 Project Structure

```
youtube-blog-mcp/
├── server/
│   ├── server.py                  # MCP Server and JSON-RPC API
│   ├── agents/                    # AI/Tool Agents
│   │   ├── transcript_agent.py
│   │   ├── blog_agent.py
│   │   ├── visual_agent.py
│   │   └── exporter_agent.py
│   └── manifests/                 # MCP Manifests (to integrate with other MCP clients)
├── client/
│   └── mcp_client.py              # MCP Client that orchestrates workflow
├── chatbot.py                     # Web-based chatbot interface
└── requirements.txt
```

---

## 🧩 Extending the System

You can easily extend the system by adding new agents:
- **SummarizerAgent** — summarize blogs or transcripts.
- **SEOAgent** — optimize blog for search engines.
- **PublisherAgent** — auto-publish to WordPress or Medium.

Each new agent requires a corresponding manifest JSON file in `server/manifests/`.

---

## 🧠 LLM Integration & Prompt Engineering

The system uses **GPT-4o** via a LiteLLM proxy for:
- **Workflow Planning**: Enhanced prompt engineering ensures the LLM creates optimal execution plans
- **Blog Generation**: High-quality blog posts from transcripts
- **Smart Tool Selection**: Automatically selects the right tools based on user requests

**Key Prompt Engineering Features:**
- ✅ Structured tool descriptions with parameter details
- ✅ Step-by-step workflow instructions
- ✅ Context-aware planning (extracts YouTube URLs/IDs automatically)
- ✅ Chain-of-thought reasoning for tool selection
- ✅ Lower temperature (0.3) for consistent planning

You can customize prompts in `client/mcp_client.py` (planning) and `server/agents/blog_agent.py` (blog generation).

---

## 🧭 Example Goal

```
Goal: "Generate a blog post from a YouTube video: https://youtube.com/watch?v=dQw4w9WgXcQ"
```

The MCP client will automatically plan the tool usage:
1. TranscriptAgent.get_transcript
2. BlogAgent.generate_blog
3. ExporterAgent.export_blog

---

## 🪄 Author
**Anuj Kumar Jaiswal**  
Senior Customer Architect | Elastic | GenAI Enthusiast
