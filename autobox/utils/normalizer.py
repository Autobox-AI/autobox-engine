import re


def value_to_id(value: str):
    return value.replace(" ", "_").lower()


def remove_ansi_codes(text: str) -> str:
    # This regex matches ANSI escape sequences anywhere in the string
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)
