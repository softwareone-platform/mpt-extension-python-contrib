"""Shared naming helpers."""


def normalize_token(token: str) -> str:
    """Normalize a free-form token for comparisons."""
    return token.strip().lower().replace("-", "_").replace(" ", "_")
