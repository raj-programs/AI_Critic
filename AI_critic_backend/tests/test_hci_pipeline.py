from app.services.hci.analyzer import analyze_results
from app.services.hci.rules import run_all_rules


def _crawler_evidence():
    return {
        "url": "https://example.com",
        "accessibility": {
            "images": {
                "items": [{"index": 0, "visible": True, "alt": None, "src": "/hero.png"}]
            },
            "interactive": {
                "items": [
                    {
                        "index": 0,
                        "tag": "a",
                        "role": None,
                        "visible": True,
                        "text": "",
                        "aria_label": "",
                        "title": "",
                    }
                ]
            },
            "keyboard_navigation": {"items": []},
        },
        "forms": {
            "forms": {
                "items": [
                    {
                        "controls": {
                            "items": [
                                {
                                    "index": 0,
                                    "tag": "input",
                                    "type": "email",
                                    "visible": True,
                                    "id": "email",
                                    "name": "email",
                                    "label": None,
                                    "aria_label": None,
                                    "aria_labelledby": None,
                                    "placeholder": "Email address",
                                },
                                {
                                    "index": 1,
                                    "tag": "input",
                                    "type": "text",
                                    "visible": True,
                                    "id": "name",
                                    "name": "name",
                                    "label": "Name",
                                    "aria_label": None,
                                    "aria_labelledby": None,
                                    "placeholder": "Your name",
                                },
                            ]
                        }
                    }
                ]
            },
            "controls_outside_forms": {"items": []},
        },
        "interactive": {"buttons": {"items": []}},
        "layout": {"overflow": {"horizontal": False}, "interactive": {"items": []}},
        "media": {"images": {"items": []}},
        "structure": {"headings": {"counts": {"h1": 1}, "items": []}},
    }


def test_rules_produce_actionable_suggestions_from_collector_shapes():
    findings = run_all_rules(_crawler_evidence())
    by_id = {finding["id"]: finding for finding in findings}

    assert {"HCI-001", "HCI-002", "HCI-003"}.issubset(by_id)
    assert "alternative text" in by_id["HCI-001"]["recommendation"].lower()
    assert "accessible name" in by_id["HCI-002"]["recommendation"].lower()
    assert "descriptive label" in by_id["HCI-003"]["recommendation"].lower()
    assert by_id["HCI-003"]["evidence"]["id"] == "email"
    assert len([item for item in findings if item["id"] == "HCI-003"]) == 1


def test_final_report_preserves_hci_finding_when_critic_is_unavailable():
    hci_finding = run_all_rules(_crawler_evidence())[0]

    report = analyze_results(
        _crawler_evidence(),
        hci_findings=[hci_finding],
        vlm_result={"findings": []},
        critic_result={"findings": []},
    )

    assert report["summary"]["total_findings"] == 1
    assert report["findings"][0]["recommendation"] == hci_finding["recommendation"]
    assert report["findings"][0]["sources"] == ["hci_rule"]


def test_final_report_merges_evidence_matched_critic_duplicate():
    hci_finding = run_all_rules(_crawler_evidence())[2]
    critic_finding = {
        "id": "AI-001",
        "category": "form usability",
        "severity": "high",
        "element": "input",
        "problem": hci_finding["problem"],
        "evidence": "The email field has no associated label.",
        "user_impact": "Users may enter the wrong information.",
        "recommendation": "Associate the email field with a label.",
        "confidence": 0.9,
    }

    report = analyze_results(
        _crawler_evidence(),
        hci_findings=[hci_finding],
        vlm_result={"findings": []},
        critic_result={"findings": [critic_finding]},
    )

    assert report["summary"]["total_findings"] == 1
    assert report["findings"][0]["sources"] == ["critic", "hci_rule"]
