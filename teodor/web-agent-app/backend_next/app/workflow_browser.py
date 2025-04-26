import os, sys
from pathlib import Path

from marinabox import mb_start_browser, mb_stop_browser, mb_use_browser_tool

from langchain_core.messages import HumanMessage

def load_env_manually(dotenv_path):
    if os.path.exists(dotenv_path):
        with open(dotenv_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"')

from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.prebuilt import InjectedState

from langchain_anthropic import ChatAnthropic             # <- Anthropic model
# ------------------------------------------------------------------
# 0. Environment & secrets
# ------------------------------------------------------------------
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_env_manually(dotenv_path)

print(f"Loaded ANTHROPIC_API_KEY: {os.getenv('ANTHROPIC_API_KEY')}")

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key or api_key == "ANTHROPIC_API_KEY":
    raise RuntimeError(
        "ANTHROPIC_API_KEY is missing or empty. "
        f"Expected it in {dotenv_path} or your shell environment."
    )

from marinabox import MarinaboxSDK

# ------------------------------------------------------------------
# 1. Tools + model
# ------------------------------------------------------------------
tools      = [mb_use_browser_tool]
tool_node  = ToolNode(tools=tools)
llm        = ChatAnthropic(model="claude-3-opus-20240229", temperature=0, api_key=api_key)
agent_lm   = llm.bind_tools(tools)

# ------------------------------------------------------------------
# 2. LangGraph callbacks
# ------------------------------------------------------------------
def should_continue(state: InjectedState):
    msgs = state["messages"]
    if msgs and getattr(msgs[-1], "tool_calls", None):
        return Command(goto="tool_node")
    return Command(goto="stop_browser")

def call_model(state: InjectedState):
    usr = input("Human > ")
    if usr.strip().lower() == "stop_browser":
        # signal termination
        return {"messages": [], "session_id": state.get("session_id")}
    resp = agent_lm.invoke([HumanMessage(content=usr)])
    return {"messages": [resp], "session_id": state.get("session_id")}

# ------------------------------------------------------------------
# 3. Build graph
# ------------------------------------------------------------------
wf = StateGraph(dict)
wf.add_node("start_browser", mb_start_browser)   # returns {"session_id": "..."}
wf.add_node("agent",         call_model)
wf.add_node("tool_node",     tool_node)
wf.add_node("stop_browser",  mb_stop_browser)
wf.add_node("should_continue", should_continue)

wf.add_edge(START, "start_browser")
wf.add_edge("start_browser", "agent")
wf.add_edge("agent", "should_continue")
wf.add_edge("tool_node", "agent")
wf.add_edge("stop_browser", END)

app = wf.compile()

# ------------------------------------------------------------------
# 4. Run
# ------------------------------------------------------------------
state = app.invoke({"messages": [], "session_id": None})

# When stop_browser runs, `state` contains the last session-id
sid = state.get("session_id")
if sid:

    sdk     = MarinaboxSDK()
    sess    = sdk.get_session(sid)
    vnc_url = f"http://localhost:{sess.vnc_port}/vnc.html?resize=scale"
    print(f"\n✅ Session stopped. Embed with:\n<iframe src='{vnc_url}' … ></iframe>\n")
