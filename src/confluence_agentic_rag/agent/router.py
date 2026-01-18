

def route(question: str) -> str:
    q = question.lower()
    keywords = ["what did we decide", "decision", "adr", "minutes",
                "why did we choose"]
    if any(k in q for k in keywords):
        return "confluence_decision_rag"
    return "unknown"
