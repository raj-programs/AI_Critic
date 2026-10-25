
# app/services/hci/analyzer.py

import json
from difflib import SequenceMatcher
from typing import Any


SEVERITY_WEIGHTS = {
    "critical": 20,
    "high": 10,
    "medium": 5,
    "low": 2,
    "info": 0,
}

SEVERITY_ALIASES = {
    "blocker": "critical",
    "major": "high",
    "moderate": "medium",
    "minor": "low",
    "informational": "info",
}

SOURCE_PRIORITY = {
    "hci_rule": 3,
    "vlm": 2,
    "critic": 1,
}

RATINGS = [
    (90, "Excellent"),
    (75, "Good"),
    (60, "Needs improvement"),
    (40, "Poor"),
    (0, "Critical usability concerns"),
]


def to_dict(value: Any) -> dict:
    """Convert dictionaries and Pydantic models to dictionaries."""
    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump(
            mode="json",
            by_alias=True,
        )

    if hasattr(value, "dict"):
        return value.dict(by_alias=True)

    return {}


def to_text(value: Any) -> str:
    """Safely convert evidence and other values into readable text."""
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, (dict, list, tuple)):
        return json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        )

    return str(value)


def normalize_severity(value: Any) -> str:
    """Normalize severity labels from different analysis sources."""
    severity = to_text(value).strip().lower()
    severity = SEVERITY_ALIASES.get(severity, severity)

    if severity not in SEVERITY_WEIGHTS:
        return "medium"

    return severity


def normalize_finding(
    finding: Any,
    source: str,
) -> dict:
    """Convert one finding into the common report format."""
    finding = to_dict(finding)

    heuristic = finding.get("heuristic", {})
    if not isinstance(heuristic, dict):
        heuristic = to_dict(heuristic)

    evidence = finding.get(
        "evidence",
        finding.get(
            "visual_evidence",
            finding.get("description", ""),
        ),
    )

    normalized = {
        "id": to_text(finding.get("id", "")),
        "source": source,
        "category": to_text(
            finding.get(
                "category",
                heuristic.get("name", "Usability"),
            )
        ),
        "heuristic": heuristic,
        "severity": normalize_severity(
            finding.get("severity", "medium")
        ),
        "element": to_text(
            finding.get(
                "element",
                finding.get(
                    "element_description",
                    finding.get("selector", "Unknown element"),
                ),
            )
        ),
        "problem": to_text(
            finding.get(
                "problem",
                finding.get("issue", ""),
            )
        ),
        "evidence": to_text(evidence),
        "user_impact": to_text(
            finding.get("user_impact", "")
        ),
        "recommendation": to_text(
            finding.get(
                "recommendation",
                finding.get("suggestion", ""),
            )
        ),
        "confidence": finding.get("confidence"),
    }

    confidence = normalized["confidence"]

    try:
        if confidence is not None:
            normalized["confidence"] = max(
                0.0,
                min(1.0, float(confidence)),
            )
    except (TypeError, ValueError):
        normalized["confidence"] = None

    return normalized


def _similarity(first: str, second: str) -> float:
    """Calculate normalized text similarity."""
    first = first.strip().lower()
    second = second.strip().lower()

    if not first or not second:
        return 0.0

    return SequenceMatcher(None, first, second).ratio()


def are_duplicates(
    first: dict,
    second: dict,
) -> bool:
    """Conservatively detect findings describing the same issue."""
    first_problem = first["problem"]
    second_problem = second["problem"]

    first_element = first["element"]
    second_element = second["element"]

    same_element = (
        first_element.lower() == second_element.lower()
    )

    problem_similarity = _similarity(
        first_problem,
        second_problem,
    )

    # Same problem on the same element.
    if same_element and problem_similarity >= 0.70:
        return True

    # Similar descriptions with substantial textual overlap.
    if problem_similarity >= 0.92:
        return True

    # Matching rule IDs can establish duplicate identity.
    if (
        first["source"] == "hci_rule"
        and second["source"] == "hci_rule"
        and first["id"]
        and first["id"] == second["id"]
    ):
        return True

    return False


def _merge_text(existing: str, incoming: str) -> str:
    """Merge distinct text without repeating identical content."""
    if not incoming:
        return existing

    if not existing:
        return incoming

    if incoming.strip().lower() in existing.strip().lower():
        return existing

    if existing.strip().lower() in incoming.strip().lower():
        return incoming

    return f"{existing}\nAdditional evidence: {incoming}"


def merge_duplicate(
    existing: dict,
    incoming: dict,
) -> dict:
    """Combine information from duplicate findings."""
    if (
        SOURCE_PRIORITY.get(incoming["source"], 0)
        > SOURCE_PRIORITY.get(existing["source"], 0)
    ):
        # Prefer the stronger source's core finding while retaining
        # evidence and metadata already collected.
        preferred = incoming.copy()
        secondary = existing
    else:
        preferred = existing.copy()
        secondary = incoming

    preferred["evidence"] = _merge_text(
        preferred["evidence"],
        secondary["evidence"],
    )

    preferred["user_impact"] = _merge_text(
        preferred["user_impact"],
        secondary["user_impact"],
    )

    preferred["recommendation"] = _merge_text(
        preferred["recommendation"],
        secondary["recommendation"],
    )

    if not preferred["heuristic"]:
        preferred["heuristic"] = secondary["heuristic"]

    if not preferred["category"]:
        preferred["category"] = secondary["category"]

    if preferred["confidence"] is None:
        preferred["confidence"] = secondary["confidence"]

    sources = set(
        preferred.get("sources", [preferred["source"]])
    )
    sources.update(
        secondary.get("sources", [secondary["source"]])
    )
    preferred["sources"] = sorted(sources)

    return preferred


def merge_findings(
    hci_findings=None,
    vlm_result=None,
    critic_result=None,
) -> list[dict]:
    """Normalize and merge findings from all analysis stages."""
    normalized = []

    # Deterministic HCI rules.
    for finding in hci_findings or []:
        normalized.append(
            normalize_finding(finding, "hci_rule")
        )

    # VLM output may be a Pydantic model, dict, or list.
    vlm_data = to_dict(vlm_result)

    vlm_findings = (
        vlm_data.get("findings", [])
        if vlm_data
        else vlm_result
    )

    if isinstance(vlm_findings, list):
        for finding in vlm_findings:
            normalized.append(
                normalize_finding(finding, "vlm")
            )

    # AI Critic output may also be a model, dict, or list.
    critic_data = to_dict(critic_result)

    critic_findings = (
        critic_data.get("findings", [])
        if critic_data
        else critic_result
    )

    if isinstance(critic_findings, list):
        for finding in critic_findings:
            normalized.append(
                normalize_finding(finding, "critic")
            )

    merged = []

    for finding in normalized:
        duplicate_index = None

        for index, existing in enumerate(merged):
            if are_duplicates(existing, finding):
                duplicate_index = index
                break

        if duplicate_index is None:
            finding["sources"] = [finding["source"]]
            merged.append(finding)
        else:
            merged[duplicate_index] = merge_duplicate(
                merged[duplicate_index],
                finding,
            )

    # Stable, predictable ordering.
    severity_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "info": 4,
    }

    merged.sort(
        key=lambda item: (
            severity_order.get(item["severity"], 5),
            item["problem"].lower(),
        )
    )

    return merged


def calculate_score(findings: list[dict]) -> dict:
    """
    Calculate a provisional severity-weighted score.

    This is a heuristic score, not a validated usability metric.
    """
    total_penalty = sum(
        SEVERITY_WEIGHTS.get(
            normalize_severity(item.get("severity")),
            0,
        )
        for item in findings
    )

    score = max(0, min(100, 100 - total_penalty))

    rating = next(
        label
        for minimum, label in RATINGS
        if score >= minimum
    )

    severity_counts = {
        severity: sum(
            1
            for item in findings
            if normalize_severity(item.get("severity"))
            == severity
        )
        for severity in SEVERITY_WEIGHTS
    }

    return {
        "score": score,
        "rating": rating,
        "total_findings": len(findings),
        "severity_counts": severity_counts,
        "scoring_note": (
            "Provisional heuristic score based on finding severity. "
            "It is not a validated measure of overall usability."
        ),
    }


def analyze_results(
    crawl_data,
    hci_findings=None,
    vlm_result=None,
    critic_result=None,
) -> dict:
    """Build the final report from all analysis stages."""
    findings = merge_findings(
        hci_findings=hci_findings,
        vlm_result=vlm_result,
        critic_result=critic_result,
    )

    score_data = calculate_score(findings)

    return {
        "url": crawl_data.get("url", ""),
        "score": score_data["score"],
        "rating": score_data["rating"],
        "summary": {
            "total_findings": score_data["total_findings"],
            "severity_counts": score_data["severity_counts"],
            "scoring_note": score_data["scoring_note"],
        },
        "findings": findings,
    }
