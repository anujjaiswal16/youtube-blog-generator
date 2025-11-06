import json, requests
import logging
from openai import OpenAI
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Custom LiteLLM proxy endpoint
openai_client = OpenAI(
    base_url="OPENAI_URL" #replace OPENAI_URL with actual url
)

class MCPClient:
    def __init__(self, server_url):
        self.server_url = server_url
    
    def list_tools(self):
        logger.info(f"Fetching tools from MCP server: {self.server_url}")
        start_time = datetime.now()
        payload = {"jsonrpc": "2.0", "id": 1, "method": "list_tools"}
        try:
            response = requests.post(f"{self.server_url}/jsonrpc", json=payload, timeout=10)
            response.raise_for_status()
            json_response = response.json()
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if "error" in json_response:
                logger.error(f"Server error: {json_response['error']}")
                raise Exception(f"Server error: {json_response['error']}")
            
            tools = json_response["result"]
            logger.info(f"Retrieved {len(tools)} tools in {elapsed:.2f}s")
            return tools
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling MCP server: {e}")
            raise
        except Exception as e:
            logger.error(f"Error listing tools: {e}", exc_info=True)
            raise
    
    def call_tool(self, tool, inputs):
        logger.info(f"Calling tool: {tool} with inputs: {list(inputs.keys())}")
        start_time = datetime.now()
        payload = {"jsonrpc": "2.0", "id": 1, "method": "call_tool", "params": {"tool": tool, "inputs": inputs}}
        try:
            response = requests.post(f"{self.server_url}/jsonrpc", json=payload, timeout=300)  # 5 min timeout per tool
            response.raise_for_status()
            json_response = response.json()
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if "error" in json_response:
                error_msg = json_response.get("error", {}).get("message", "Unknown error")
                logger.error(f"Tool {tool} failed after {elapsed:.2f}s: {error_msg}")
                raise Exception(f"Tool call error for {tool}: {error_msg}")
            
            logger.info(f"Tool {tool} completed in {elapsed:.2f}s")
            return json_response["result"]
        except requests.exceptions.Timeout:
            logger.error(f"Tool {tool} timed out after 300 seconds")
            raise Exception(f"Tool {tool} timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling tool {tool}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling tool {tool}: {e}", exc_info=True)
            raise
    
    def plan_and_execute(self, goal, progress_callback=None):
        """
        Plan and execute a goal using available MCP tools.
        
        Args:
            goal: The user's goal/request
            progress_callback: Optional callback function(status_message) for progress updates
        """
        tools = self.list_tools()
        
        # Enhanced prompt engineering for better planning
        tools_description = ""
        for tool in tools:
            tool_name = tool.get("name", "Unknown")
            tool_desc = tool.get("description", "")
            input_schema = tool.get("inputSchema", {})
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            params_desc = []
            for param, details in properties.items():
                param_type = details.get("type", "string")
                param_desc = details.get("description", "")
                is_required = param in required
                req_text = " (REQUIRED)" if is_required else " (optional)"
                params_desc.append(f"  - {param} ({param_type}){req_text}: {param_desc}")
            
            tools_description += f"\n{tool_name}:\n  Description: {tool_desc}\n  Parameters:\n" + "\n".join(params_desc) + "\n"
        
        plan_prompt = f"""You are an expert AI workflow planner specialized in YouTube-to-blog conversion workflows. Your task is to create an optimal execution plan.

USER GOAL: {goal}

AVAILABLE TOOLS:{tools_description}

PLANNING INSTRUCTIONS:
1. Analyze the user's goal carefully. Extract any YouTube video URLs or video IDs mentioned.
2. Create a logical sequence of tool calls that will accomplish the goal.
3. For YouTube-to-blog workflows, ALWAYS follow this sequence:
   - Step 1: Use TranscriptAgent.get_transcript with the video_url parameter
   - Step 2: Use BlogAgent.generate_blog with clean_transcript from Step 1
   - Step 3 (optional): Use VisualAgent.generate_diagram if diagrams are needed
   - Step 4: Use ExporterAgent.export_blog with blog_markdown from Step 2

4. Use $prev.output_key syntax to chain outputs between steps:
   - TranscriptAgent outputs: clean_transcript
   - BlogAgent outputs: blog_markdown
   - VisualAgent outputs: diagram_url
   - ExporterAgent outputs: docx_url, pdf_url

5. Extract video URLs/IDs from the goal text. Support formats:
   - https://youtube.com/watch?v=VIDEO_ID
   - https://youtu.be/VIDEO_ID
   - https://www.youtube.com/watch?v=VIDEO_ID
   - Just the VIDEO_ID if mentioned

6. If the user asks for a "blog", "article", or "document", include the export step.
7. If the user mentions "diagrams", "flowcharts", or "architecture", include VisualAgent.
8. Choose appropriate tone for BlogAgent (educational, casual, professional) based on context.

RESPONSE FORMAT (JSON only, no markdown):
{{
  "plan": [
    {{
      "tool": "ToolName.method",
      "inputs": {{
        "param1": "value1",
        "param2": "$prev.output_key"
      }},
      "description": "Brief explanation of what this step does"
    }}
  ]
}}

CRITICAL: Return ONLY valid JSON. No markdown code blocks, no explanations outside the JSON."""
        
        if progress_callback:
            progress_callback("🤖 Analyzing your request and creating an execution plan...")
        
        logger.info("Sending planning request to LLM")
        plan_start = datetime.now()
        try:
            plan_response = openai_client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": "You are an expert workflow planner. Always respond with valid JSON only, no markdown or explanations."},
                    {"role": "user", "content": plan_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent planning
                timeout=60.0  # 60 second timeout for planning
            )
            plan_elapsed = (datetime.now() - plan_start).total_seconds()
            logger.info(f"LLM planning completed in {plan_elapsed:.2f}s")
            plan_content = plan_response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM planning failed: {e}", exc_info=True)
            raise Exception(f"Failed to create execution plan: {str(e)}")
        
        # Try to extract JSON from the response (in case it's wrapped in markdown code blocks)
        if "```json" in plan_content:
            plan_content = plan_content.split("```json")[1].split("```")[0].strip()
        elif "```" in plan_content:
            plan_content = plan_content.split("```")[1].split("```")[0].strip()
        
        # Clean up any leading/trailing whitespace or newlines
        plan_content = plan_content.strip()
        
        try:
            plan = json.loads(plan_content)
        except json.JSONDecodeError as e:
            # Try to find JSON object in the response
            import re
            json_match = re.search(r'\{[^{}]*"plan"[^{}]*\[[^\]]*\][^{}]*\}', plan_content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
            else:
                raise Exception(f"Failed to parse plan JSON: {str(e)}\nResponse: {plan_content[:200]}")
        
        steps = plan["plan"]
        context = {}
        execution_log = []
        
        for i, step in enumerate(steps, 1):
            tool = step["tool"]
            step_desc = step.get("description", f"Executing {tool}")
            
            if progress_callback:
                progress_callback(f"[{i}/{len(steps)}] {step_desc}")
            else:
                print(f"\n[Step {i}/{len(steps)}] {step_desc}")
            
            inputs = {}
            for k, v in step["inputs"].items():
                if isinstance(v, str) and v.startswith('$prev.'):
                    key = v.replace('$prev.', '')
                    inputs[k] = context.get(key, v)
                else:
                    inputs[k] = v
            
            step_start = datetime.now()
            try:
                logger.info(f"Executing step {i}/{len(steps)}: {tool}")
                if progress_callback:
                    progress_callback(f"[{i}/{len(steps)}] Executing: {step_desc}")
                
                result = self.call_tool(tool, inputs)
                context.update(result)
                step_elapsed = (datetime.now() - step_start).total_seconds()
                
                execution_log.append({
                    "step": i,
                    "tool": tool,
                    "description": step_desc,
                    "status": "success",
                    "duration_seconds": step_elapsed,
                    "output_keys": list(result.keys()) if isinstance(result, dict) else []
                })
                
                logger.info(f"Step {i} completed in {step_elapsed:.2f}s. Output keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                
                if progress_callback:
                    progress_callback(f"✓ Step {i} completed in {step_elapsed:.1f}s: {tool}")
            except Exception as e:
                step_elapsed = (datetime.now() - step_start).total_seconds()
                error_msg = str(e)
                logger.error(f"Step {i} failed after {step_elapsed:.2f}s: {error_msg}")
                
                execution_log.append({
                    "step": i,
                    "tool": tool,
                    "description": step_desc,
                    "status": "error",
                    "duration_seconds": step_elapsed,
                    "error": error_msg
                })
                
                if progress_callback:
                    progress_callback(f"✗ Step {i} failed after {step_elapsed:.1f}s: {error_msg}")
                raise
        
        return {
            "context": context,
            "execution_log": execution_log,
            "final_result": context
        }

if __name__ == "__main__":
    mcp_client = MCPClient("http://localhost:8000")
    goal = "Generate a blog post from a YouTube video: https://youtube.com/watch?v=uMzUB89uSxU"
    result = mcp_client.plan_and_execute(goal)
    print("\n" + "="*60)
    print("EXECUTION COMPLETE")
    print("="*60)
    print(f"\nFinal Result: {json.dumps(result.get('final_result', {}), indent=2)}")
    print(f"\nExecution Log: {json.dumps(result.get('execution_log', []), indent=2)}")
