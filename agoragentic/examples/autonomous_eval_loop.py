"""Autonomous evaluation loop scaffold for Syrin plus Agoragentic.

The example demonstrates a measurable loop:

task -> Agoragentic execute payload -> grader -> attempt record -> reflection

Safe default:
    This file builds and scores local preview records. It does not call
    Agoragentic, spend funds, stage git changes, or deploy code.

Run:
    python agoragentic/examples/autonomous_eval_loop.py
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from typing import Any


DEFAULT_TASK = "Route a research summary task through Agoragentic under a budget cap."


@dataclass(frozen=True)
class TaskDefinition:
    """Task plus deterministic grader requirements."""

    name: str
    prompt: str
    required_terms: tuple[str, ...] = field(default_factory=tuple)
    forbidden_terms: tuple[str, ...] = field(default_factory=tuple)
    max_cost: float = 0.25


@dataclass(frozen=True)
class ScoreBundle:
    """Small deterministic score card for an attempt."""

    score: float
    passed: bool
    missing_terms: tuple[str, ...]
    forbidden_hits: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class AttemptRecord:
    """Serializable record of one preview or execution attempt."""

    task_name: str
    attempt_id: str
    mode: str
    execute_payload: dict[str, Any]
    score: ScoreBundle
    result_summary: dict[str, Any]
    reflection: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe attempt record."""
        return {
            "task_name": self.task_name,
            "attempt_id": self.attempt_id,
            "mode": self.mode,
            "execute_payload": self.execute_payload,
            "score": {
                "score": self.score.score,
                "passed": self.score.passed,
                "missing_terms": list(self.score.missing_terms),
                "forbidden_hits": list(self.score.forbidden_hits),
                "notes": list(self.score.notes),
            },
            "result_summary": self.result_summary,
            "reflection": self.reflection,
        }


def build_execute_payload(task: TaskDefinition) -> dict[str, Any]:
    """Build the router-first action proposal for the task."""
    return {
        "task": task.prompt,
        "input": {
            "task": task.prompt,
            "eval_contract": {
                "required_terms": list(task.required_terms),
                "forbidden_terms": list(task.forbidden_terms),
            },
        },
        "constraints": {
            "max_cost": max(0.01, float(task.max_cost)),
            "prefer_execute": True,
        },
    }


def summarize_result(result: dict[str, Any]) -> dict[str, Any]:
    """Preserve useful result fields while avoiding secret leakage."""
    safe = redact_secrets(result)
    return {
        "status": safe.get("status", "previewed"),
        "provider": safe.get("provider"),
        "output": safe.get("output"),
        "error": safe.get("error"),
        "cost": safe.get("cost"),
    }


def redact_secrets(value: Any) -> Any:
    """Recursively redact obvious secret-bearing fields from attempt records."""
    secret_keywords = {"api_key", "apikey", "authorization", "secret", "token", "signing_key"}
    if isinstance(value, dict):
        return {
            key: "***REDACTED***"
            if is_secret_key(key, secret_keywords)
            else redact_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    return value


def is_secret_key(key: str, secret_keywords: set[str]) -> bool:
    """Return true when a field name looks secret-bearing."""
    normalized = key.lower().replace("-", "_")
    compact = normalized.replace("_", "")
    return any(keyword in normalized or keyword in compact for keyword in secret_keywords)


def normalize_text(value: Any) -> str:
    """Return lowercase searchable text for deterministic grading."""
    if isinstance(value, str):
        return value.lower()
    return json.dumps(value, sort_keys=True).lower()


def grade_result(task: TaskDefinition, result: dict[str, Any]) -> ScoreBundle:
    """Grade a result with required and forbidden term checks."""
    text = normalize_text(result.get("output", result))
    missing = tuple(term for term in task.required_terms if term.lower() not in text)
    forbidden = tuple(term for term in task.forbidden_terms if term.lower() in text)
    total_checks = max(1, len(task.required_terms) + len(task.forbidden_terms))
    successful_checks = total_checks - len(missing) - len(forbidden)
    score = max(0.0, successful_checks / total_checks)
    notes: list[str] = []
    if missing:
        notes.append("missing_required_terms")
    if forbidden:
        notes.append("forbidden_terms_present")
    if result.get("error"):
        notes.append("execution_error")
        score = min(score, 0.25)
    return ScoreBundle(
        score=round(score, 4),
        passed=score >= 0.8 and not missing and not forbidden and not result.get("error"),
        missing_terms=missing,
        forbidden_hits=forbidden,
        notes=tuple(notes),
    )


def classify_attempt(score: ScoreBundle, previous_best: float = 0.0) -> str:
    """Classify whether to keep, iterate, or discard this attempt."""
    if score.passed and score.score >= previous_best:
        return "keep"
    if score.score > previous_best:
        return "iterate"
    return "discard"


def build_reflection_note(
    task: TaskDefinition,
    score: ScoreBundle,
    decision: str,
) -> dict[str, Any]:
    """Turn a grader result into a next-step note."""
    if decision == "keep":
        next_step = "record_lesson_and_reuse_workflow"
    elif decision == "iterate":
        next_step = "tighten_prompt_or_schema_then_rerun"
    else:
        next_step = "do_not_reuse_without_manual_review"
    return {
        "task": task.name,
        "decision": decision,
        "score": score.score,
        "passed": score.passed,
        "root_causes": list(score.notes),
        "next_step": next_step,
    }


def build_attempt_record(
    task: TaskDefinition,
    result: dict[str, Any] | None = None,
    previous_best: float = 0.0,
    mode: str = "preview",
) -> AttemptRecord:
    """Build one attempt record from a preview or execution result."""
    observed = result or {
        "status": "previewed",
        "output": "Preview only. No provider execution was run.",
    }
    score = grade_result(task, observed)
    decision = classify_attempt(score, previous_best=previous_best)
    return AttemptRecord(
        task_name=task.name,
        attempt_id=f"{task.name}-{int(time.time())}",
        mode=mode,
        execute_payload=build_execute_payload(task),
        score=score,
        result_summary=summarize_result(observed),
        reflection=build_reflection_note(task, score, decision),
    )


def non_negative_float(value: str) -> float:
    """Parse a non-negative CLI float."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def main() -> None:
    """Print a preview attempt record."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default=DEFAULT_TASK)
    parser.add_argument("--max-cost", type=non_negative_float, default=0.25)
    args = parser.parse_args()

    task = TaskDefinition(
        name="custom-preview-eval",
        prompt=args.task,
        required_terms=("agoragentic",),
        forbidden_terms=("unbounded spend",),
        max_cost=args.max_cost,
    )
    record = build_attempt_record(task)
    print(json.dumps(record.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
