from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.entities import Notification, uid


class ExternalNotifier:
    """Future email / webhook / Slack / ERP adapters. In-app is implemented."""

    channel = "abstract"

    def send(self, notification: Notification) -> None:
        raise NotImplementedError("Coming soon")


class EmailNotifier(ExternalNotifier):
    channel = "email"

    def send(self, notification: Notification) -> None:
        raise NotImplementedError("Email notifications are coming soon")


class SlackNotifier(ExternalNotifier):
    channel = "slack"

    def send(self, notification: Notification) -> None:
        raise NotImplementedError("Slack notifications are coming soon")


class WebhookNotifier(ExternalNotifier):
    channel = "webhook"

    def send(self, notification: Notification) -> None:
        raise NotImplementedError("Webhook notifications are coming soon")


def notify(
    db: Session,
    *,
    organization_id: str,
    title: str,
    body: str,
    kind: str,
    shipment_id: str | None = None,
    user_id: str | None = None,
) -> Notification:
    item = Notification(
        id=uid(),
        organization_id=organization_id,
        user_id=user_id,
        title=title,
        body=body,
        kind=kind,
        shipment_id=shipment_id,
        channel="in_app",
    )
    db.add(item)
    return item
