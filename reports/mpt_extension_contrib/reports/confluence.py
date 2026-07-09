"""Attach report files to a Confluence page."""

import logging

import requests
from atlassian import Confluence
from atlassian.errors import ApiError

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Client for attaching files to a Confluence page.

    Credentials and the target instance are supplied explicitly so the client
    has no dependency on any extension settings object.
    """

    def __init__(self, base_url: str, user: str, token: str, *, cloud: bool = True) -> None:
        """Initialize the client.

        Args:
            base_url: Base URL of the Confluence instance.
            user: Username used for authentication.
            token: API token used for authentication.
            cloud: Whether the instance is Confluence Cloud.
        """
        self._client = Confluence(  # type: ignore[no-untyped-call]
            url=base_url,
            username=user,
            password=token,
            cloud=cloud,
        )

    def attach_content(
        self,
        page_id: str,
        filename: str,
        file_content: bytes,
        *,
        content_type: str,
        comment: str | None = None,
    ) -> bool:
        """Upload a file as an attachment to a Confluence page.

        The ``comment`` default mirrors the underlying
        ``atlassian.Confluence.attach_content`` call.

        Args:
            page_id: ID of the Confluence page to attach the file to.
            filename: Name of the file to upload.
            file_content: Binary content of the file.
            content_type: MIME type of the file.
            comment: Optional comment to add to the attachment.

        Returns:
            ``True`` if the upload succeeded, ``False`` otherwise.
        """
        try:
            self._client.attach_content(  # type: ignore[no-untyped-call]
                content=file_content,
                name=filename,
                content_type=content_type,
                page_id=page_id,
                comment=comment,
            )
        except (ApiError, requests.exceptions.RequestException):
            logger.exception("Failed to attach %s to Confluence page %s", filename, page_id)
            return False
        else:
            logger.info("File %s attached to Confluence page %s", filename, page_id)
            return True
