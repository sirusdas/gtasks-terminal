"""
CLI Notify Command - Check, list, read, and manage notifications.
"""
import click
from datetime import datetime
from gtasks_cli.notifications.manager import NotificationManager
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def notify():
    """Notification management system for GTasks."""
    pass


@notify.command(name='list')
@click.option('--unread-only', '-u', is_flag=True, help='Show only unread notifications')
@click.option('--limit', '-n', default=20, type=int, help='Maximum number of notifications to show')
@click.pass_context
def list_notifications(ctx, unread_only, limit):
    """List recent notifications."""
    account_name = ctx.obj.get('account_name') if ctx.obj else None
    nm = NotificationManager(account_name=account_name)
    notifs = nm.list_notifications(unread_only=unread_only, limit=limit)
    unread_count = nm.get_unread_count()

    click.echo(f"\n📬 Notifications ({len(notifs)} shown, {unread_count} unread):")
    click.echo("=" * 65)

    if not notifs:
        click.echo("✨ No notifications found.")
        return

    for n in notifs:
        status_marker = "🔴" if not n['read'] else "⚪"
        sev_color = {
            'critical': 'red',
            'warning': 'yellow',
            'info': 'blue',
            'success': 'green'
        }.get(n['severity'], 'white')

        click.echo(f"{status_marker} [{n['id']}] {click.style(n['title'], fg=sev_color, bold=True)}")
        click.echo(f"   {n['message']}")
        click.echo(f"   {click.style(n['created_at'], dim=True)} | Type: {n['type']} | Severity: {n['severity']}")
        click.echo("-" * 65)


@notify.command(name='check')
@click.pass_context
def check_notifications(ctx,):
    """Scan tasks and generate new alerts for overdue and upcoming tasks."""
    account_name = ctx.obj.get('account_name') if ctx.obj else None
    storage_backend = ctx.obj.get('storage_backend', 'sqlite') if ctx.obj else 'sqlite'

    tm = TaskManager(use_google_tasks=False, storage_backend=storage_backend, account_name=account_name)
    tasks = tm.list_tasks()

    nm = NotificationManager(account_name=account_name)
    new_alerts = nm.evaluate_task_alerts(tasks)

    click.echo(f"🔍 Checked {len(tasks)} tasks.")
    if new_alerts:
        click.echo(click.style(f"⚠️  Generated {len(new_alerts)} new notification(s):", fg='yellow', bold=True))
        for a in new_alerts:
            click.echo(f" - [{a['severity'].upper()}] {a['title']}: {a['message']}")
    else:
        click.echo(click.style("✅ Everything up to date, no new alerts generated.", fg='green'))


@notify.command(name='read')
@click.argument('notif_id', required=False)
@click.option('--all', 'mark_all', is_flag=True, help='Mark all notifications as read')
@click.pass_context
def read_notification(ctx, notif_id, mark_all):
    """Mark notification(s) as read."""
    account_name = ctx.obj.get('account_name') if ctx.obj else None
    nm = NotificationManager(account_name=account_name)

    if mark_all or not notif_id:
        nm.mark_as_read(None)
        click.echo(click.style("✅ Marked all notifications as read.", fg='green'))
    else:
        if nm.mark_as_read(notif_id):
            click.echo(click.style(f"✅ Marked notification {notif_id} as read.", fg='green'))
        else:
            click.echo(click.style(f"❌ Failed to mark notification {notif_id}.", fg='red'))


@notify.command(name='clear')
@click.argument('notif_id', required=False)
@click.option('--all', 'clear_all', is_flag=True, help='Clear all notifications')
@click.confirmation_option(prompt='Are you sure you want to delete notifications?')
@click.pass_context
def clear_notifications(ctx, notif_id, clear_all):
    """Delete notification(s)."""
    account_name = ctx.obj.get('account_name') if ctx.obj else None
    nm = NotificationManager(account_name=account_name)

    if clear_all or not notif_id:
        nm.clear(None)
        click.echo(click.style("🗑️ Cleared all notifications.", fg='green'))
    else:
        if nm.clear(notif_id):
            click.echo(click.style(f"🗑️ Deleted notification {notif_id}.", fg='green'))
        else:
            click.echo(click.style(f"❌ Failed to delete notification {notif_id}.", fg='red'))
