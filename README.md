# Linkedin Automation Agent

And Testground for Security Breaches and Preventions
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
docker logs -f proxy | grep "CANARY LEAK"
```

Three things that will bite in this exact run:
- input() approval can't run detached — your nw.sh runs the agent with -d, which EOFErrors on the prompt. Run it with -it (step 3) until you seed allowed_tools.json.
- The config path is CWD-relative — the code opens sandbox/agent/allowed_tools.json, which works from the repo root on the host but not inside the container (WORKDIR /app, files are flat). Change it to os.path.join(Path(__file__).parent, "allowed_tools.json") so it resolves in both, or approval silently reads/writes nothing.
- Keys: real ones on the host (proxy injects), placeholders on the agent — as above.

Once approval writes allowed_tools.json with get_weather/read_file/tavily, re-runs can go back to -d. Fix the path first — otherwise step 3 will loop right back to agent.tools [].
