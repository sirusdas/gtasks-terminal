"""
Notification Manager Module - Rule evaluation, alerts generation and notification service.
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from gtasks_cli.notifications.storage import NotificationStorage
from gtasks_cli.models.task import Task, TaskStatus
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


class NotificationManager:
    """Evaluates task states and manages notifications."""

    def __init__(self, db_path: Optional[Path] = None, account_name: Optional[str] = None):
        self.storage = NotificationStorage(db_path=db_path, account_name=account_name)

    def _make_naive(self, dt):
        if dt and hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt

    def evaluate_task_alerts(self, tasks: List[Any]) -> List[Dict[str, Any]]:
        """
        Evaluate tasks for overdue and upcoming deadline conditions.
        Creates notifications if they haven't been alerted today.
        """
        now = datetime.now()
        today = now.date()
        today_str = today.isoformat()
        new_alerts = []

        # Load recent notifications to avoid duplicate alerts within the same day
        recent_notifs = self.storage.list_notifications(limit=200)
        recent_keys = set()
        for n in recent_notifs:
            created = n.get('created_at', '')
            if created.startswith(today_str):
                task_id = n.get('task_id')
                notif_type = n.get('type')
                if task_id and notif_type:
                    recent_keys.add(f"{notif_type}:{task_id}")

        for t in tasks:
            # Handle both Task objects and dicts
            task_id = getattr(t, 'id', None) or (t.get('id') if isinstance(t, dict) else '')
            title = getattr(t, 'title', None) or (t.get('title') if isinstance(t, dict) else 'Untitled')
            status = getattr(t, 'status', None) or (t.get('status') if isinstance(t, dict) else 'pending')
            due_raw = getattr(t, 'due', None) or (t.get('due') if isinstance(t, dict) else None)

            # Skip completed or deleted tasks
            if status in ('completed', TaskStatus.COMPLETED):
                continue
            is_deleted = getattr(t, 'is_deleted', False) or (t.get('is_deleted', False) if isinstance(t, dict) else False)
            if is_deleted:
                continue

            if not due_raw:
                continue

            # Parse due date
            due_dt = None
            if isinstance(due_raw, str):
                try:
                    due_dt = datetime.fromisoformat(due_raw.replace('Z', '+00:00'))
                except Exception:
                    pass
            elif isinstance(due_raw, datetime):
                due_dt = due_raw

            if not due_dt:
                continue

            due_dt = self._make_naive(due_dt)
            due_date = due_dt.date()

            # Rule 1: Overdue Task
            if due_date < today:
                days_overdue = (today - due_date).days
                rule_key = f"overdue:{task_id}"
                if rule_key not in recent_keys:
                    severity = 'critical' if days_overdue >= 7 else ('warning' if days_overdue >= 3 else 'info')
                    notif_id = f"notif_overdue_{task_id}_{today_str}"
                    msg = f"Task is {days_overdue} day{'s' if days_overdue > 1 else ''} overdue (was due {due_date.isoformat()})."
                    
                    added = self.storage.add_notification(
                        notif_id=notif_id,
                        title=f"Overdue: {title}",
                        message=msg,
                        notif_type='overdue',
                        severity=severity,
                        task_id=task_id,
                        metadata={'days_overdue': days_overdue, 'due': due_raw}
                    )
                    if added:
                        recent_keys.add(rule_key)
                        new_alerts.append({
                            'id': notif_id,
                            'title': f"Overdue: {title}",
                            'message': msg,
                            'severity': severity,
                            'task_id': task_id
                        })

            # Rule 2: Due Today or Tomorrow (< 36 hours)
            elif due_date == today:
                rule_key = f"due_today:{task_id}"
                if rule_key not in recent_keys:
                    notif_id = f"notif_today_{task_id}_{today_str}"
                    msg = "Task is scheduled for today!"
                    added = self.storage.add_notification(
                        notif_id=notif_id,
                        title=f"Due Today: {title}",
                        message=msg,
                        notif_type='due_today',
                        severity='warning',
                        task_id=task_id,
                        metadata={'due': due_raw}
                    )
                    if added:
                        recent_keys.add(rule_key)
                        new_alerts.append({
                            'id': notif_id,
                            'title': f"Due Today: {title}",
                            'message': msg,
                            'severity': 'warning',
                            'task_id': task_id
                        })

        return new_alerts

    def create_custom_notification(self, title: str, message: str,
                                   notif_type: str = 'custom', severity: str = 'info',
                                   task_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a manual or system notification."""
        notif_id = f"notif_{uuid.uuid4().hex[:12]}"
        self.storage.add_notification(
            notif_id=notif_id,
            title=title,
            message=message,
            notif_type=notif_type,
            severity=severity,
            task_id=task_id,
            metadata=metadata
        )
        return notif_id

    def list_notifications(self, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        return self.storage.list_notifications(unread_only=unread_only, limit=limit)

    def get_unread_count(self) -> int:
        return self.storage.get_unread_count()

    def mark_as_read(self, notif_id: Optional[str] = None) -> bool:
        return self.storage.mark_as_read(notif_id=notif_id)

    def clear(self, notif_id: Optional[str] = None) -> bool:
        return self.storage.clear_notifications(notif_id=notif_id)
