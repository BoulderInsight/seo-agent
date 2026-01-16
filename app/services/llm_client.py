"""LLM client service for AI-powered analysis."""

import json
import os
import time
from typing import Optional


class LLMClient:
    """Client for interacting with LLM APIs (OpenAI or Anthropic)."""

    def __init__(self):
        """Initialize the LLM client based on environment configuration."""
        self.provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
        self.max_retries = 3
        self.retry_delay = 2

        if self.provider == "anthropic":
            import anthropic

            self.client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            self.model = "claude-sonnet-4-20250514"
        elif self.provider == "openai":
            import openai

            self.client = openai.OpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
            self.model = "gpt-4o"
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def analyze(
        self,
        system_prompt: str,
        content: str,
        max_tokens: int = 2000,
    ) -> str:
        """
        Send content to the LLM for analysis.

        Args:
            system_prompt: The system prompt describing the analysis task
            content: The content to analyze
            max_tokens: Maximum tokens in the response

        Returns:
            The LLM's response text

        Raises:
            Exception: If all retry attempts fail
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                if self.provider == "anthropic":
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": content}
                        ],
                    )
                    return response.content[0].text

                elif self.provider == "openai":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": content},
                        ],
                    )
                    return response.choices[0].message.content

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Check if it's a rate limit error
                if "rate" in error_str or "429" in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (attempt + 1)
                        time.sleep(wait_time)
                        continue

                # Check for other retryable errors
                if "timeout" in error_str or "connection" in error_str:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue

                # Non-retryable error
                break

        error_msg = f"LLM API error after {self.max_retries} attempts: {last_error}"
        if "api_key" in str(last_error).lower() or "authentication" in str(last_error).lower():
            error_msg = "Invalid API key. Please check your LLM API key in the .env file."
        elif "rate" in str(last_error).lower():
            error_msg = "Rate limit exceeded. Please wait a moment and try again."

        raise Exception(error_msg)

    def analyze_json(
        self,
        system_prompt: str,
        content: str,
        max_tokens: int = 2000,
    ) -> dict:
        """
        Send content to the LLM and parse the response as JSON.

        Args:
            system_prompt: The system prompt (should request JSON output)
            content: The content to analyze
            max_tokens: Maximum tokens in the response

        Returns:
            Parsed JSON response as a dictionary
        """
        response = self.analyze(system_prompt, content, max_tokens)

        # Try to extract JSON from the response
        try:
            # First, try direct parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re

            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # Return empty dict if parsing fails
            return {}
