from .base import LLM


class StubLLM(LLM):
    def generate(self, prompt: str) -> str:
        # Replace with Azure/OpenAI later
        return (
            "LLM stub: replace with a real model call.\n\n"
            "Here is the grounded context I would answer from:\n\n" + prompt[:2000]
        )
