from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

# ---------- 1) Graph state ----------
class AgentState(BaseModel):
    question: str
    intent: str | None = None   # "kpi" | "sentiment" | "fallback"
    answer: str | None = None

# ---------- 2) Planner (sets intent) ----------
def node_plan(state: AgentState) -> AgentState:
    q = state.question.lower()
    intent = "fallback"
    if any(k in q for k in ["revenue", "sales", "units", "trend", "top", "leaderboard"]):
        intent = "kpi"
    if any(k in q for k in ["sentiment", "feedback", "review"]):
        intent = "sentiment"
    return state.model_copy(update={"intent": intent})

# Router function used by add_conditional_edges
def route_from_intent(state: AgentState) -> str:
    return state.intent or "fallback"

# ---------- 3) Branch nodes ----------
def node_kpi(state: AgentState) -> AgentState:
    # (Stub) In Step 3 we'll compute from CSV via pandas
    return state.model_copy(update={"answer": "KPI branch: I would compute metrics (revenue/units) and return a chart."})

def node_sentiment(state: AgentState) -> AgentState:
    # (Stub) In Step 3 we'll aggregate feedback by day and plot
    return state.model_copy(update={"answer": "Sentiment branch: I would aggregate daily sentiment from feedback data and plot a trend."})

def node_fallback(state: AgentState) -> AgentState:
    return state.model_copy(update={"answer": "Sorry, I didn’t understand. Try asking about revenue trend, top products, store leaderboard, or sentiment."})

# ---------- 4) Build the graph ----------
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("plan", node_plan)
    g.add_node("kpi", node_kpi)
    g.add_node("sentiment", node_sentiment)
    g.add_node("fallback", node_fallback)

    g.add_edge(START, "plan")
    # conditional branching based on planner output
    g.add_conditional_edges(
        "plan",
        route_from_intent,
        {
            "kpi": "kpi",
            "sentiment": "sentiment",
            "fallback": "fallback",
        },
    )
    g.add_edge("kpi", END)
    g.add_edge("sentiment", END)
    g.add_edge("fallback", END)
    return g.compile()

graph = build_graph()


# ---------- 5) Try it ----------
if __name__ == "__main__":

    for q in [
        "Show revenue trend for last 30 days",
        "What’s the daily customer sentiment?",
        "Tell me something random"
    ]:
        final = graph.invoke(AgentState(question=q))
        print(f"\nQ: {q}\nA: {final['answer']}")
