from .heuristics import get_heuristic
# ============================================================
# Helper
# ============================================================

def create_issue(
    rule_id,
    heuristic_id,
    severity,
    element,
    problem,
    evidence,
    user_impact,
    recommendation
):
    """
    Create a standardized HCI issue.
    """

    heuristic = get_heuristic(heuristic_id)

    return {
        "id": rule_id,
        "heuristic": {
            "id": heuristic_id,
            "name": heuristic["name"]
        },
        "severity": severity,
        "element": element,
        "problem": problem,
        "evidence": evidence,
        "user_impact": user_impact,
        "recommendation": recommendation
    }


# ============================================================
# HCI-001
# Missing image alternative text
# ============================================================

def check_missing_image_alt(data):
    """
    Detect images that do not have an alt attribute.

    Heuristic:
        H6 - Recognition rather than recall
    """

    issues = []

    images = data.get("accessibility", {}).get(
        "images", {}
    ).get("items", [])

    for image in images:

        if not image.get("visible", True):
            continue

        alt = image.get("alt")

        if alt is None:

            issues.append(
                create_issue(
                    rule_id="HCI-001",
                    heuristic_id="H6",
                    severity="medium",
                    element="img",
                    problem="Image does not have alternative text.",
                    evidence={
                        "index": image.get("index"),
                        "src": image.get("src"),
                        "alt": None
                    },
                    user_impact=(
                        "Users who cannot see the image may not "
                        "understand its purpose or content."
                    ),
                    recommendation=(
                        "Provide meaningful alternative text. "
                        "If the image is purely decorative, use "
                        "an empty alt attribute."
                    )
                )
            )

    return issues


# ============================================================
# HCI-002
# Unnamed interactive elements
# ============================================================

def check_unnamed_interactive_elements(data):
    """
    Detect interactive elements that do not have a usable accessible name.

    Heuristic:
        H6 - Recognition rather than recall
    """

    issues = []

    interactive = data.get("accessibility", {}).get(
        "interactive", {}
    ).get("items", [])

    for element in interactive:

        if not element.get("visible", True):
            continue

        tag = element.get("tag")
        role = element.get("role")

        # Form controls and buttons have dedicated rules with richer evidence.
        if tag in {"button", "input", "select", "textarea"}:
            continue

        if tag != "a" and not role:
            continue

        text = (element.get("text") or "").strip()
        aria_label = (element.get("aria_label") or "").strip()
        title = (element.get("title") or "").strip()

        has_name = bool(
            text or
            aria_label or
            title
        )

        if not has_name:

            issues.append(
                create_issue(
                    rule_id="HCI-002",
                    heuristic_id="H6",
                    severity="high",
                    element=tag,
                    problem=(
                        "Interactive element does not have a "
                        "recognizable name."
                    ),
                    evidence={
                        "index": element.get("index"),
                        "tag": tag,
                        "role": role,
                        "text": text,
                        "aria_label": aria_label,
                        "title": title
                    },
                    user_impact=(
                        "Users may not understand what action "
                        "the control performs, particularly "
                        "screen-reader and keyboard users."
                    ),
                    recommendation=(
                        "Give the control a clear visible label "
                        "or an appropriate accessible name."
                    )
                )
            )

    return issues


# ============================================================
# HCI-003
# Form controls without labels
# ============================================================

def check_unlabeled_form_controls(data):
    """
    Detect form controls that do not have an associated label.

    Heuristic:
        H5 - Error prevention
    """

    issues = []

    forms = data.get("forms", {})

    controls = []
    for form in forms.get("forms", {}).get("items", []):
        controls.extend(form.get("controls", {}).get("items", []))

    controls.extend(
        forms.get("controls_outside_forms", {}).get("items", [])
    )

    for control in controls:

        if not control.get("visible", True):
            continue

        tag = control.get("tag")

        if tag not in ["input", "select", "textarea"]:
            continue

        input_type = (
            control.get("type") or ""
        ).lower()

        # Hidden inputs do not require visible labels.
        if input_type == "hidden":
            continue

        label = control.get("label")

        aria_label = (
            control.get("aria_label") or ""
        ).strip()

        aria_labelledby = (
            control.get("aria_labelledby") or ""
        ).strip()

        has_label = bool(
            label or
            aria_label or
            aria_labelledby
        )

        if not has_label:

            issues.append(
                create_issue(
                    rule_id="HCI-003",
                    heuristic_id="H5",
                    severity="high",
                    element=tag,
                    problem="Form control does not have an associated label.",
                    evidence={
                        "index": control.get("index"),
                        "tag": tag,
                        "type": input_type,
                        "name": control.get("name"),
                        "id": control.get("id"),
                        "placeholder": control.get("placeholder")
                    },
                    user_impact=(
                        "Users may not understand what information "
                        "the field expects, increasing the likelihood "
                        "of input errors."
                    ),
                    recommendation=(
                        "Associate the control with a descriptive "
                        "label or provide an appropriate accessible name."
                    )
                )
            )

    return issues


# ============================================================
# HCI-004
# Horizontal overflow
# ============================================================

def check_horizontal_overflow(data):
    """
    Detect horizontal page overflow.

    Heuristic:
        H8 - Aesthetic and minimalist design
    """

    issues = []

    layout = data.get("layout", {})

    overflow = layout.get("overflow", {})

    horizontal = overflow.get(
        "horizontal",
        False
    )

    overflow_amount = overflow.get(
        "horizontal_overflow",
        0
    )

    if horizontal:

        issues.append(
            create_issue(
                rule_id="HCI-004",
                heuristic_id="H8",
                severity="high",
                element="page",
                problem="Page has horizontal overflow.",
                evidence={
                    "horizontal_overflow": True,
                    "overflow_amount": overflow_amount,
                    "viewport_width": layout.get(
                        "viewport", {}
                    ).get("viewport_width"),
                    "document_width": layout.get(
                        "viewport", {}
                    ).get("document_width")
                },
                user_impact=(
                    "Users may need to scroll horizontally to "
                    "access content, especially on smaller screens."
                ),
                recommendation=(
                    "Identify the element causing the overflow "
                    "and make the layout responsive to the viewport."
                )
            )
        )

    return issues


# ============================================================
# HCI-005
# Broken images
# ============================================================

def check_broken_images(data):
    """
    Detect images that failed to load.

    Heuristic:
        H1 - Visibility of system status
    """

    issues = []

    images = data.get("media", {}).get(
        "images", {}
    ).get("items", [])

    for image in images:

        if not image.get("visible", True):
            continue

        if image.get("broken"):

            issues.append(
                create_issue(
                    rule_id="HCI-005",
                    heuristic_id="H1",
                    severity="medium",
                    element="img",
                    problem="Image failed to load.",
                    evidence={
                        "index": image.get("index"),
                        "src": image.get("src"),
                        "broken": True
                    },
                    user_impact=(
                        "Users may see missing visual content "
                        "or an incomplete interface."
                    ),
                    recommendation=(
                        "Verify the image URL and provide an "
                        "appropriate fallback when necessary."
                    )
                )
            )

    return issues


# ============================================================
# HCI-006
# Positive tabindex
# ============================================================

def check_positive_tabindex(data):
    """
    Detect positive tabindex values.

    Heuristic:
        H4 - Consistency and standards
    """

    issues = []

    keyboard = data.get(
        "accessibility", {}
    ).get(
        "keyboard_navigation", {}
    ).get(
        "items", []
    )

    for element in keyboard:

        tabindex = element.get("tabindex")

        if tabindex is None:
            continue

        try:
            tabindex_value = int(tabindex)
        except (ValueError, TypeError):
            continue

        if tabindex_value > 0:

            issues.append(
                create_issue(
                    rule_id="HCI-006",
                    heuristic_id="H4",
                    severity="medium",
                    element=element.get("tag"),
                    problem=(
                        "Element uses a positive tabindex value."
                    ),
                    evidence={
                        "index": element.get("index"),
                        "tag": element.get("tag"),
                        "tabindex": tabindex_value
                    },
                    user_impact=(
                        "Custom tab order can make keyboard "
                        "navigation unpredictable and difficult "
                        "to follow."
                    ),
                    recommendation=(
                        "Prefer tabindex='0' or native interactive "
                        "elements and allow the DOM order to define "
                        "the natural keyboard sequence."
                    )
                )
            )

    return issues


# ============================================================
# HCI-007
# Very small interactive targets
# ============================================================

def check_small_interactive_targets(data):
    """
    Detect unusually small interactive elements.

    Heuristic:
        H5 - Error prevention

    NOTE:
        This is an initial heuristic threshold and should later
        be refined using platform/accessibility standards.
    """

    issues = []

    interactive = data.get(
        "layout", {}
    ).get(
        "interactive", {}
    ).get(
        "items", []
    )

    MIN_SIZE = 24

    for element in interactive:

        if not element.get("visible", True):
            continue

        width = element.get("width", 0)
        height = element.get("height", 0)

        if width < MIN_SIZE or height < MIN_SIZE:

            issues.append(
                create_issue(
                    rule_id="HCI-007",
                    heuristic_id="H5",
                    severity="medium",
                    element=element.get("tag"),
                    problem=(
                        "Interactive target is unusually small."
                    ),
                    evidence={
                        "index": element.get("index"),
                        "tag": element.get("tag"),
                        "width": width,
                        "height": height
                    },
                    user_impact=(
                        "Users may have difficulty accurately "
                        "activating the control, particularly "
                        "on touch devices."
                    ),
                    recommendation=(
                        "Increase the interactive target size and "
                        "provide sufficient spacing between controls."
                    )
                )
            )

    return issues


# ============================================================
# HCI-008
# Heading hierarchy
# ============================================================

def check_heading_hierarchy(data):
    """
    Detect potentially problematic heading hierarchy.

    Heuristic:
        H6 - Recognition rather than recall
    """

    issues = []

    headings = data.get(
        "structure", {}
    ).get(
        "headings", {}
    ).get(
        "items", []
    )

    if not headings:
        return issues

    previous_level = None

    for heading in headings:

        level_string = heading.get("level", "")

        if not level_string.startswith("h"):
            continue

        try:
            level = int(level_string[1:])
        except ValueError:
            continue

        if previous_level is not None:

            if level > previous_level + 1:

                issues.append(
                    create_issue(
                        rule_id="HCI-008",
                        heuristic_id="H6",
                        severity="medium",
                        element=level_string,
                        problem=(
                            "Heading hierarchy skips a heading level."
                        ),
                        evidence={
                            "previous_level": f"h{previous_level}",
                            "current_level": f"h{level}",
                            "text": heading.get("text")
                        },
                        user_impact=(
                            "Users may find the information structure "
                            "harder to understand and navigate."
                        ),
                        recommendation=(
                            "Use heading levels that reflect the "
                            "logical structure of the content."
                        )
                    )
                )

        previous_level = level

    return issues


# ============================================================
# HCI-009
# Missing H1
# ============================================================

def check_missing_h1(data):
    """
    Detect pages that do not contain an H1 heading.

    Heuristic:
        H6 - Recognition rather than recall
    """

    issues = []

    headings = data.get(
        "structure", {}
    ).get(
        "headings", {}
    )

    counts = headings.get(
        "counts", {}
    )

    h1_count = counts.get(
        "h1",
        0
    )

    if h1_count == 0:

        issues.append(
            create_issue(
                rule_id="HCI-009",
                heuristic_id="H6",
                severity="medium",
                element="page",
                problem="Page does not contain an H1 heading.",
                evidence={
                    "h1_count": 0
                },
                user_impact=(
                    "The primary purpose or topic of the page "
                    "may be less obvious to users and assistive "
                    "technology."
                ),
                recommendation=(
                    "Provide a clear primary heading that "
                    "describes the main purpose of the page."
                )
            )
        )

    return issues


# ============================================================
# HCI-010
# Empty buttons
# ============================================================

def check_empty_buttons(data):
    """
    Detect visible buttons without recognizable content.
    """

    issues = []

    buttons = data.get(
        "interactive", {}
    ).get(
        "buttons", {}
    ).get(
        "items", []
    )

    for button in buttons:

        if not button.get("visible", True):
            continue

        text = (button.get("text") or "").strip()
        aria_label = (
            button.get("aria_label") or ""
        ).strip()
        title = (
            button.get("title") or ""
        ).strip()

        if not text and not aria_label and not title:

            issues.append(
                create_issue(
                    rule_id="HCI-010",
                    heuristic_id="H6",
                    severity="high",
                    element="button",
                    problem="Button has no recognizable label.",
                    evidence={
                        "index": button.get("index"),
                        "text": text,
                        "aria_label": aria_label,
                        "title": title
                    },
                    user_impact=(
                        "Users may not understand what action "
                        "the button performs."
                    ),
                    recommendation=(
                        "Provide a clear visible label or "
                        "accessible name for the button."
                    )
                )
            )

    return issues


# ============================================================
# Rule registry
# ============================================================


# Rule registry

HCI_RULES = [
    check_missing_image_alt,
    check_unnamed_interactive_elements,
    check_unlabeled_form_controls,
    check_horizontal_overflow,
    check_broken_images,
    check_positive_tabindex,
    check_small_interactive_targets,
    check_heading_hierarchy,
    check_missing_h1,
    check_empty_buttons,
]


def run_all_rules(data):
    """
    Execute all deterministic HCI rules against crawler output.
    """
    issues = []
    rule_errors = []

    for rule in HCI_RULES:
        try:
            rule_issues = rule(data)

            if rule_issues:
                issues.extend(rule_issues)

        except Exception as error:
            rule_errors.append({
                "rule": rule.__name__,
                "error": str(error),
            })

    return issues
