from __future__ import annotations
import os, re, csv, io, sys
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain.agents.agent_toolkits import SQLDatabaseToolkit, create_sql_agent

DB_PATH = os.getenv("LTW_DB_PATH", "data/lt_walmart_data.db")
OUT_DIR = "./outputs"; os.makedirs(OUT_DIR, exist_ok=True)

# ---------- Build the SQL agent once ----------
db = SQLDatabase.from_uri(
    f"sqlite:///{DB_PATH}",
    include_tables=["sales_data", "products", "stores", "inventory", "customer_feedback"],
    sample_rows_in_table_info=2,
)
llm = init_chat_model("gemini-2.5-flash", model_provider="google_vertexai")
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
sql_agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    agent_type="tool-calling",
    verbose=True
)

SAFETY_PREFIX = (
    "Use only SELECT. Never modify data. "
    "If grouping by day, use DATE(Date) AS Date. "
    "When feasible, return results as CSV (first line headers, comma-separated)."
)

# ---------- LangGraph state ----------
class AgentState(BaseModel):
    question: str
    raw_output: str | None = None
    result_csv_path: str | None = None
    chart_png_path: str | None = None
    message: str | None = None

# ---------- Helpers ----------
def parse_csv_from_text(text: str) -> Optional[Tuple[List[str], List[List[str]]]]:
    """
    Heuristic: if the agent returns CSV (headers on first line), parse it.
    Otherwise return None and we'll leave just the text answer.
    """
    # Quick check: at least two commas in the first line
    first_line = text.strip().splitlines()[0] if text.strip().splitlines() else ""
    if first_line.count(",") < 1:
        return None
    # Remove code fences if present
    cleaned = re.sub(r"^```(csv|CSV)?", "", text.strip(), flags=re.M)
    cleaned = re.sub(r"```$", "", cleaned, flags=re.M)
    try:
        reader = csv.reader(io.StringIO(cleaned))
        rows = list(reader)
        if not rows:
            return None
        header = rows[0]
        data = rows[1:]
        # basic sanity: same number of cols
        if any(len(r) != len(header) for r in data):
            return None
        return header, data
    except Exception:
        return None

def save_table(header: List[str], rows: List[List[str]], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)

def maybe_chart(header: List[str], rows: List[List[str]], question: str) -> Optional[str]:
    if len(header) < 2 or not rows:
        return None
    # try cast second column to float; if fails, skip chart
    try:
        y = [float(r[1]) for r in rows]
    except Exception:
        return None
    x = [r[0] for r in rows]
    fig = plt.figure(figsize=(9,4.5))
    # try time series
    from datetime import datetime as dt
    try:
        xdt = [dt.fromisoformat(str(v)) for v in x]
        plt.plot(xdt, y)
        plt.xlabel(header[0]); plt.ylabel(header[1]); plt.title(question)
    except Exception:
        plt.bar([str(v) for v in x[:30]], y[:30])
        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.ylabel(header[1]); plt.title(question)

    out_png = os.path.join(OUT_DIR, "chart.png")
    plt.tight_layout(); plt.savefig(out_png); plt.close(fig)
    return out_png

# ---------- Nodes ----------
def node_agent(state: AgentState) -> AgentState:
    out = sql_agent.invoke({"input": f"{SAFETY_PREFIX}\n\nQuestion: {state.question}"})
    return state.model_copy(update={"raw_output": out["output"]})

def node_parse_and_visualize(state: AgentState) -> AgentState:
    if not state.raw_output:
        return state.model_copy(update={"message": "No output from agent."})
    parsed = parse_csv_from_text(state.raw_output)
    if not parsed:
        # no CSV; just return text
        return state.model_copy(update={"message": state.raw_output})
    header, rows = parsed
    out_csv = os.path.join(OUT_DIR, "result.csv")
    save_table(header, rows, out_csv)
    chart_path = maybe_chart(header, rows, state.question)
    msg = f"Saved {out_csv}" + (f" and {chart_path}" if chart_path else "")
    return state.model_copy(update={"result_csv_path": out_csv, "chart_png_path": chart_path, "message": msg})

# ---------- Graph ----------
from langgraph.graph import StateGraph, START, END
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("agent", node_agent)
    g.add_node("parse_visualize", node_parse_and_visualize)
    g.add_edge(START, "agent")
    g.add_edge("agent", "parse_visualize")
    g.add_edge("parse_visualize", END)
    return g.compile()

graph = build_graph()

# ---------- CLI ----------
if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "Show revenue trend for the last 30 days"
    final = graph.invoke(AgentState(question=q))
    print("\n=== Agent Reply ===\n" + (final['message'] or ""))
