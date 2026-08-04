# Agent SecOps Harness


1. Fully isolated Docker network
2. Real secrets are [applied](https://github.com/Mikkicon/agent-secops/blob/main/sandbox/egress/interceptor.py#L24) on egress - they never enter agent & tools containers
3. Egress proxy to monitor the canary secrets leak
4. Tool [approval](https://github.com/Mikkicon/agent-secops/blob/main/sandbox/agent/security.py#L40) with hashing of: name + description + schema
5. In this example User manually approves poisoned [weather tool](https://github.com/Mikkicon/agent-secops/blob/main/sandbox/tools/weather.py#L5)
6. But thanks to 2 line of defence -> Isolation + Egress control - secrets never leave sandbox

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
