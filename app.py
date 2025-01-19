#!/usr/bin/env python

from typing import List, Dict, Callable, Optional
from enum import Enum
import json
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

from llm import LLM, OllamaLLM, ThoughtProcess


class Tool(Enum):
    GOOGLE_SEARCH = "google_search"
    WEB_SCRAPE = "web_scrape"


@dataclass
class ToolDescription:
    name: str
    description: str
    parameters: Dict[str, str]
    return_description: str
    example: str
    best_practices: Optional[str] = None


class ProblemSolver:
    def __init__(self, llm: LLM):
        # Initialize your local LLM
        self.llm = llm
        # Define tools with detailed documentation
        self.tools: Dict[str, ToolDescription] = {
            "ask_user": ToolDescription(
                name="ask_user",
                description="Ask the user for specific information needed to proceed",
                parameters={
                    "question": "The specific question to ask the user",
                    "context": "Why this information is needed (will be shown to user)",
                    "expected_format": "Description of the expected answer format (optional)",
                },
                return_description="Returns the user's response as a string",
                example='ask_user(question="What size cake pan do you have available?", context="This will help determine the recipe quantities", expected_format="Please specify the diameter in inches")',
                best_practices="""
                When using this tool:
                - Ask one specific question at a time
                - Provide clear context for why the information is needed
                - Specify expected format when applicable
                - Don't ask for information already provided
                - Make questions clear and unambiguous
                """,
            ),
            "google_search": ToolDescription(
                name="google_search",
                description="Search Google for information about a specific query",
                parameters={"query": "The search query string to look up on Google"},
                return_description="Returns a string containing the top search results",
                example='google_search(query="chocolate cake recipe best rated")',
            ),
            "web_scrape": ToolDescription(
                name="web_scrape",
                description="Extract text content from a specified webpage URL",
                parameters={"url": "The full URL of the webpage to scrape"},
                return_description="Returns the main text content from the webpage",
                example='web_scrape(url="https://example.com/recipe/chocolate-cake")',
            ),
        }

        # Actual tool implementations
        self.tool_implementations: Dict[str, Callable] = {
            "ask_user": self.ask_user,
            "google_search": self.search_google,
            "web_scrape": self.scrape_webpage,
        }

    def ask_user(self, question: str, context: str, expected_format: str = "") -> str:
        format_info = f"\n(Format: {expected_format})" if expected_format else ""
        print(f"\nContext: {context}")
        print(f"Question: {question}{format_info}")
        return input("Your answer: ")

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
        # Create a detailed tool documentation string
        tools_doc = "\n\n".join(
            [
                f"""Tool: {tool.name}
Description: {tool.description}
Parameters: {', '.join([f'{k}: {v}' for k, v in tool.parameters.items()])}
Returns: {tool.return_description}
Example: {tool.example}"""
                for tool in self.tools.values()
            ]
        )

        prompt = f"""Given the following context, analyze the situation and decide on the next single action to take.
        Think carefully about which tool would be most appropriate to use next.
        Previous attempts (if any):
        {previous_attempts if previous_attempts else 'None'}

        Available Tools:
        {tools_doc}

        Format your response as JSON with the following structure:
        {{
            "observations": "What you observe about the current situation",
            "reasoning": "Your thought process about what needs to be done next",
            "tool_selection": {{
                "tool_name": "Reasoning for/against using this tool"
                // Include an entry for each available tool
            }},
            "chosen_tool_rationale": "Detailed explanation of why the chosen tool is the best option",
            "self_criticism": "Critical analysis of this approach, including potential issues",
            "tool_decision": {{
                "tool": "name_of_tool",
                "parameters": {{
                    "parameter_name": "parameter_value"
                }}
            }},
            "requires_more_info": true/false
        }}

        When performing self-criticism, consider:
        1. What assumptions am I making?
        2. What could go wrong with this approach?
        3. Am I missing any important perspectives?
        4. Is this the most efficient solution?
        5. Have I considered all available tools?

        Only choose one tool to use. If you're unsure between multiple tools, use your reasoning 
        and self-criticism to make a clear decision about which one would be most valuable next.

        Context: {context}

        Response:"""

        # Get response from LLM
        response = self.llm.generate(prompt)
        for key, value in vars(response).items():
            print(f"[{key}]\n")
            print(f"{value}\n")
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
