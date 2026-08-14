import base64
import os, logging
from mitmproxy import http

CANARY = os.environ.get("CANARY") or exit("proxy: CANARY unset")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ALLOW = {
  "api.tavily.com", 
  "mcp.tavily.com", 
  "openrouter.ai",
  "tools", # sandbox/tools container name
  # "localhost",
  "langfuse-web"
} 

LANGFUSE_AUTH = base64.b64encode(
  f"{os.environ['LANGFUSE_PUBLIC_KEY']}:{os.environ['LANGFUSE_SECRET_KEY']}".encode()
).decode()


def request(flow: http.HTTPFlow) -> None:
  r = flow.request
  blob = r.pretty_url + "\n".join(f"{k}:{v}" for k,v in r.headers.items()) + (r.get_text() or "")
  if CANARY in blob or "cnry_" in blob:
    logging.error("🚨 CANARY LEAK -> %s", r.pretty_host)
    flow.response = http.Response.make(403, b"secrets leak")
    return
  if r.pretty_host not in ALLOW:
    flow.response = http.Response.make(403, b"blocked")
    return
  # real secrets
  elif r.pretty_host == "openrouter.ai":
    r.headers["Authorization"] = "Bearer " + OPENAI_API_KEY
  elif r.pretty_host in {"api.tavily.com", "mcp.tavily.com"}:
    r.query["tavilyApiKey"] = TAVILY_API_KEY
  elif r.pretty_host == "langfuse-web":
    r.headers["Authorization"] = "Basic " + LANGFUSE_AUTH