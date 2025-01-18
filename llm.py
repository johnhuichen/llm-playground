import json
import ollama


class GenerateResponse:
    def __init__(
        self,
        observations: str,
        reasoning: str,
        plan: list[str],
        next_action: str,
        requires_more_info: bool,
    ):
        self.observations = observations
        self.reasoning = reasoning
        self.plan = plan
        self.next_action = next_action
        self.requires_more_info = requires_more_info

    def __str__(self) -> str:
        plan = "\n".join([f"{i+1}. {line}" for i, line in enumerate(self.plan)])
        return f"""[Observations]
{self.observations}

[Reasoning]
{self.reasoning}

[Requires More Info]
{self.requires_more_info}

[Plan]
{plan}

[Next Action]
{self.next_action}
"""


class LLM:
    def __str__(self) -> str:
        raise Exception("not implemented")

    def __repr__(self):
        return self.__str__()

    def generate(self, prompt: str) -> GenerateResponse:
        raise Exception("not implemented")


class OllamaLLM(LLM):
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name

    def __str__(self) -> str:
        return "Ollama"

    def generate(self, prompt: str) -> GenerateResponse:
        ollama_response = ollama.generate(model="llama3.2", prompt=prompt)
        ollama_response = json.loads(ollama_response.response)
        response = GenerateResponse(
            observations=ollama_response["observations"],
            reasoning=ollama_response["reasoning"],
            plan=ollama_response["plan"],
            next_action=ollama_response["next_action"],
            requires_more_info=ollama_response["requires_more_info"],
        )
        return response
