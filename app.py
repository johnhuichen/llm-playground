#!/usr/bin/env python

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum
import json
import requests
from bs4 import BeautifulSoup
from typing import Callable

from llm import LLM, OllamaLLM


@dataclass
class ThoughtProcess:
    observations: str
    reasoning: str
    plan: List[str]
    self_criticism: str
    confidence: float
    alternative_approaches: List[str]
    next_action: str
    requires_more_info: bool


class Tool(Enum):
    GOOGLE_SEARCH = "google_search"
    WEB_SCRAPE = "web_scrape"


class ProblemSolver:
    def __init__(self, llm: LLM):
        # Initialize your local LLM
        self.llm = llm
        # Register available tools
        self.tools: Dict[str, Callable] = {
            Tool.GOOGLE_SEARCH.value: self.search_google,
            Tool.WEB_SCRAPE.value: self.scrape_webpage,
        }

    def search_google(self, query: str) -> str:
        # Implement your Google search function here
        # This is a placeholder
        return f"Search results for: {query}"

    def scrape_webpage(self, url: str) -> str:
        # Basic web scraping implementation
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            return soup.get_text()[:1000]  # First 1000 chars for brevity
        except Exception as e:
            return f"Error scraping webpage: {str(e)}"

    def get_thought_process(
        self, context: str, previous_attempts: List[str] = []
    ) -> ThoughtProcess:
        prompt = f"""Given the following context and any previous attempts, analyze the situation including self-reflection.
        Previous attempts (if any):
        {previous_attempts if previous_attempts else 'None'}

        Format your response as JSON with the following structure:
        {{
            "observations": "What you observe about the current situation",
            "reasoning": "Your reasoning about what to do next",
            "plan": ["Step 1", "Step 2", ...],
            "self_criticism": "Critical analysis of your approach, potential pitfalls, and biases",
            "confidence": 0.0-1.0,
            "alternative_approaches": ["Alternative 1", "Alternative 2"],
            "next_action": "The next action to take (either google_search or web_scrape)",
            "requires_more_info": true/false
        }}

        When performing self-criticism, consider:
        1. What assumptions am I making?
        2. What could go wrong with this approach?
        3. Am I missing any important perspectives?
        4. Is this the most efficient solution?
        5. Have I considered all available tools?

        Context: {context}

        Response:"""

        # Get response from LLM
        response = self.llm.generate(prompt)
        print(response)
        # response = self.llm(
        #     prompt,
        #     max_tokens=512,
        #     temperature=0.7,
        #     stop=["```"],
        # )
        raise Exception("test")

        try:
            thought_json = json.loads(response["choices"][0]["text"])
            return ThoughtProcess(**thought_json)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}")

    def solve_problem(self, problem: str, max_steps: int = 5) -> str:
        context = problem
        solution_steps = []
        previous_attempts = []

        for step in range(max_steps):
            # Get the next thought process with previous attempts for reflection
            thought = self.get_thought_process(context, previous_attempts)

            step_summary = f"""
Step {step + 1}:
Reasoning: {thought.reasoning}
Self-Criticism: {thought.self_criticism}
Confidence: {thought.confidence * 100}%
Alternative Approaches Considered: {', '.join(thought.alternative_approaches)}
"""
            solution_steps.append(step_summary)

            # If confidence is too low, try an alternative approach
            if thought.confidence < 0.4 and thought.alternative_approaches:
                context += f"\nSwitching to alternative approach: {thought.alternative_approaches[0]}"
                previous_attempts.append(
                    f"Abandoned approach due to low confidence: {thought.reasoning}"
                )
                continue

            if not thought.requires_more_info:
                break

            # Execute the next action using appropriate tool
            if thought.next_action in self.tools:
                tool_fn = self.tools[thought.next_action]
                result = tool_fn(context)
                context += f"\nNew information:\n{result}"
                previous_attempts.append(
                    f"Attempted action: {thought.next_action} - Result length: {len(result)}"
                )

        return "\n\n".join(solution_steps)


# Example usage
def main():
    llm = OllamaLLM()
    solver = ProblemSolver(llm)

    problem = """
    I want to buy a noise-cancelling earphone with a budget of less than $200
    """

    solution = solver.solve_problem(problem)
    print(solution)


if __name__ == "__main__":
    main()
