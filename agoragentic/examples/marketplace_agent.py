"""Starter Syrin agent that uses Agoragentic as an execute-first capability router.

Environment:
    OPENAI_API_KEY=...
    AGORAGENTIC_API_KEY=...

Run:
    python agoragentic/examples/marketplace_agent.py
    python agoragentic/examples/marketplace_agent.py "Summarize the attached report and save a reusable lesson."
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from syrin import Agent, Budget, Model
from syrin.enums import ExceedPolicy

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agoragentic.agoragentic_syrin import AgoragenticTools


SYSTEM_PROMPT = """
You are a marketplace-native software research and execution agent.

Operating rules:
- Prefer agoragentic_match before paid execution when task fit is unclear.
- Prefer agoragentic_execute for real work instead of hard-coding provider IDs.
- Use agoragentic_memory_search before repeating prior research.
- Save durable takeaways with agoragentic_save_learning_note when you discover a reusable workflow lesson.
- Use agoragentic_invoke only when the user explicitly wants a known listing.
""".strip()


def _build_agent() -> Agent:
    """Create the example agent after environment variables are loaded."""
    return Agent(
        model=Model.OpenAI("gpt-4o-mini", api_key=os.environ["OPENAI_API_KEY"]),
        budget=Budget(max_cost=5.00, exceed_policy=ExceedPolicy.STOP),
        system_prompt=SYSTEM_PROMPT,
        tools=AgoragenticTools(api_key=os.environ["AGORAGENTIC_API_KEY"]),
    )


def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("Set OPENAI_API_KEY before running this example.")
    if not os.environ.get("AGORAGENTIC_API_KEY"):
        raise RuntimeError("Set AGORAGENTIC_API_KEY before running this example.")

    prompt = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "Find a strong marketplace provider for summarizing technical papers under $0.25, "
            "run it on a short sample input, then save one reusable lesson about the workflow."
        )
    )

    result = _build_agent().run(prompt)
    print(result.content)
    if getattr(result, "cost", None) is not None:
        print(f"\nSyrin tracked cost: ${result.cost:.6f}")


if __name__ == "__main__":
    main()
