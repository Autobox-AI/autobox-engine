"""
Agent name sanitization to prevent Unicode/special character issues.
"""

import re
import unicodedata
from typing import Dict


def sanitize_agent_name(name: str) -> str:
    """
    Sanitize an agent name to ensure it works correctly throughout the system.
    Converts special characters to ASCII-safe equivalents.

    Args:
        name: The original agent name.

    Returns:
        A sanitized version of the name.
    """
    if not name:
        return name

    normalized = unicodedata.normalize("NFD", name)

    ascii_name = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )

    replacements = {
        "Ö": "O",
        "ö": "o",
        "Ä": "A",
        "ä": "a",
        "Å": "A",
        "å": "a",
        "Ø": "O",
        "ø": "o",
        "Æ": "AE",
        "æ": "ae",
        "Ü": "U",
        "ü": "u",
        "ß": "ss",
        "Ñ": "N",
        "ñ": "n",
        "Ç": "C",
        "ç": "c",
    }

    for old, new in replacements.items():
        ascii_name = ascii_name.replace(old, new)

    safe_name = re.sub(r"[^a-zA-Z0-9\s\-_\.]", "", ascii_name)

    safe_name = " ".join(safe_name.split())

    return safe_name.strip()


def create_name_mapping(names: list[str]) -> Dict[str, str]:
    """
    Create a mapping from original names to sanitized names.

    Args:
        names: List of original agent names.

    Returns:
        Dictionary mapping original names to sanitized names.
    """
    mapping = {}
    sanitized_names = set()

    for name in names:
        sanitized = sanitize_agent_name(name)

        if sanitized in sanitized_names:
            counter = 2
            base_name = sanitized
            while sanitized in sanitized_names:
                sanitized = f"{base_name}_{counter}"
                counter += 1

        mapping[name] = sanitized
        sanitized_names.add(sanitized)

    return mapping
