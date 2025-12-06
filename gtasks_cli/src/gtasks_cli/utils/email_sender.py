import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)

class EmailSender:
    """Helper class to send emails using Gmail SMTP."""
    
    def __init__(self, email_address: str = None, password: str = None):
        self.email_address = email_address or os.environ.get('GTASKS_EMAIL_USER')
        self.password = password or os.environ.get('GTASKS_EMAIL_PASSWORD')
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email(self, to_email: str, subject: str, body: str):
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
        """
        if not self.email_address or not self.password:
            logger.warning("Email credentials not found. Set GTASKS_EMAIL_USER and GTASKS_EMAIL_PASSWORD environment variables.")
            print("Error: Email credentials not configured. Please set GTASKS_EMAIL_USER and GTASKS_EMAIL_PASSWORD.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.password)
            text = msg.as_string()
            server.sendmail(self.email_address, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            print(f"Error sending email: {e}")
            return False
