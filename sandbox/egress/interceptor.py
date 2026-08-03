import os, logging
from mitmproxy import http

CANARY = os.environ["CANARY"] # CANARY requried
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ALLOW = {
  "api.tavily.com", 
  "mcp.tavily.com", 
  "openrouter.ai",
  "tools", # sandbox/tools container name
  # "localhost"
} 

def request(flow: http.HTTPFlow) -> None:
  r = flow.request
  blob = r.pretty_url + "\n".join(f"{k}:{v}" for k,v in r.headers.items()) + (r.get_text() or "")
  if CANARY in blob:
    logging.error("🚨 CANARY LEAK -> %s", r.pretty_host)
  if r.pretty_host not in ALLOW:
    flow.response = http.Response.make(403, b"blocked")
  # real secrets
  if r.pretty_host == "openrouter.ai":
    r.headers["Authorization"] = "Bearer " + OPENAI_API_KEY
  if r.pretty_host in {"api.tavily.com", "mcp.tavily.com"}:
    r.query["tavilyApiKey"] = TAVILY_API_KEY