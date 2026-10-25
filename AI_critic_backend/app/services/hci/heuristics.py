NIELSEN_HEURISTICS = {

    "H1": {
        "id": "H1",
        "name": "Visibility of system status",
        "description": (
            "The system should always keep users informed about "
            "what is going on through appropriate and timely feedback."
        ),
        "keywords": [
            "feedback",
            "loading",
            "progress",
            "status",
            "system response",
            "confirmation"
        ]
    },

    "H2": {
        "id": "H2",
        "name": "Match between system and the real world",
        "description": (
            "The system should use language, concepts, and conventions "
            "that are familiar to the user and reflect the real world."
        ),
        "keywords": [
            "language",
            "terminology",
            "familiar concepts",
            "real-world conventions",
            "mapping",
            "labels"
        ]
    },

    "H3": {
        "id": "H3",
        "name": "User control and freedom",
        "description": (
            "Users should have clear ways to undo, redo, cancel, "
            "exit, or otherwise recover from actions."
        ),
        "keywords": [
            "undo",
            "redo",
            "cancel",
            "back",
            "exit",
            "close",
            "navigation",
            "user control"
        ]
    },

    "H4": {
        "id": "H4",
        "name": "Consistency and standards",
        "description": (
            "Users should not have to wonder whether different words, "
            "situations, or actions mean the same thing."
        ),
        "keywords": [
            "consistency",
            "standards",
            "buttons",
            "navigation",
            "labels",
            "visual patterns",
            "interaction patterns"
        ]
    },

    "H5": {
        "id": "H5",
        "name": "Error prevention",
        "description": (
            "The interface should prevent problems from occurring "
            "whenever possible, or provide confirmation before "
            "potentially harmful actions."
        ),
        "keywords": [
            "validation",
            "constraints",
            "confirmation",
            "input errors",
            "forms",
            "required fields",
            "destructive actions"
        ]
    },

    "H6": {
        "id": "H6",
        "name": "Recognition rather than recall",
        "description": (
            "The interface should make relevant information, actions, "
            "and options visible so users do not have to remember "
            "information from one part of the interface to another."
        ),
        "keywords": [
            "recognition",
            "navigation",
            "labels",
            "headings",
            "information architecture",
            "discoverability",
            "visible options"
        ]
    },

    "H7": {
        "id": "H7",
        "name": "Flexibility and efficiency of use",
        "description": (
            "The interface should accommodate both inexperienced and "
            "experienced users and provide efficient ways to perform "
            "frequent actions."
        ),
        "keywords": [
            "efficiency",
            "shortcuts",
            "keyboard",
            "power users",
            "navigation",
            "workflow",
            "customization"
        ]
    },

    "H8": {
        "id": "H8",
        "name": "Aesthetic and minimalist design",
        "description": (
            "Interfaces should avoid information that is irrelevant "
            "or rarely needed and should present only information "
            "that is useful to the user."
        ),
        "keywords": [
            "visual hierarchy",
            "clutter",
            "simplicity",
            "spacing",
            "content density",
            "layout",
            "visual noise"
        ]
    },

    "H9": {
        "id": "H9",
        "name": "Help users recognize, diagnose, and recover from errors",
        "description": (
            "Error messages should be expressed in clear language, "
            "identify the problem, and suggest a constructive solution."
        ),
        "keywords": [
            "error messages",
            "validation",
            "error recovery",
            "feedback",
            "diagnosis",
            "recovery",
            "instructions"
        ]
    },

    "H10": {
        "id": "H10",
        "name": "Help and documentation",
        "description": (
            "The system should provide relevant help and documentation "
            "when users need assistance, with information that is easy "
            "to find, understand, and act upon."
        ),
        "keywords": [
            "help",
            "documentation",
            "instructions",
            "FAQ",
            "guidance",
            "support",
            "search"
        ]
    }
}


def get_heuristic(heuristic_id: str):
    """
    Return a single Nielsen heuristic by ID.

    Example:
        get_heuristic("H5")
    """

    return NIELSEN_HEURISTICS.get(heuristic_id)


def get_all_heuristics():
    """
    Return all Nielsen heuristics.
    """

    return NIELSEN_HEURISTICS


def get_heuristic_name(heuristic_id: str):
    """
    Return only the name of a heuristic.
    """

    heuristic = get_heuristic(heuristic_id)

    if heuristic is None:
        return None

    return heuristic["name"]