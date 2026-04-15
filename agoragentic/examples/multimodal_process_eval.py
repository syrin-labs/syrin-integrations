"""Process-verified multimodal evaluation scaffold for Agoragentic/Syrin.

The example follows the Agentic-MME-style idea that multimodal agents should be
graded on process evidence, not only on final answers.

Safe default:
    This file records and scores local process events. It does not fetch image
    URLs, call visual tools, or spend funds.

Run:
    python agoragentic/examples/multimodal_process_eval.py
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from typing import Any


VISUAL_TOOLS = {"crop", "enhance", "ocr", "chart_read", "image_search"}
KNOWLEDGE_TOOLS = {"web_search", "fetch", "citation_check"}


@dataclass(frozen=True)
class ProcessEvent:
    """One tool-use or reasoning checkpoint event."""

    step: int
    event_type: str
    tool: str
    purpose: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe event."""
        return {
            "step": self.step,
            "event_type": self.event_type,
            "tool": self.tool,
            "purpose": self.purpose,
            "source": self.source,
        }


@dataclass(frozen=True)
class VisualArtifact:
    """Evidence-bearing visual artifact produced during a multimodal run."""

    artifact_id: str
    kind: str
    source_url: str
    reveals_decisive_evidence: bool
    provenance: str

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe artifact."""
        return {
            "artifact_id": self.artifact_id,
            "kind": self.kind,
            "source_url": self.source_url,
            "reveals_decisive_evidence": self.reveals_decisive_evidence,
            "provenance": self.provenance,
        }


def build_execute_payload(
    task: str,
    image_url: str,
    document_url: str | None,
    max_cost: float,
) -> dict[str, Any]:
    """Build a routed multimodal execute payload with a process contract."""
    return {
        "task": task,
        "input": {
            "task": task,
            "image_url": image_url,
            "document_url": document_url,
            "process_contract": {
                "log_visual_events": True,
                "log_search_events": True,
                "return_artifacts": True,
                "avoid_overthinking": True,
            },
        },
        "constraints": {
            "max_cost": max(0.01, float(max_cost)),
            "prefer_execute": True,
        },
    }


def score_multimodal_process(
    events: tuple[ProcessEvent, ...],
    artifacts: tuple[VisualArtifact, ...],
    max_expected_steps: int = 6,
) -> dict[str, Any]:
    """Score strategy, visual tool use, evidence, and overthinking."""
    tools = {event.tool for event in events}
    has_visual = bool(tools & VISUAL_TOOLS)
    has_knowledge = bool(tools & KNOWLEDGE_TOOLS)
    has_purpose = all(event.purpose.strip() for event in events)
    evidence_artifacts = [artifact for artifact in artifacts if artifact.reveals_decisive_evidence]

    strategy_score = 1.0 if has_visual and has_purpose else 0.5 if has_purpose else 0.0
    if has_knowledge:
        strategy_score = min(1.0, strategy_score + 0.25)
    visual_tool_score = 1.0 if has_visual else 0.0
    visual_evidence_score = 1.0 if evidence_artifacts else 0.0
    excess_steps = max(0, len(events) - max_expected_steps)
    overthinking_score = max(0.0, 1.0 - (excess_steps / max(1, max_expected_steps)))

    return {
        "strategy_score": round(strategy_score, 4),
        "visual_tool_score": round(visual_tool_score, 4),
        "visual_evidence_score": round(visual_evidence_score, 4),
        "overthinking_score": round(overthinking_score, 4),
        "event_count": len(events),
        "artifact_count": len(artifacts),
        "evidence_artifacts": [artifact.artifact_id for artifact in evidence_artifacts],
        "passed": strategy_score >= 0.75
        and visual_tool_score == 1.0
        and visual_evidence_score == 1.0
        and overthinking_score >= 0.5,
    }


def sample_events() -> tuple[ProcessEvent, ...]:
    """Return a small process log for demo output."""
    return (
        ProcessEvent(1, "tool", "crop", "isolate the diagram region", "image"),
        ProcessEvent(2, "tool", "ocr", "extract labels from the cropped region", "artifact:crop-1"),
        ProcessEvent(3, "tool", "fetch", "read the supporting specification", "document"),
    )


def sample_artifacts(image_url: str) -> tuple[VisualArtifact, ...]:
    """Return one evidence-bearing artifact for demo output."""
    return (
        VisualArtifact(
            artifact_id="artifact-ocr-1",
            kind="ocr_text",
            source_url=image_url,
            reveals_decisive_evidence=True,
            provenance="derived from crop event 1 and ocr event 2",
        ),
    )


def non_negative_float(value: str) -> float:
    """Parse a non-negative CLI float."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(parsed):
        raise argparse.ArgumentTypeError("must be finite")
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def main() -> None:
    """Print a multimodal process-eval preview."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="Inspect this image and cite decisive visual evidence.")
    parser.add_argument("--image-url", default="https://example.com/screenshot.png")
    parser.add_argument("--document-url", default="https://example.com/spec.pdf")
    parser.add_argument("--max-cost", type=non_negative_float, default=0.5)
    args = parser.parse_args()

    events = sample_events()
    artifacts = sample_artifacts(args.image_url)
    output = {
        "execute_payload": build_execute_payload(
            task=args.task,
            image_url=args.image_url,
            document_url=args.document_url,
            max_cost=args.max_cost,
        ),
        "process_events": [event.as_dict() for event in events],
        "visual_artifacts": [artifact.as_dict() for artifact in artifacts],
        "score": score_multimodal_process(events, artifacts),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
