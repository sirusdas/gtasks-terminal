"""
Notification Storage Module - SQLite persistent storage for notifications.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


class NotificationStorage:
    """Manages persistent SQLite storage for notifications."""

    def __init__(self, db_path: Optional[Path] = None, account_name: Optional[str] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            base_dir = Path.home() / '.gtasks'
            if account_name and account_name.lower() not in ('default', 'personal'):
                self.db_path = base_dir / account_name / 'tasks.db'
            else:
                self.db_path = base_dir / 'tasks.db'

        self._init_table()

    def _init_table(self):
        """Create notifications table if it doesn't exist."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute('PRAGMA journal_mode=WAL;')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notifications (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        read BOOLEAN DEFAULT 0,
                        task_id TEXT,
                        metadata TEXT,
                        created_at DATETIME NOT NULL
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_notif_read ON notifications(read)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_notif_created ON notifications(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_notif_task ON notifications(task_id)')
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error initializing notifications table: {e}")

    def add_notification(self, notif_id: str, title: str, message: str,
                         notif_type: str = 'info', severity: str = 'info',
                         task_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                         created_at: Optional[datetime] = None) -> bool:
        """Insert a notification into database."""
        created = created_at or datetime.now()
        def _json_default(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return str(obj)

        meta_json = json.dumps(metadata, default=_json_default) if metadata else None
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO notifications
                    (id, title, message, type, severity, read, task_id, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
                ''', (notif_id, title, message, notif_type, severity, task_id, meta_json, created.isoformat()))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error adding notification: {e}")
            return False

    def list_notifications(self, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve notifications ordered by creation date descending."""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                if unread_only:
                    cursor.execute('''
                        SELECT id, title, message, type, severity, read, task_id, metadata, created_at
                        FROM notifications
                        WHERE read = 0
                        ORDER BY created_at DESC
                        LIMIT ?
                    ''', (limit,))
                else:
                    cursor.execute('''
                        SELECT id, title, message, type, severity, read, task_id, metadata, created_at
                        FROM notifications
                        ORDER BY created_at DESC
                        LIMIT ?
                    ''', (limit,))

                rows = cursor.fetchall()
                results = []
                for row in rows:
                    meta = None
                    if row[7]:
                        try:
                            meta = json.loads(row[7])
                        except Exception:
                            meta = row[7]

                    results.append({
                        'id': row[0],
                        'title': row[1],
                        'message': row[2],
                        'type': row[3],
                        'severity': row[4],
                        'read': bool(row[5]),
                        'task_id': row[6],
                        'metadata': meta,
                        'created_at': row[8]
                    })
                return results
        except sqlite3.Error as e:
            logger.error(f"Error listing notifications: {e}")
            return []

    def get_unread_count(self) -> int:
        """Count unread notifications."""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM notifications WHERE read = 0')
                row = cursor.fetchone()
                return row[0] if row else 0
        except sqlite3.Error as e:
            logger.error(f"Error counting unread notifications: {e}")
            return 0

    def mark_as_read(self, notif_id: Optional[str] = None) -> bool:
        """Mark specific notification or all notifications as read."""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                if notif_id:
                    cursor.execute('UPDATE notifications SET read = 1 WHERE id = ?', (notif_id,))
                else:
                    cursor.execute('UPDATE notifications SET read = 1 WHERE read = 0')
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error marking notification as read: {e}")
            return False

    def clear_notifications(self, notif_id: Optional[str] = None) -> bool:
        """Delete specific notification or all notifications."""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                if notif_id:
                    cursor.execute('DELETE FROM notifications WHERE id = ?', (notif_id,))
                else:
                    cursor.execute('DELETE FROM notifications')
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error clearing notifications: {e}")
            return False
