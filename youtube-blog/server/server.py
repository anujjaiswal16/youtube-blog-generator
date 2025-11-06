from fastapi import FastAPI, Request
from agents.transcript_agent import get_transcript
from agents.blog_agent import generate_blog
from agents.visual_agent import generate_diagram
from agents.exporter_agent import export_blog
import json, os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube Blog MCP Server")

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFESTS_DIR = os.path.join(BASE_DIR, "manifests")

TOOLS = {
    "TranscriptAgent.get_transcript": get_transcript,
    "BlogAgent.generate_blog": generate_blog,
    "VisualAgent.generate_diagram": generate_diagram,
    "ExporterAgent.export_blog": export_blog
}

@app.get("/tools")
def list_tools():
    manifests = []
    if not os.path.exists(MANIFESTS_DIR):
        return manifests
    for file in os.listdir(MANIFESTS_DIR):
        if file.endswith(".json") and file != "server.manifest.json":
            with open(os.path.join(MANIFESTS_DIR, file)) as f:
                manifests.append(json.load(f))
    return manifests

@app.post("/jsonrpc")
async def jsonrpc(req: Request):
    payload = await req.json()
    method = payload.get("method")
    params = payload.get("params", {})
    _id = payload.get("id", 1)
    
    client_ip = req.client.host if req.client else "unknown"
    logger.info(f"JSON-RPC request from {client_ip}: method={method}")

    if method == "list_tools":
        tools = list_tools()
        logger.info(f"Returning {len(tools)} tools")
        return {"jsonrpc": "2.0", "result": tools, "id": _id}

    if method == "call_tool":
        tool = params.get("tool")
        inputs = params.get("inputs", {})
        logger.info(f"Calling tool: {tool} with inputs: {list(inputs.keys())}")
        
        func = TOOLS.get(tool)
        if not func:
            logger.error(f"Tool not found: {tool}")
            return {"jsonrpc": "2.0", "error": {"message": "Tool not found"}, "id": _id}
        
        start_time = datetime.now()
        try:
            result = func(**inputs)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Tool {tool} completed successfully in {elapsed:.2f}s")
            return {"jsonrpc": "2.0", "result": result, "id": _id}
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Tool {tool} failed after {elapsed:.2f}s: {str(e)}", exc_info=True)
            return {"jsonrpc": "2.0", "error": {"message": str(e)}, "id": _id}
    
    logger.warning(f"Unknown method: {method}")
    return {"jsonrpc": "2.0", "error": {"message": "Unknown method"}, "id": _id}