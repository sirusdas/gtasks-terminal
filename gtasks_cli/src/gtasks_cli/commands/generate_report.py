#!/usr/bin/env python3
"""
Generate Report command for the Google Tasks CLI application.
"""

import click
import os
from typing import List
from datetime import datetime, timedelta

from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.reports.base_report import ReportManager
from gtasks_cli.reports.task_completion_report import TaskCompletionReport
from gtasks_cli.reports.pending_tasks_report import PendingTasksReport
from gtasks_cli.reports.task_creation_report import TaskCreationReport
from gtasks_cli.reports.overdue_tasks_report import OverdueTasksReport
from gtasks_cli.reports.task_distribution_report import TaskDistributionReport
from gtasks_cli.reports.task_completion_rate_report import TaskCompletionRateReport
from gtasks_cli.reports.future_timeline_report import FutureTimelineReport
from gtasks_cli.reports.timeline_report import TimelineReport
from gtasks_cli.reports.organized_tasks_report import OrganizedTasksReport
from gtasks_cli.reports.custom_filtered_report import CustomFilteredReport
from gtasks_cli.utils.tag_extractor import extract_tags_from_task
from gtasks_cli.utils.email_sender import EmailSender

logger = setup_logger(__name__)


@click.command()
@click.argument('report_ids', nargs=-1)
@click.option('--list', 'list_reports', is_flag=True, help='List all available reports')
@click.option('--list-tags', 'list_tags', is_flag=True, help='List all available tags')
@click.option('--email', multiple=True, help='Send report via email (can be used multiple times)')
@click.option('--cc', multiple=True, help='CC email addresses (can be used multiple times)')
@click.option('--bcc', multiple=True, help='BCC email addresses (can be used multiple times)')
@click.option('--export', type=click.Choice(['txt', 'csv', 'pdf']), default='txt', help='Export format')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--days', type=int, default=30, help='Number of days to analyze')
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='Start date (YYYY-MM-DD)')
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='End date (YYYY-MM-DD)')
@click.option('--days-ahead', type=int, default=30, help='Number of days ahead for future reports')
@click.option('--tags', help='Filter tasks by tags (comma-separated)')
@click.option('--with-all-tags', is_flag=True, help='Require all specified tags to be present (used with --tags)')
@click.option('--only-title', is_flag=True, help='Show only task titles, no descriptions or notes')
@click.option('--no-other-tasks', is_flag=True, help='Do not show Other Tasks (not matching any category)')
@click.option('--only-pending', is_flag=True, help='Show only pending tasks, exclude completed and deleted tasks')
@click.option('--filter', 'filter_str', help='Dynamic filter string (e.g., this_week:created_at)')
@click.option('--order-by', 'order_by', help='Field to order by (e.g., modified_at)')
@click.option('--output-tags', 'output_tags', help='Filter tags for output display (e.g., em:****,aa|ex:my,p,m)')
@click.option('--output-lists', 'output_lists', help='Filter lists for output display (e.g., em:List1,List2|ex:List3)')
@click.option('--output-tasks', 'output_tasks', help='Filter tasks for output display (e.g., em:Task1|ex:Task2)')
@click.pass_context
def generate_report(ctx, report_ids, list_reports, list_tags, email, cc, bcc, export, output, days, start_date, end_date, days_ahead, tags, with_all_tags, only_title, no_other_tasks, only_pending, filter_str, order_by, output_tags, output_lists, output_tasks):
    """Generate reports based on task data."""
    
    # Initialize report manager and register all reports
    report_manager = ReportManager()
    report_manager.register_report('rp1', TaskCompletionReport())
    report_manager.register_report('rp2', PendingTasksReport())
    report_manager.register_report('rp3', TaskCreationReport())
    report_manager.register_report('rp4', OverdueTasksReport())
    report_manager.register_report('rp5', TaskDistributionReport())
    report_manager.register_report('rp6', TaskCompletionRateReport())
    report_manager.register_report('rp7', FutureTimelineReport())
    report_manager.register_report('rp8', TimelineReport())
    report_manager.register_report('rp9', OrganizedTasksReport())
    report_manager.register_report('rp10', CustomFilteredReport())
    
    # Handle list option
    if list_reports:
        reports = report_manager.list_reports()
        click.echo("Available Reports:")
        click.echo("=" * 50)
        for report_id, report_info in reports.items():
            click.echo(f"{report_id}: {report_info['name']}")
            click.echo(f"    {report_info['description']}")
            click.echo()
        return
    
    # Handle list tags option
    if list_tags:
        # Get storage backend from context
        storage_backend = ctx.obj.get('storage_backend', 'json')
        account_name = ctx.obj.get('account_name')
        
        # Initialize task manager to get tasks
        task_manager = TaskManager(
            use_google_tasks=False,  # We just need to read local tasks
            storage_backend=storage_backend,
            account_name=account_name
        )
        
        # Load tasks
        try:
            tasks = task_manager.list_tasks()
            logger.info(f"Loaded {len(tasks)} tasks for tag listing")
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            click.echo("Error loading tasks for tag listing.")
            return
        
        # Extract all tags
        all_tags = set()
        for task in tasks:
            task_tags = extract_tags_from_task(task)
            all_tags.update(task_tags)
        
        # Sort and display tags
        sorted_tags = sorted(list(all_tags))
        click.echo("Available Tags:")
        click.echo("=" * 30)
        for tag in sorted_tags:
            click.echo(f"- {tag}")
        click.echo(f"\nTotal: {len(sorted_tags)} tags")
        return
    
    # If no report IDs specified, show help
    if not report_ids:
        click.echo("Please specify report IDs to generate.")
        click.echo("Use --list to see available reports.")
        return
    
    # Parse tags if provided
    tag_list = []
    is_complex_tag_filter = False
    if tags:
        # Check for complex filter indicators: pipe separator or em/ex/group prefixes
        if '|' in tags or 'em:' in tags or 'ex:' in tags or 'group:' in tags:
            is_complex_tag_filter = True
        else:
            tag_list = [tag.strip() for tag in tags.split(',')]
    
    # Get storage backend from context
    storage_backend = ctx.obj.get('storage_backend', 'json')
    account_name = ctx.obj.get('account_name')
    
    # Initialize task manager to get tasks
    task_manager = TaskManager(
        use_google_tasks=False,  # We just need to read local tasks
        storage_backend=storage_backend,
        account_name=account_name
    )
    
    # Load tasks
    try:
        # For reports, we want all tasks including completed ones
        tasks = task_manager.list_tasks()
        logger.info(f"Loaded {len(tasks)} tasks for report generation")
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        click.echo("Error loading tasks for report generation.")
        return
    
    # Filter tasks by pending status if specified
    if only_pending:
        from gtasks_cli.models.task import TaskStatus
        tasks = [task for task in tasks if task.status == TaskStatus.PENDING]
        logger.info(f"Filtered to {len(tasks)} pending tasks")
    
    # Filter tasks by tags if specified (only for simple tag filtering)
    if tag_list and not is_complex_tag_filter:
        from gtasks_cli.utils.tag_extractor import task_has_any_tag, task_has_all_tags
        filtered_tasks = []
        if with_all_tags:
            # Require all tags to be present
            for task in tasks:
                if task_has_all_tags(task, tag_list):
                    filtered_tasks.append(task)
        else:
            # Require any tag to be present
            for task in tasks:
                if task_has_any_tag(task, tag_list):
                    filtered_tasks.append(task)
        
        tasks = filtered_tasks
        logger.info(f"Filtered to {len(tasks)} tasks based on tags: {tag_list}")
    
    # Process each requested report
    for report_id in report_ids:
        if report_id not in report_manager.reports:
            click.echo(f"Unknown report ID: {report_id}")
            click.echo("Use --list to see available reports.")
            continue
        
        # Generate report data
        kwargs = {}
        if report_id in ['rp1', 'rp3', 'rp6', 'rp8']:  # Reports that use date ranges
            kwargs['period_days'] = days
            if start_date:
                kwargs['start_date'] = start_date
            if end_date:
                kwargs['end_date'] = end_date
        elif report_id == 'rp7':  # Future timeline report
            kwargs['days_ahead'] = days_ahead
        elif report_id == 'rp9':  # Organized tasks report
            kwargs['only_title'] = only_title
            kwargs['no_other_tasks'] = no_other_tasks
            kwargs['only_pending'] = only_pending
        elif report_id == 'rp10': # Custom Filtered Report
            kwargs['filter_str'] = filter_str
            kwargs['tags_filter'] = tags if is_complex_tag_filter else None
            kwargs['order_by'] = order_by
            kwargs['output_tags'] = output_tags
            kwargs['output_lists'] = output_lists
            kwargs['output_tasks'] = output_tasks
        
        # Generate the report
        try:
            report_data = report_manager.generate_report(report_id, tasks, **kwargs)
            
            # Determine if we should use color
            use_color = not output
            
            exported_report = report_manager.export_report(report_id, report_data, export, color=use_color)
            
            # Output the report
            if output:
                with open(output, 'w') as f:
                    f.write(exported_report)
                click.echo(f"Report {report_id} exported to: {output}")
            else:
                click.echo(f"{'='*60}")
                click.echo(f"REPORT: {report_id}")
                click.echo(f"{'='*60}")
                click.echo(exported_report)
            
            # Send email if requested
            if email:
                # Flatten the email addresses from multiple --email options
                all_to_emails = []
                for email_item in email:
                    all_to_emails.extend([e.strip() for e in email_item.split(',')])
                
                # Flatten the CC addresses from multiple --cc options
                all_cc_emails = []
                for cc_item in cc:
                    all_cc_emails.extend([e.strip() for e in cc_item.split(',')])
                
                # Flatten the BCC addresses from multiple --bcc options
                all_bcc_emails = []
                for bcc_item in bcc:
                    all_bcc_emails.extend([e.strip() for e in bcc_item.split(',')])
                
                click.echo(f"Sending report {report_id} to {', '.join(all_to_emails)}...")
                if all_cc_emails:
                    click.echo(f"CC: {', '.join(all_cc_emails)}")
                if all_bcc_emails:
                    click.echo(f"BCC: {', '.join(all_bcc_emails)}")
                    
                sender = EmailSender()
                subject = f"GTasks Report: {report_id}"
                if isinstance(report_data, dict) and 'title' in report_data:
                    subject = report_data['title']
                
                # Send the email with all recipients
                if sender.send_email(to_emails=all_to_emails, subject=subject, body=exported_report, cc_emails=all_cc_emails, bcc_emails=all_bcc_emails):
                    click.echo(f"Report sent successfully")
                else:
                    click.echo(f"Failed to send email")
        except Exception as e:
            logger.error(f"Error generating report '{report_id}': {e}")
            click.echo(f"Failed to generate report: {report_id}")