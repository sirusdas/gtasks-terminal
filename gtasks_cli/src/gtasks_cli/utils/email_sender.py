import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import re
from datetime import datetime
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)

class EmailSender:
    """Helper class to send emails using Gmail SMTP."""
    
    def __init__(self, email_address: str = None, password: str = None):
        self.email_address = email_address or os.environ.get('GTASKS_EMAIL_USER')
        self.password = password or os.environ.get('GTASKS_EMAIL_PASSWORD')
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def _strip_ansi_codes(self, text: str) -> str:
        """Remove ANSI color codes from text."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def _clean_note_tags(self, note: str) -> str:
        """Remove tags from notes intelligently.
        
        - If note contains only tags like [tag1][tag2], return empty string
        - If note has tags at the end after content, remove only the trailing tags
        - Otherwise, keep the note as-is
        """
        if not note:
            return ""
        
        # Check if note contains only tags (and whitespace)
        cleaned = re.sub(r'\[.*?\]', '', note).strip()
        if len(cleaned) == 0:
            # Note contains only tags, remove entirely
            return ""
        
        # Remove trailing tags (tags at the end after newlines or content)
        # Pattern: match tags at the end of the string, possibly after newlines
        # This handles cases like "content\n\n[tag1][tag2]" or "content [tag1][tag2]"
        note_cleaned = re.sub(r'\s*(\[.*?\]\s*)+$', '', note).strip()
        
        return note_cleaned if note_cleaned else ""

    def _convert_report_to_html(self, plain_text: str) -> str:
        """Convert plain text report to beautiful HTML email."""
        # Strip ANSI codes first
        text = self._strip_ansi_codes(plain_text)
        
        # Parse the report structure
        lines = text.split('\n')
        html_body = []
        
        in_section = False
        current_section = ""
        in_task = False
        collecting_notes = False
        notes_buffer = []
        
        def close_current_task():
            nonlocal in_task, notes_buffer
            if in_task:
                if notes_buffer:
                    notes_text = '\n'.join(notes_buffer)
                    notes_cleaned = self._clean_note_tags(notes_text)
                    if notes_cleaned:
                        html_body.append(f'''
                        <div style="margin-top: 6px; color: #6b7280; font-size: 12px; display: flex; align-items: start; gap: 4px;">
                            <span style="flex-shrink: 0;">💬</span>
                            <span style="word-wrap: break-word; flex: 1; min-width: 0; white-space: pre-wrap;">{notes_cleaned}</span>
                        </div>
                        ''')
                    notes_buffer = []
                html_body.append('                        </div>')
                html_body.append('                    </div>')
                html_body.append('                </div>')
                in_task = False

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Main title (first line with ===)
            if '=' * 20 in line and not html_body:
                i += 1
                continue
            elif stripped and not html_body and '=' not in line:
                html_body.append(f'<h1 style="color: #1a1a1a; margin: 0 0 8px 0; font-size: 22px; font-weight: 700;">{stripped}</h1>')
                i += 1
                continue
            elif '=' * 20 in line:
                i += 1
                continue
            
            # Metadata (Generated at, Total Tasks)
            elif stripped.startswith('Generated at:'):
                date_str = stripped.replace('Generated at:', '').strip()
                try:
                    dt = datetime.fromisoformat(date_str)
                    formatted_date = dt.strftime('%b %d, %Y at %I:%M %p')
                    html_body.append(f'<div style="color: #666; font-size: 13px; margin-bottom: 4px;">📅 {formatted_date}</div>')
                except:
                    html_body.append(f'<div style="color: #666; font-size: 13px; margin-bottom: 4px;">📅 {stripped.replace("Generated at:", "").strip()}</div>')
                i += 1
                continue
            elif stripped.startswith('Total Tasks:'):
                count = stripped.replace('Total Tasks:', '').strip()
                html_body.append(f'<div style="color: #666; font-size: 13px; margin-bottom: 20px;">📊 <strong>{count}</strong> tasks</div>')
                i += 1
                continue
            elif '-' * 20 in line:
                i += 1
                continue
            
            # Section headers (SECTION 1, SECTION 2, etc.)
            elif stripped.startswith('SECTION'):
                close_current_task()
                if in_section:
                    html_body.append('</div>')
                in_section = True
                current_section = stripped
                section_color = '#2563eb' if '1' in stripped else '#7c3aed' if '2' in stripped else '#dc2626'
                html_body.append(f'''
                <div style="margin: 24px 0 16px 0; padding: 12px 16px; background: {section_color}; border-radius: 6px;">
                    <h2 style="color: white; margin: 0; font-size: 16px; font-weight: 600; letter-spacing: 0.5px;">{stripped}</h2>
                </div>
                <div style="margin-bottom: 20px;">
                ''')
                i += 1
                continue
            
            # List/Tag/Group headers
            elif stripped.startswith('LIST:') or stripped.startswith('TAG:') or stripped.startswith('GROUP:'):
                close_current_task()
                prefix = stripped.split(':')[0]
                name = ':'.join(stripped.split(':')[1:]).strip()
                icon = '📋' if prefix == 'LIST' else '🏷️' if prefix == 'TAG' else '📁'
                html_body.append(f'''
                <div style="margin: 16px 0 8px 0; padding: 8px 12px; background: #f3f4f6; border-left: 3px solid #6b7280; border-radius: 4px;">
                    <div style="color: #374151; font-size: 14px; font-weight: 600;">{icon} {name}</div>
                </div>
                ''')
                i += 1
                continue
            
            # Task items
            elif stripped.startswith('Task:'):
                close_current_task()
                
                # Parse task status and title
                task_line = stripped.replace('Task:', '').strip()
                is_completed = '[x]' in task_line or '[X]' in task_line
                
                # Remove status marker
                task_title = re.sub(r'\[[ xX]\]\s*', '', task_line)
                
                # Look ahead for dates on next line
                dates_str = ""
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('📅'):
                    next_line = lines[i + 1].strip()
                    if '|' in next_line:
                        dates_part, notes_part = next_line.split('|', 1)
                        dates_str = dates_part.replace('📅', '').strip()
                        # Start collecting notes from this line
                        notes_buffer = [notes_part.strip()] if notes_part.strip() else []
                        collecting_notes = True
                        i += 1  # Skip the date/notes line since we processed it
                    else:
                        dates_str = next_line.replace('📅', '').strip()
                        collecting_notes = False
                        i += 1  # Skip the dates line
                
                status_icon = '✅' if is_completed else '⏳'
                status_color = '#10b981' if is_completed else '#f59e0b'
                text_decoration = 'line-through' if is_completed else 'none'
                opacity = '0.7' if is_completed else '1'
                
                # Build task title with inline dates
                title_html = f'<span style="text-decoration: {text_decoration}; opacity: {opacity};">{task_title}</span>'
                if dates_str:
                    title_html += f' <span style="color: #9ca3af; font-size: 11px; font-weight: 400;">({dates_str})</span>'
                
                html_body.append(f'''
                <div style="margin: 8px 0; padding: 10px 12px; background: white; border-left: 3px solid {status_color}; border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="display: flex; align-items: start; gap: 8px;">
                        <span style="flex-shrink: 0; font-size: 16px;">{status_icon}</span>
                        <div style="flex: 1; min-width: 0;">
                            <div style="color: #1f2937; font-size: 14px; font-weight: 500; word-wrap: break-word;">{title_html}</div>
                ''')
                in_task = True
                i += 1
                continue
            
            # Collect multi-line notes content
            elif in_task and collecting_notes and stripped and not stripped.startswith('Task:') and not stripped.startswith('LIST:') and not stripped.startswith('TAG:') and not stripped.startswith('GROUP:') and not stripped.startswith('SECTION') and not stripped.startswith('Details:'):
                notes_buffer.append(stripped)
                i += 1
                continue
            
            # Empty line or non-task line - stop collecting notes
            elif in_task and (not stripped or stripped.startswith('Details:')):
                collecting_notes = False
                if stripped.startswith('Details:'):
                    content = stripped.replace('Details:', '').strip()
                    html_body.append(f'''
                            <div style="margin-top: 6px; color: #6b7280; font-size: 12px; display: flex; align-items: start; gap: 4px;">
                                <span style="flex-shrink: 0;">📝</span>
                                <span style="word-wrap: break-word; flex: 1; min-width: 0;">{content}</span>
                            </div>
                    ''')
                i += 1
                continue
            
            # No tags/groups found message
            elif '(No tags found' in stripped or '(No groups found' in stripped:
                html_body.append(f'<div style="color: #9ca3af; font-style: italic; font-size: 13px; margin: 12px 0; padding: 8px;">{stripped}</div>')
                i += 1
                continue
            
            i += 1
        
        # Close any open task
        close_current_task()
        
        # Close any open section
        if in_section:
            html_body.append('</div>')
        
        return '\n'.join(html_body)

    def send_email(self, to_emails: list, subject: str, body: str, html: bool = True, cc_emails: list = None, bcc_emails: list = None):
        """
        Send an email with optional HTML formatting.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Email body content (plain text or will be converted to HTML)
            html: Whether to send as HTML email (default: True)
            cc_emails: List of CC email addresses
            bcc_emails: List of BCC email addresses
        """
        if not self.email_address or not self.password:
            logger.warning("Email credentials not found. Set GTASKS_EMAIL_USER and GTASKS_EMAIL_PASSWORD environment variables.")
            print("Error: Email credentials not configured. Please set GTASKS_EMAIL_USER and GTASKS_EMAIL_PASSWORD.")
            return False

        # Ensure inputs are lists
        if isinstance(to_emails, str):
            to_emails = [e.strip() for e in to_emails.split(',')]
        if isinstance(cc_emails, str):
            cc_emails = [e.strip() for e in cc_emails.split(',')]
        
        cc_emails = cc_emails or []
        bcc_emails = bcc_emails or []

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = ", ".join(to_emails)
            if cc_emails:
                msg['Cc'] = ", ".join(cc_emails)
            msg['Subject'] = subject

            # Create plain text version (strip ANSI codes)
            plain_text = self._strip_ansi_codes(body)
            
            # Attach plain text version
            msg.attach(MIMEText(plain_text, 'plain'))
            
            # If HTML is enabled, create and attach HTML version
            if html:
                html_content = self._convert_report_to_html(body)
                
                # Wrap in full HTML template
                html_email = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        @media only screen and (max-width: 600px) {{
            .container {{ padding: 12px !important; }}
            .header {{ padding: 12px !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.5; color: #1f2937; background-color: #f9fafb;">
    <div class="container" style="width: 100%; max-width: 100%; padding: 16px; box-sizing: border-box;">
        <div style="background: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); max-width: 1200px; margin: 0 auto;">
            <div class="header" style="border-bottom: 2px solid #e5e7eb; padding-bottom: 12px; margin-bottom: 20px;">
                <div style="display: inline-block; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: white; padding: 6px 14px; border-radius: 5px; font-weight: 600; font-size: 13px;">
                    📊 GTasks Report
                </div>
            </div>
            
            {html_content}
            
            <div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e7eb; text-align: center;">
                <div style="color: #9ca3af; font-size: 11px; margin: 4px 0;">
                    Generated by GTasks CLI
                </div>
                <div style="color: #d1d5db; font-size: 10px; margin: 4px 0;">
                    This is an automated email. Please do not reply.
                </div>
            </div>
        </div>
    </div>
</body>
</html>
                '''
                msg.attach(MIMEText(html_email, 'html'))

            # Combine all recipients for sendmail
            all_recipients = to_emails + cc_emails + bcc_emails

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.password)
            text = msg.as_string()
            server.sendmail(self.email_address, all_recipients, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            print(f"Error sending email: {e}")
            return False
