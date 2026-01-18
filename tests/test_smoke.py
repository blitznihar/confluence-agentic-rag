def test_smoke_imports():
    # Basic import smoke test so pytest discovers something
    import confluence_agentic_rag  # noqa: F401


def test_stub_llm_generates_text():
    from confluence_agentic_rag.llm.stub import StubLLM

    llm = StubLLM()
    out = llm.generate("hello")
    assert isinstance(out, str)
    assert "LLM stub" in out
