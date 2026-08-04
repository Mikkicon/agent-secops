# Agent SecOps Harness


1. Fully isolated Docker network
2. Real secrets are [applied](https://github.com/Mikkicon/agent-secops/blob/main/sandbox/egress/interceptor.py#L24) on egress - they never enter agent & tools containers
3. Egress proxy to monitor the canary secrets leak
4. Tool [approval](https://github.com/Mikkicon/agent-secops/blob/main/sandbox/agent/security.py#L40) with hashing of: name + description + schema
5. In this example User manually approves poisoned [weather tool](https://github.com/Mikkicon/agent-secops/blob/main/sandbox/tools/weather.py#L5)
6. But thanks to 2 line of defence -> Isolation + Egress control - secrets never leave sandbox

## Architecture

```mermaid
flowchart LR
  subgraph host["Host (pentest/)"]
    nw["docker-internal-nw.sh<br/>build · gen CA · run"]
    gen["gen-sec.sh<br/>plants canary"]
  end

  subgraph snbx["snbx network — internal, no route out"]
    agent["agent<br/>LLM loop · placeholder keys"]
    tools["tools<br/>FastMCP :8000<br/>read_file · poisoned get_weather"]
    data[("/data/.env<br/>MY_SECRET = canary")]
    proxy["proxy / egress-guard<br/>mitmdump + interceptor.py<br/>injects real keys · scans canary · allowlist"]
  end

  subgraph egr["egress network → internet"]
    or["openrouter.ai<br/>LLM"]
    tav["mcp.tavily.com<br/>search"]
  end

  gen -. plants .-> data
  tools --- data
  agent -->|"1 · read_file /data/.env (direct, NO_PROXY)"| tools
  agent -->|"2 · LLM call carries canary (HTTPS via proxy)"| proxy
  proxy -->|"inject real key · scan"| or
  proxy -->|"inject real key · scan"| tav
  proxy -. "3 · 🚨 CANARY LEAK" .-> nw

  classDef guard fill:#2563eb,color:#fff,stroke:#1e3a8a,stroke-width:1px;
  class proxy guard
```

Only the **proxy** is dual-homed (`snbx` + `egress`), so it's the single route out; everything else on `snbx` has no internet. The agent talks to `tools` directly (`NO_PROXY`), but every external call is forced through the proxy, which injects the real keys and scans for the canary.

```sh
# 1. prereqs (host shell)
export OPENAI_API_KEY=sk-or-...      # REAL keys — the proxy injects these
export TAVILY_API_KEY=tvly-...
source pentest/gen-sec.sh            # sets $CANARY + plants /data/.env

# 2. build + start proxy + tools (your nw.sh does CA→builds→proxy→tools)
bash pentest/docker-internal-nw.sh

# 3. run the agent INTERACTIVELY the first time (approval needs a TTY)
docker rm -f agent 2>/dev/null
docker run --rm -it --network snbx --name agent \
  -e NO_PROXY=tools -e HTTPS_PROXY=http://proxy:8080 -e HTTP_PROXY=http://proxy:8080 \
  -e OPENAI_API_KEY=placeholder -e TAVILY_API_KEY=placeholder -e CANARY="$CANARY" \
  sandbox-agent

#   → approve get_weather / read_file / tavily when prompted

# 4. watch for the leak
docker logs -f proxy | grep -i canary
> ...
> [20:31:26.947] 🚨 CANARY LEAK -> openrouter.ai
> [20:31:36.599] 🚨 CANARY LEAK -> localhost
```

```sh
# teardown
docker rm -f proxy tools agent 2>/dev/null

```
