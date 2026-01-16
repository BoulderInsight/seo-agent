#!/usr/bin/env python3
"""Entry point for the EngineOp application."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()


def validate_environment() -> bool:
    """Validate required environment variables."""
    provider = os.getenv("LLM_PROVIDER", "anthropic")

    if provider == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("ERROR: ANTHROPIC_API_KEY environment variable is required")
            print("Please set it in your .env file or environment")
            return False
        print(f"Using LLM provider: Anthropic")
    elif provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            print("ERROR: OPENAI_API_KEY environment variable is required")
            print("Please set it in your .env file or environment")
            return False
        print(f"Using LLM provider: OpenAI")
    else:
        print(f"ERROR: Unknown LLM_PROVIDER: {provider}")
        print("Supported providers: anthropic, openai")
        return False

    return True


def main() -> int:
    """Main entry point."""
    if not validate_environment():
        return 1

    from app import create_app

    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG", "0") == "1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
