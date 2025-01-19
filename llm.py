from dataclasses import dataclass
from typing import Any, Dict, List
import json
import ollama


@dataclass
class ThoughtProcess:
    observations: str
    reasoning: str
    plan: List[str]
    self_criticism: str
    tool_selection: Dict[str, str]
    chosen_tool_rationale: str
    tool_decision: Dict[str, Any]
    requires_more_info: bool = True


class LLM:
    def __str__(self) -> str:
        raise Exception("not implemented")

    def __repr__(self):
        return self.__str__()

    def generate(self, prompt: str) -> ThoughtProcess:
        raise Exception("not implemented")


class OllamaLLM(LLM):
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name

    def __str__(self) -> str:
        return "Ollama"

    def generate(self, prompt: str) -> ThoughtProcess:
        ollama_response = ollama.generate(model="llama3.2", prompt=prompt)
        response_json = json.loads(ollama_response.response)
        response = ThoughtProcess(**response_json)
        return response
