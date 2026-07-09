"""Shared Adaptive Card primitives for the Teams sync and async channels.

This module imports ``microsoft-teams-cards`` at module level, so it is importable
only when the ``teams`` extra is installed. Both :mod:`.teams` and
:mod:`.teams_async` build on it, which keeps card construction in one place.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Protocol

from microsoft_teams.cards import (
    Action,
    AdaptiveCard,
    CardElement,
    Fact,
    FactSet,
    OpenUrlAction,
    TextBlock,
)

Color = Literal["Good", "Warning", "Attention", "Accent"]
SeverityName = Literal["warning", "success", "error", "exception"]

# Emoji + card colour per severity, kept in one place for both channels.
_SEVERITIES: Mapping[SeverityName, tuple[str, Color]] = MappingProxyType({
    "warning": ("☢", "Warning"),
    "success": ("✅", "Good"),
    "error": ("💣", "Attention"),
    "exception": ("🔥", "Attention"),
})


@dataclass(frozen=True)
class Button:
    """A link button rendered as an ``Action.OpenUrl`` on the card."""

    label: str
    url: str


@dataclass(frozen=True)
class FactsSection:
    """A titled key/value section rendered as a ``FactSet`` on the card."""

    title: str
    entries: Mapping[str, str]


class TeamsSettings(Protocol):
    """Settings the Teams channels read from."""

    teams_webhook_url: str | None
    teams_notifications_enabled: bool


def facts_blocks(section: FactsSection) -> list[CardElement]:
    """Render a facts section as a heading plus a ``FactSet``."""
    facts: list[Fact] = []
    for name, detail in section.entries.items():
        facts.append(Fact(title=name, value=detail))
    heading = TextBlock(text=section.title, weight="Bolder", wrap=True)
    return [heading, FactSet(facts=facts)]


def severity_card(
    title: str,
    text: str,
    severity: SeverityName,
    *,
    button: Button | None,
    facts: FactsSection | None,
) -> AdaptiveCard:
    """Build a severity-styled Adaptive Card (emoji + colour from ``severity``)."""
    emoji, color = _SEVERITIES[severity]
    heading = f"{emoji} {title}"
    body: list[CardElement] = [
        TextBlock(text=heading, weight="Bolder", size="Large", color=color, wrap=True),
        TextBlock(text=text, wrap=True),
    ]
    if facts is not None:
        body += facts_blocks(facts)
    actions: list[Action] = []
    if button is not None:
        actions.append(OpenUrlAction(title=button.label, url=button.url))
    return AdaptiveCard(body=body, actions=actions)


def payload(card: AdaptiveCard) -> dict[str, object]:
    """Wrap an Adaptive Card in the Teams webhook message envelope."""
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card.model_dump(by_alias=True, exclude_none=True),
            },
        ],
    }
