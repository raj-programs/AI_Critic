# ============================================================
# Severity Configuration
# ============================================================

SEVERITY_WEIGHTS = {
    "critical": 20,
    "high": 10,
    "medium": 5,
    "low": 2
}


def get_severity_weight(severity: str) -> int:
    """
    Return the score penalty associated with a severity level.
    """

    return SEVERITY_WEIGHTS.get(
        severity,
        SEVERITY_WEIGHTS["medium"]
    )
    